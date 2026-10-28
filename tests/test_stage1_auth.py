"""
Stage 1 Tests — Authentication and Profile functionality.
Tests registration, login, password hashing, duplicates, profile updates,
database persistence, and user data isolation.
"""

import pytest
from services.auth_service import (
    register_user,
    login_user,
    change_password,
    get_user_by_id,
    _hash_password,
    _verify_password,
    AuthError,
)
from services.profile_service import (
    get_profile,
    update_profile,
    complete_onboarding,
    ProfileError,
)
from models.user import User
from models.profile import UserProfile


# ─── Helper ───────────────────────────────────────────────────────────────────

def _register(db, email="test@example.com", username="testuser",
               password="SecurePass1!", confirm=None):
    return register_user(db, email, username, password, confirm or password)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_is_not_plain_text(self):
        hashed = _hash_password("MySecret123!")
        assert hashed != "MySecret123!"

    def test_verify_correct_password(self):
        hashed = _hash_password("MySecret123!")
        assert _verify_password("MySecret123!", hashed) is True

    def test_verify_wrong_password(self):
        hashed = _hash_password("MySecret123!")
        assert _verify_password("WrongPassword!", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = _hash_password("SamePassword1!")
        h2 = _hash_password("SamePassword1!")
        # bcrypt uses random salt so hashes differ
        assert h1 != h2

    def test_empty_password_raises(self):
        with pytest.raises(AuthError):
            _hash_password("")


class TestRegistration:
    """Tests for user registration."""

    def test_successful_registration(self, db):
        user = _register(db)
        db.commit()
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_password_is_not_stored_in_plain_text(self, db):
        user = _register(db)
        db.commit()
        assert user.password_hash != "SecurePass1!"
        assert len(user.password_hash) > 20  # bcrypt hash is long

    def test_profile_created_automatically(self, db):
        user = _register(db)
        db.commit()
        profile = db.query(UserProfile).filter_by(user_id=user.id).first()
        assert profile is not None
        assert profile.onboarding_complete is False

    def test_email_normalised_to_lowercase(self, db):
        user = register_user(db, "Test@EXAMPLE.COM", "lowertest", "SecurePass1!", "SecurePass1!")
        db.commit()
        assert user.email == "test@example.com"

    def test_duplicate_email_raises(self, db):
        _register(db)
        db.commit()
        with pytest.raises(AuthError, match="email"):
            register_user(db, "test@example.com", "otheruser", "SecurePass1!", "SecurePass1!")

    def test_duplicate_username_raises(self, db):
        _register(db)
        db.commit()
        with pytest.raises(AuthError, match="username"):
            register_user(db, "other@example.com", "testuser", "SecurePass1!", "SecurePass1!")

    def test_invalid_email_raises(self, db):
        with pytest.raises(AuthError, match="email"):
            register_user(db, "not-an-email", "validuser", "SecurePass1!", "SecurePass1!")

    def test_short_password_raises(self, db):
        with pytest.raises(AuthError, match="8"):
            register_user(db, "x@example.com", "xuser", "short", "short")

    def test_mismatched_passwords_raise(self, db):
        with pytest.raises(AuthError, match="match"):
            register_user(db, "x@example.com", "xuser", "SecurePass1!", "DifferentPass1!")

    def test_invalid_username_raises(self, db):
        with pytest.raises(AuthError):
            register_user(db, "x@example.com", "ab", "SecurePass1!", "SecurePass1!")

    def test_username_with_spaces_raises(self, db):
        with pytest.raises(AuthError):
            register_user(db, "x@example.com", "user name", "SecurePass1!", "SecurePass1!")


class TestLogin:
    """Tests for user login."""

    def test_login_with_email(self, db):
        _register(db)
        db.commit()
        user = login_user(db, "test@example.com", "SecurePass1!")
        assert user.username == "testuser"

    def test_login_with_username(self, db):
        _register(db)
        db.commit()
        user = login_user(db, "testuser", "SecurePass1!")
        assert user.username == "testuser"

    def test_login_wrong_password_raises(self, db):
        _register(db)
        db.commit()
        with pytest.raises(AuthError):
            login_user(db, "testuser", "WrongPass!")

    def test_login_unknown_user_raises(self, db):
        with pytest.raises(AuthError):
            login_user(db, "nobody@example.com", "SomePass1!")

    def test_login_updates_last_login(self, db):
        user = _register(db)
        db.commit()
        assert user.last_login is None
        login_user(db, "testuser", "SecurePass1!")
        db.commit()
        updated_user = db.query(User).filter_by(id=user.id).first()
        assert updated_user.last_login is not None

    def test_login_case_insensitive_email(self, db):
        _register(db)
        db.commit()
        user = login_user(db, "TEST@EXAMPLE.COM", "SecurePass1!")
        assert user.username == "testuser"

    def test_inactive_account_cannot_login(self, db):
        user = _register(db)
        user.is_active = False
        db.commit()
        with pytest.raises(AuthError, match="deactivated"):
            login_user(db, "testuser", "SecurePass1!")

    def test_empty_credentials_raise(self, db):
        with pytest.raises(AuthError):
            login_user(db, "", "")


class TestPasswordChange:
    """Tests for password change functionality."""

    def test_change_password_success(self, db):
        user = _register(db)
        db.commit()
        change_password(db, user.id, "SecurePass1!", "NewSecure99!", "NewSecure99!")
        db.commit()
        # Old password should no longer work
        assert _verify_password("NewSecure99!", db.query(User).get(user.id).password_hash)

    def test_wrong_current_password_raises(self, db):
        user = _register(db)
        db.commit()
        with pytest.raises(AuthError, match="incorrect"):
            change_password(db, user.id, "WrongOldPass!", "NewSecure99!", "NewSecure99!")

    def test_same_password_raises(self, db):
        user = _register(db)
        db.commit()
        with pytest.raises(AuthError):
            change_password(db, user.id, "SecurePass1!", "SecurePass1!", "SecurePass1!")

    def test_new_password_mismatch_raises(self, db):
        user = _register(db)
        db.commit()
        with pytest.raises(AuthError, match="match"):
            change_password(db, user.id, "SecurePass1!", "NewPass1!", "Different1!")


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestProfile:
    """Tests for profile creation and updates."""

    def test_profile_created_on_registration(self, db):
        user = _register(db)
        db.commit()
        profile = get_profile(db, user.id)
        assert profile is not None

    def test_update_profile_fields(self, db):
        user = _register(db)
        db.commit()
        profile = update_profile(
            db,
            requesting_user_id=user.id,
            target_user_id=user.id,
            display_name="Iron John",
            age=30,
            height_cm=180.0,
            weight_kg=80.0,
            fitness_goal="muscle_gain",
            experience_level="intermediate",
            preferred_workout_duration_minutes=45,
            workout_intensity="moderate",
        )
        db.commit()
        assert profile.display_name == "Iron John"
        assert profile.age == 30
        assert profile.fitness_goal == "muscle_gain"

    def test_cross_user_profile_update_blocked(self, db):
        user1 = _register(db, "a@example.com", "user_a")
        user2 = register_user(db, "b@example.com", "user_b", "SecurePass1!", "SecurePass1!")
        db.commit()
        with pytest.raises(ProfileError, match="authorized"):
            update_profile(
                db,
                requesting_user_id=user1.id,
                target_user_id=user2.id,
                display_name="Hacker",
            )

    def test_invalid_age_raises(self, db):
        user = _register(db)
        db.commit()
        with pytest.raises(ProfileError, match="Age"):
            update_profile(db, user.id, user.id, age=12)

    def test_invalid_fitness_goal_raises(self, db):
        user = _register(db)
        db.commit()
        with pytest.raises(ProfileError):
            update_profile(db, user.id, user.id, fitness_goal="become_immortal")

    def test_invalid_height_raises(self, db):
        user = _register(db)
        db.commit()
        with pytest.raises(ProfileError):
            update_profile(db, user.id, user.id, height_cm=10.0)

    def test_complete_onboarding(self, db):
        user = _register(db)
        db.commit()
        profile = complete_onboarding(
            db=db,
            user_id=user.id,
            display_name="Iron Jane",
            age=28,
            height_cm=165.0,
            weight_kg=60.0,
            fitness_goal="fat_loss",
            experience_level="beginner",
            preferred_workout_duration_minutes=30,
            workout_intensity="moderate",
            available_equipment=["Dumbbells", "Resistance bands"],
            dietary_preference="vegetarian",
            food_allergies=["Gluten"],
            food_restrictions="No pork",
            timezone="Asia/Kolkata",
        )
        db.commit()
        assert profile.onboarding_complete is True
        assert profile.display_name == "Iron Jane"
        assert "Dumbbells" in profile.available_equipment
        assert "Gluten" in profile.food_allergies

    def test_equipment_list_property(self, db):
        user = _register(db)
        db.commit()
        profile = update_profile(
            db, user.id, user.id,
            available_equipment="Dumbbells,Resistance bands,Pull-up bar"
        )
        db.commit()
        assert "Dumbbells" in profile.equipment_list
        assert len(profile.equipment_list) == 3

    def test_allergies_list_property(self, db):
        user = _register(db)
        db.commit()
        profile = update_profile(db, user.id, user.id, food_allergies="Gluten,Dairy")
        db.commit()
        assert "Gluten" in profile.allergies_list
        assert "Dairy" in profile.allergies_list


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE PERSISTENCE & ISOLATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDatabasePersistence:
    """Tests that data persists correctly after commits."""

    def test_user_readable_after_commit(self, db):
        user = _register(db)
        db.commit()
        user_id = user.id
        db.expire_all()  # Force reload from database
        reloaded = db.query(User).filter_by(id=user_id).first()
        assert reloaded is not None
        assert reloaded.username == "testuser"

    def test_profile_readable_after_commit(self, db):
        user = _register(db)
        update_profile(db, user.id, user.id, display_name="Persistent Name", age=35)
        db.commit()
        db.expire_all()
        profile = get_profile(db, user.id)
        assert profile.display_name == "Persistent Name"
        assert profile.age == 35


class TestUserIsolation:
    """Tests that users can only access their own data."""

    def test_two_users_have_separate_profiles(self, db):
        user1 = _register(db, "a@example.com", "user_a")
        user2 = register_user(db, "b@example.com", "user_b", "SecurePass1!", "SecurePass1!")
        db.commit()

        update_profile(db, user1.id, user1.id, display_name="Alice", age=25)
        update_profile(db, user2.id, user2.id, display_name="Bob", age=30)
        db.commit()

        profile1 = get_profile(db, user1.id)
        profile2 = get_profile(db, user2.id)

        assert profile1.display_name == "Alice"
        assert profile2.display_name == "Bob"
        assert profile1.user_id != profile2.user_id

    def test_login_as_correct_user(self, db):
        _register(db, "a@example.com", "user_a", "PassA1234!")
        register_user(db, "b@example.com", "user_b", "PassB1234!", "PassB1234!")
        db.commit()
        logged_in = login_user(db, "user_a", "PassA1234!")
        assert logged_in.username == "user_a"
        # Cannot login user_a with user_b's password
        with pytest.raises(AuthError):
            login_user(db, "user_a", "PassB1234!")
