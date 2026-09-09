-- ============================================================================
-- IronPulse Fitness Database Schema (PostgreSQL)
-- Tables: users, athlete_profiles, feedback, workout_sessions
-- ============================================================================

-- Enable UUID extension if needed (optional)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on user email for fast authentication lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Athlete Profiles Table
CREATE TABLE IF NOT EXISTS athlete_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gender VARCHAR(50) DEFAULT 'Male',
    focus_area TEXT[] DEFAULT ARRAY['Chest', 'Arms']::TEXT[],
    goals TEXT[] DEFAULT ARRAY['Build Muscle']::TEXT[],
    motivation TEXT[] DEFAULT ARRAY['Improve Health']::TEXT[],
    pushup_level VARCHAR(50) DEFAULT 'Beginner',
    activity_level VARCHAR(50) DEFAULT 'Moderately Active',
    weekly_training_days INTEGER DEFAULT 3 CHECK (weekly_training_days BETWEEN 1 AND 7),
    first_day VARCHAR(20) DEFAULT 'Monday',
    weight NUMERIC(5, 2) DEFAULT 68.00,
    weight_unit VARCHAR(10) DEFAULT 'KG',
    height NUMERIC(5, 2) DEFAULT 175.00,
    height_unit VARCHAR(10) DEFAULT 'CM',
    avatar_url VARCHAR(255) DEFAULT 'assets/male.png',
    custom_image TEXT,
    streak INTEGER DEFAULT 0 CHECK (streak >= 0),
    completed_workouts INTEGER DEFAULT 0 CHECK (completed_workouts >= 0),
    total_target_workouts INTEGER DEFAULT 12 CHECK (total_target_workouts >= 1),
    consistency INTEGER DEFAULT 0 CHECK (consistency BETWEEN 0 AND 100),
    feedback_given BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_athlete_profiles_user_id ON athlete_profiles(user_id);

-- 3. Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    is_suitable BOOLEAN DEFAULT TRUE,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);

-- 4. Workout Sessions Table
CREATE TABLE IF NOT EXISTS workout_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    routine_name VARCHAR(150) NOT NULL,
    duration_seconds INTEGER DEFAULT 0 CHECK (duration_seconds >= 0),
    exercises_completed INTEGER DEFAULT 0 CHECK (exercises_completed >= 0),
    total_exercises INTEGER DEFAULT 4 CHECK (total_exercises >= 0),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_created_at ON workout_sessions(created_at DESC);

-- 5. Trigger Function to Automatically Update updated_at Timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_timestamp trigger to users
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Apply update_timestamp trigger to athlete_profiles
DROP TRIGGER IF EXISTS trg_athlete_profiles_updated_at ON athlete_profiles;
CREATE TRIGGER trg_athlete_profiles_updated_at
    BEFORE UPDATE ON athlete_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
