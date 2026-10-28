"""Idempotent seed data and read-only catalog queries."""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.exercise import Exercise
from models.gamification import Achievement
from models.nutrition import Food


class CatalogError(ValueError):
    """Raised for invalid exercise or food search filters."""


EXERCISES = (
    {
        "name": "Bodyweight Squat",
        "description": "A foundational lower-body movement.",
        "instructions": "Stand with feet shoulder-width apart. Sit your hips back, keep your chest lifted, then stand.",
        "primary_muscle_group": "legs",
        "secondary_muscle_groups": "glutes,core",
        "category": "legs",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "none",
        "default_sets": 3,
        "default_reps": 12,
        "default_rest_seconds": 60,
        "met_value": 5.0,
    },
    {
        "name": "Reverse Lunge",
        "description": "A single-leg strength exercise.",
        "instructions": "Step one foot back, lower both knees with control, and return to standing. Alternate sides.",
        "primary_muscle_group": "legs",
        "secondary_muscle_groups": "glutes,core",
        "category": "legs",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "none",
        "default_sets": 3,
        "default_reps": 10,
        "default_rest_seconds": 60,
        "met_value": 5.0,
    },
    {
        "name": "Glute Bridge",
        "description": "A bodyweight glute and posterior-chain exercise.",
        "instructions": "Lie on your back with knees bent. Press through your heels and lift your hips without arching your back.",
        "primary_muscle_group": "glutes",
        "secondary_muscle_groups": "legs,core",
        "category": "glutes",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "none",
        "default_sets": 3,
        "default_reps": 12,
        "default_rest_seconds": 45,
        "met_value": 3.5,
    },
    {
        "name": "Incline Push-up",
        "description": "An adjustable upper-body pushing exercise.",
        "instructions": "Place hands on a stable elevated surface. Keep your body in a straight line as you lower and press away.",
        "primary_muscle_group": "chest",
        "secondary_muscle_groups": "shoulders,arms,core",
        "category": "chest",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "none",
        "default_sets": 3,
        "default_reps": 10,
        "default_rest_seconds": 60,
        "met_value": 4.0,
        "safety_notes": "Use a stable surface and stop if you feel pain.",
    },
    {
        "name": "Knee Push-up",
        "description": "A modified push-up variation.",
        "instructions": "Keep a straight line from knees to shoulders. Lower your chest with control and press back up.",
        "primary_muscle_group": "chest",
        "secondary_muscle_groups": "shoulders,arms,core",
        "category": "chest",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "none",
        "default_sets": 3,
        "default_reps": 8,
        "default_rest_seconds": 60,
        "met_value": 4.0,
    },
    {
        "name": "Dumbbell Row",
        "description": "A supported pulling movement for the back.",
        "instructions": "Support one hand on a bench or chair. Pull the dumbbell toward your hip while keeping your back neutral.",
        "primary_muscle_group": "back",
        "secondary_muscle_groups": "arms,shoulders",
        "category": "back",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "dumbbells",
        "default_sets": 3,
        "default_reps": 10,
        "default_rest_seconds": 60,
        "met_value": 4.0,
    },
    {
        "name": "Resistance Band Row",
        "description": "A band-based upper-body pulling movement.",
        "instructions": "Anchor the band securely. Pull your elbows back, pause, and return slowly.",
        "primary_muscle_group": "back",
        "secondary_muscle_groups": "arms,shoulders",
        "category": "back",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "resistance_bands",
        "default_sets": 3,
        "default_reps": 12,
        "default_rest_seconds": 60,
        "met_value": 3.5,
    },
    {
        "name": "Dumbbell Shoulder Press",
        "description": "A seated or standing overhead press.",
        "instructions": "Press both dumbbells overhead without arching your lower back, then lower with control.",
        "primary_muscle_group": "shoulders",
        "secondary_muscle_groups": "arms,core",
        "category": "shoulders",
        "difficulty": "intermediate",
        "exercise_type": "reps",
        "required_equipment": "dumbbells",
        "default_sets": 3,
        "default_reps": 10,
        "default_rest_seconds": 75,
        "met_value": 4.0,
    },
    {
        "name": "Dead Bug",
        "description": "A controlled core stability exercise.",
        "instructions": "Keep your lower back gently supported as you extend opposite arm and leg, then switch sides.",
        "primary_muscle_group": "core",
        "secondary_muscle_groups": "shoulders,hips",
        "category": "core",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "none",
        "default_sets": 3,
        "default_reps": 8,
        "default_rest_seconds": 45,
        "met_value": 3.0,
    },
    {
        "name": "Plank",
        "description": "An isometric core stability hold.",
        "instructions": "Keep your body in a straight line, brace gently, and breathe steadily.",
        "primary_muscle_group": "core",
        "secondary_muscle_groups": "shoulders,legs",
        "category": "core",
        "difficulty": "beginner",
        "exercise_type": "timed",
        "required_equipment": "none",
        "default_sets": 3,
        "default_duration_seconds": 30,
        "default_rest_seconds": 45,
        "met_value": 3.0,
    },
    {
        "name": "March in Place",
        "description": "A low-impact cardio warm-up.",
        "instructions": "March comfortably in place, moving your arms naturally.",
        "primary_muscle_group": "full_body",
        "secondary_muscle_groups": "legs,core",
        "category": "warmup",
        "difficulty": "beginner",
        "exercise_type": "timed",
        "required_equipment": "none",
        "default_sets": 1,
        "default_duration_seconds": 120,
        "default_rest_seconds": 30,
        "met_value": 3.0,
    },
    {
        "name": "Jumping Jack",
        "description": "A full-body cardio exercise.",
        "instructions": "Move at a comfortable pace, stepping instead of jumping if preferred.",
        "primary_muscle_group": "full_body",
        "secondary_muscle_groups": "legs,shoulders",
        "category": "full_body",
        "difficulty": "intermediate",
        "exercise_type": "timed",
        "required_equipment": "none",
        "default_sets": 3,
        "default_duration_seconds": 30,
        "default_rest_seconds": 45,
        "met_value": 7.0,
        "safety_notes": "Use the low-impact step variation if jumping is uncomfortable.",
    },
    {
        "name": "Dumbbell Romanian Deadlift",
        "description": "A hip-hinge movement for the posterior chain.",
        "instructions": "With a soft bend in your knees, push your hips back and lower the weights along your legs.",
        "primary_muscle_group": "legs",
        "secondary_muscle_groups": "glutes,back",
        "category": "legs",
        "difficulty": "intermediate",
        "exercise_type": "reps",
        "required_equipment": "dumbbells",
        "default_sets": 3,
        "default_reps": 10,
        "default_rest_seconds": 75,
        "met_value": 5.0,
        "safety_notes": "Use a comfortable range of motion and keep your back neutral.",
    },
    {
        "name": "Biceps Curl",
        "description": "An isolation exercise for the upper arms.",
        "instructions": "Keep your elbows near your sides and curl the weights without swinging.",
        "primary_muscle_group": "arms",
        "secondary_muscle_groups": "forearms",
        "category": "arms",
        "difficulty": "beginner",
        "exercise_type": "reps",
        "required_equipment": "dumbbells",
        "default_sets": 3,
        "default_reps": 12,
        "default_rest_seconds": 45,
        "met_value": 3.0,
    },
    {
        "name": "Child's Pose Breathing",
        "description": "A gentle cooldown breathing position.",
        "instructions": "Sit hips toward heels as comfortable and breathe slowly. Do not force the stretch.",
        "primary_muscle_group": "full_body",
        "secondary_muscle_groups": "back,hips",
        "category": "cooldown",
        "difficulty": "beginner",
        "exercise_type": "timed",
        "required_equipment": "none",
        "default_sets": 1,
        "default_duration_seconds": 60,
        "default_rest_seconds": 0,
        "met_value": 1.5,
    },
)

FOODS = (
    ("Chicken breast, cooked", "g", 165, 31.0, 0.0, 3.6, "proteins", False, False, False, False, False),
    ("Lentils, cooked", "g", 116, 9.0, 20.0, 0.4, "proteins", True, True, True, False, False),
    ("Firm tofu", "g", 144, 17.0, 3.0, 9.0, "proteins", True, True, True, False, False),
    ("Brown rice, cooked", "g", 123, 2.7, 25.6, 1.0, "carbs", True, True, True, False, False),
    ("Rolled oats, dry", "g", 389, 16.9, 66.3, 6.9, "carbs", True, True, False, False, False),
    ("Banana", "g", 89, 1.1, 22.8, 0.3, "fruits", True, True, True, False, False),
    ("Broccoli, cooked", "g", 35, 2.4, 7.2, 0.4, "vegetables", True, True, True, False, False),
    ("Plain Greek yogurt", "g", 59, 10.0, 3.6, 0.4, "dairy", True, False, True, True, False),
    ("Almonds", "g", 579, 21.2, 21.6, 49.9, "fats", True, True, True, False, True),
    ("Egg, whole", "g", 143, 12.6, 0.7, 9.5, "proteins", True, False, True, False, False),
)

ACHIEVEMENTS = (
    ("first_workout", "First Steps", "Complete your first workout.", "🏁", 25, "fitness"),
    ("workouts_5", "Getting Consistent", "Complete five workouts.", "💪", 50, "fitness"),
    ("workouts_25", "Training Regular", "Complete twenty-five workouts.", "🏋️", 100, "fitness"),
    ("streak_3", "Three-Day Rhythm", "Reach a three-day activity streak.", "🔥", 40, "streak"),
    ("streak_7", "Week of Momentum", "Reach a seven-day activity streak.", "🌟", 100, "streak"),
    ("first_food_log", "Mindful Log", "Record your first food entry.", "🥗", 15, "nutrition"),
    ("food_logs_25", "Nutrition Tracker", "Record twenty-five food entries.", "🍎", 50, "nutrition"),
    ("level_5", "Level Five", "Reach level five.", "⭐", 75, "milestone"),
)


def seed_catalog(db: Session) -> None:
    """Insert missing shared catalog entries; never overwrite existing records."""
    exercise_names = set(db.query(Exercise.name).all())
    exercise_names = {name for (name,) in exercise_names}
    for data in EXERCISES:
        if data["name"] not in exercise_names:
            db.add(Exercise(**data))

    food_names = {name for (name,) in db.query(Food.name).all()}
    for row in FOODS:
        name, unit, calories, protein, carbs, fat, category, vegetarian, vegan, gluten_free, dairy, nuts = row
        if name not in food_names:
            db.add(
                Food(
                    name=name,
                    serving_size=100.0,
                    serving_unit=unit,
                    calories=calories,
                    protein_g=protein,
                    carbs_g=carbs,
                    fat_g=fat,
                    category=category,
                    is_vegetarian=vegetarian,
                    is_vegan=vegan,
                    is_gluten_free=gluten_free,
                    contains_dairy=dairy,
                    contains_nuts=nuts,
                    data_source="IronPulse starter catalog",
                )
            )

    achievement_keys = {key for (key,) in db.query(Achievement.key).all()}
    for key, name, description, icon, xp_reward, category in ACHIEVEMENTS:
        if key not in achievement_keys:
            db.add(
                Achievement(
                    key=key,
                    name=name,
                    description=description,
                    icon=icon,
                    xp_reward=xp_reward,
                    category=category,
                )
            )
    db.flush()


def search_exercises(
    db: Session, query: str = "", category: str | None = None
) -> list[Exercise]:
    """Return active exercises matching an optional search and category."""
    if not isinstance(query, str) or len(query) > 100:
        raise CatalogError("Exercise search must be a string of at most 100 characters.")
    if category is not None and category not in {
        "warmup", "chest", "back", "shoulders", "arms", "core", "legs",
        "glutes", "full_body", "cooldown",
    }:
        raise CatalogError("Invalid exercise category.")
    statement = db.query(Exercise).filter(Exercise.is_active.is_(True))
    if query.strip():
        term = f"%{query.strip()}%"
        statement = statement.filter(
            or_(Exercise.name.ilike(term), Exercise.description.ilike(term))
        )
    if category:
        statement = statement.filter(Exercise.category == category)
    return statement.order_by(Exercise.category, Exercise.name).all()


def search_foods(db: Session, query: str = "") -> list[Food]:
    """Return foods matching an optional case-insensitive name search."""
    if not isinstance(query, str) or len(query) > 100:
        raise CatalogError("Food search must be a string of at most 100 characters.")
    statement = db.query(Food)
    if query.strip():
        statement = statement.filter(Food.name.ilike(f"%{query.strip()}%"))
    return statement.order_by(Food.name).all()
