"""XP, levels, HP, achievements, and timezone-aware activity streaks."""

from datetime import date, datetime, time, timedelta, timezone
from math import floor
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.gamification import (
    Achievement,
    StreakActivity,
    UserAchievement,
    UserGameStats,
    XPTransaction,
)
from models.profile import UserProfile
from models.user import User


XP_PER_LEVEL = 250
HP_REGEN_INTERVAL = timedelta(hours=1)
HP_REGEN_AMOUNT = 5
WORKOUT_HP_COST = 10
VALID_XP_SOURCES = {"workout_completion", "achievement", "streak_milestone", "bonus"}


class GamificationError(ValueError):
    """Raised for invalid user, XP, HP, or timezone operations."""


def _require_user(db: Session, user_id: int) -> User:
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise GamificationError("A valid user ID is required.")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise GamificationError("User not found or inactive.")
    return user


def get_game_stats(db: Session, user_id: int) -> UserGameStats:
    """Get or create the user's single gamification record."""
    _require_user(db, user_id)
    stats = db.query(UserGameStats).filter_by(user_id=user_id).first()
    if stats is None:
        stats = UserGameStats(user_id=user_id, last_hp_regen=datetime.now(timezone.utc))
        try:
            with db.begin_nested():
                db.add(stats)
                db.flush()
        except IntegrityError:
            stats = db.query(UserGameStats).filter_by(user_id=user_id).first()
            if stats is None:
                raise
    regenerate_hp(stats)
    return stats


def level_for_xp(total_xp: int) -> int:
    """Levels advance for each 250 lifetime XP."""
    if not isinstance(total_xp, int) or isinstance(total_xp, bool) or total_xp < 0:
        raise GamificationError("Total XP must be a non-negative integer.")
    return total_xp // XP_PER_LEVEL + 1


def xp_to_next_level(total_xp: int) -> int:
    return XP_PER_LEVEL - total_xp % XP_PER_LEVEL


def regenerate_hp(
    stats: UserGameStats, now: datetime | None = None
) -> UserGameStats:
    """Regenerate five game-energy points per full hour, capped at max HP."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise GamificationError("HP regeneration time must include a timezone.")
    last_regen = stats.last_hp_regen
    if last_regen is None:
        stats.last_hp_regen = now
        return stats
    if last_regen.tzinfo is None or last_regen.utcoffset() is None:
        last_regen = last_regen.replace(tzinfo=timezone.utc)
    if now < last_regen:
        return stats
    elapsed_intervals = floor((now - last_regen) / HP_REGEN_INTERVAL)
    if elapsed_intervals:
        stats.current_hp = min(
            stats.max_hp, stats.current_hp + elapsed_intervals * HP_REGEN_AMOUNT
        )
        stats.last_hp_regen = last_regen + elapsed_intervals * HP_REGEN_INTERVAL
    return stats


def _apply_hp_cost(stats: UserGameStats, amount: int, now: datetime) -> None:
    regenerate_hp(stats, now)
    stats.current_hp = max(0, stats.current_hp - amount)
    if stats.current_hp == 0:
        stats.last_hp_regen = now


def apply_workout_hp_cost(db: Session, user_id: int, now: datetime) -> int:
    """Spend a bounded amount of fictional game energy after a logged workout."""
    stats = get_game_stats(db, user_id)
    _apply_hp_cost(stats, WORKOUT_HP_COST, now)
    return stats.current_hp


def award_xp(
    db: Session,
    user_id: int,
    xp_amount: int,
    source_type: str,
    source_id: str,
    description: str = "",
) -> XPTransaction | None:
    """Award XP once per source. Duplicate event IDs return None without changing totals."""
    _require_user(db, user_id)
    if not isinstance(xp_amount, int) or isinstance(xp_amount, bool) or xp_amount <= 0:
        raise GamificationError("XP amount must be a positive integer.")
    if not isinstance(source_type, str) or source_type not in VALID_XP_SOURCES:
        raise GamificationError("Invalid XP source type.")
    if not isinstance(source_id, str) or not source_id.strip() or len(source_id) > 100:
        raise GamificationError("A non-empty source ID of at most 100 characters is required.")
    if not isinstance(description, str) or len(description) > 200:
        raise GamificationError("XP description must be at most 200 characters.")

    transaction = XPTransaction(
        user_id=user_id,
        xp_amount=xp_amount,
        source_type=source_type,
        source_id=source_id.strip(),
        description=description.strip() or None,
    )
    try:
        with db.begin_nested():
            db.add(transaction)
            db.flush()
            stats = db.query(UserGameStats).filter_by(user_id=user_id).with_for_update().first()
            if stats is None:
                stats = UserGameStats(user_id=user_id)
                db.add(stats)
                db.flush()
            stats.total_xp += xp_amount
            stats.current_level = level_for_xp(stats.total_xp)
            db.flush()
        return transaction
    except IntegrityError:
        existing = (
            db.query(XPTransaction)
            .filter_by(user_id=user_id, source_type=source_type, source_id=source_id.strip())
            .first()
        )
        if existing is not None:
            return None
        raise


def get_local_date(db: Session, user_id: int, when: datetime | None = None) -> date:
    """Convert an aware instant to the user's configured calendar date."""
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    timezone_name = profile.timezone if profile else "UTC"
    try:
        tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError) as exc:
        raise GamificationError("The profile timezone is not a valid IANA timezone.") from exc
    when = when or datetime.now(timezone.utc)
    if when.tzinfo is None or when.utcoffset() is None:
        raise GamificationError("Activity timestamps must include a timezone.")
    return when.astimezone(tz).date()


def record_workout_activity(
    db: Session,
    user_id: int,
    workout_session_id: int,
    occurred_at: datetime,
) -> tuple[int, bool]:
    """Record one local calendar-day activity and recalculate the user's streak."""
    _require_user(db, user_id)
    if (
        not isinstance(workout_session_id, int)
        or isinstance(workout_session_id, bool)
        or workout_session_id <= 0
    ):
        raise GamificationError("A valid workout session ID is required.")
    from models.workout import WorkoutSession

    owned_session = (
        db.query(WorkoutSession)
        .filter_by(id=workout_session_id, user_id=user_id, status="completed")
        .first()
    )
    if owned_session is None:
        raise GamificationError("A completed workout owned by this user is required.")
    if not isinstance(occurred_at, datetime):
        raise GamificationError("Workout activity time must be a datetime.")
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise GamificationError("Workout activity time must include a timezone.")
    completed_at = owned_session.completed_at
    if completed_at is None:
        raise GamificationError("Completed workout is missing its completion time.")
    if completed_at.tzinfo is None or completed_at.utcoffset() is None:
        completed_at = completed_at.replace(tzinfo=timezone.utc)
    if completed_at.astimezone(timezone.utc) != occurred_at.astimezone(timezone.utc):
        raise GamificationError("Activity time must match the workout completion time.")
    local_date = get_local_date(db, user_id, occurred_at)
    if local_date > get_local_date(db, user_id):
        raise GamificationError("Workout activity cannot be dated in the future.")

    activity = StreakActivity(
        user_id=user_id,
        activity_date=local_date,
        workout_session_id=workout_session_id,
    )
    inserted = True
    try:
        with db.begin_nested():
            db.add(activity)
            db.flush()
    except IntegrityError:
        inserted = False

    dates = [
        row[0]
        for row in db.query(StreakActivity.activity_date)
        .filter_by(user_id=user_id)
        .order_by(StreakActivity.activity_date)
        .all()
    ]
    stats = get_game_stats(db, user_id)
    stats.current_streak, stats.best_streak = _calculate_streaks(
        dates, get_local_date(db, user_id)
    )
    stats.last_active_date = dates[-1] if dates else None
    if inserted:
        if stats.current_streak in {3, 7, 14, 30}:
            award_xp(
                db,
                user_id,
                {3: 20, 7: 50, 14: 100, 30: 200}[stats.current_streak],
                "streak_milestone",
                str(stats.current_streak),
                f"{stats.current_streak}-day activity streak",
            )
        unlock_eligible_achievements(db, user_id)
    return stats.current_streak, inserted


def _calculate_streaks(dates: list[date], today: date) -> tuple[int, int]:
    if not dates:
        return 0, 0
    unique_dates = sorted(set(dates))
    best = current_run = run = 0
    previous = None
    for day in unique_dates:
        run = run + 1 if previous and day == previous + timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    latest = unique_dates[-1]
    if latest in {today, today - timedelta(days=1)}:
        current_run = 1
        for day in reversed(unique_dates[:-1]):
            if day == latest - timedelta(days=current_run):
                current_run += 1
            else:
                break
    return current_run, best


def unlock_achievement(db: Session, user_id: int, key: str) -> bool:
    """Unlock one seeded achievement and award its XP exactly once."""
    _require_user(db, user_id)
    achievement = db.query(Achievement).filter_by(key=key).first()
    if achievement is None:
        raise GamificationError("Achievement not found.")
    if not _achievement_is_eligible(db, user_id, key):
        raise GamificationError("This achievement's requirements have not been met.")
    record = UserAchievement(user_id=user_id, achievement_id=achievement.id)
    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError:
        return False
    if achievement.xp_reward:
        award_xp(
            db,
            user_id,
            achievement.xp_reward,
            "achievement",
            achievement.key,
            achievement.name,
        )
    return True


def unlock_eligible_achievements(db: Session, user_id: int) -> list[str]:
    """Unlock achievements whose workout, nutrition, streak, or level thresholds are met."""
    _require_user(db, user_id)
    from models.nutrition import FoodLog
    from models.workout import WorkoutSession

    completed_workouts = (
        db.query(WorkoutSession).filter_by(user_id=user_id, status="completed").count()
    )
    food_logs = db.query(FoodLog).filter_by(user_id=user_id).count()
    stats = db.query(UserGameStats).filter_by(user_id=user_id).first()
    streak = stats.current_streak if stats else 0
    level = stats.current_level if stats else 1

    conditions = {
        "first_workout": completed_workouts >= 1,
        "workouts_5": completed_workouts >= 5,
        "workouts_25": completed_workouts >= 25,
        "streak_3": streak >= 3,
        "streak_7": streak >= 7,
        "first_food_log": food_logs >= 1,
        "food_logs_25": food_logs >= 25,
        "level_5": level >= 5,
    }
    unlocked = []
    for key, eligible in conditions.items():
        if eligible and unlock_achievement(db, user_id, key):
            unlocked.append(key)
    return unlocked


def _achievement_is_eligible(db: Session, user_id: int, key: str) -> bool:
    from models.nutrition import FoodLog
    from models.workout import WorkoutSession

    workouts = (
        db.query(WorkoutSession).filter_by(user_id=user_id, status="completed").count()
    )
    food_logs = db.query(FoodLog).filter_by(user_id=user_id).count()
    stats = db.query(UserGameStats).filter_by(user_id=user_id).first()
    streak = stats.current_streak if stats else 0
    level = stats.current_level if stats else 1
    requirements = {
        "first_workout": workouts >= 1,
        "workouts_5": workouts >= 5,
        "workouts_25": workouts >= 25,
        "streak_3": streak >= 3,
        "streak_7": streak >= 7,
        "first_food_log": food_logs >= 1,
        "food_logs_25": food_logs >= 25,
        "level_5": level >= 5,
    }
    return requirements.get(key, False)


def list_user_achievements(db: Session, user_id: int) -> list[tuple[Achievement, UserAchievement]]:
    """Return achievements earned by this user, ordered by unlock time."""
    _require_user(db, user_id)
    return (
        db.query(Achievement, UserAchievement)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .filter(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.unlocked_at.desc())
        .all()
    )


def today_window(db: Session, user_id: int, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return the aware UTC boundaries for today in the user's timezone."""
    today = get_local_date(db, user_id, now)
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    try:
        tz = ZoneInfo(profile.timezone if profile else "UTC")
    except (ZoneInfoNotFoundError, TypeError) as exc:
        raise GamificationError("The profile timezone is not a valid IANA timezone.") from exc
    start = datetime.combine(today, time.min, tzinfo=tz)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
