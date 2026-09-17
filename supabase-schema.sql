-- ============================================================================
-- IronPulse – Supabase Schema
-- Run this entire script in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================================

-- 1. athlete_profiles table
--    Primary key is the Supabase auth user UUID (same as auth.users.id)
CREATE TABLE IF NOT EXISTS public.athlete_profiles (
  id                    UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name             TEXT,
  gender                TEXT DEFAULT 'Male',
  focus_area            TEXT[] DEFAULT ARRAY['Chest', 'Arms'],
  goals                 TEXT[] DEFAULT ARRAY['Build Muscle'],
  motivation            TEXT[] DEFAULT ARRAY['Improve Health'],
  pushup_level          TEXT DEFAULT 'Beginner',
  activity_level        TEXT DEFAULT 'Moderately Active',
  weekly_training_days  INTEGER DEFAULT 3 CHECK (weekly_training_days BETWEEN 1 AND 7),
  first_day             TEXT DEFAULT 'Monday',
  weight                NUMERIC(5,2) DEFAULT 68.00,
  weight_unit           TEXT DEFAULT 'KG',
  height                NUMERIC(5,2) DEFAULT 175.00,
  height_unit           TEXT DEFAULT 'CM',
  avatar_url            TEXT DEFAULT 'assets/male.png',
  custom_image          TEXT,
  streak                INTEGER DEFAULT 0 CHECK (streak >= 0),
  completed_workouts    INTEGER DEFAULT 0 CHECK (completed_workouts >= 0),
  total_target_workouts INTEGER DEFAULT 12 CHECK (total_target_workouts >= 1),
  consistency           INTEGER DEFAULT 0 CHECK (consistency BETWEEN 0 AND 100),
  feedback_given        BOOLEAN DEFAULT FALSE,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Enable Row Level Security
ALTER TABLE public.athlete_profiles ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies - each user can only access their own row
CREATE POLICY "Users can view own profile"
  ON public.athlete_profiles
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON public.athlete_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.athlete_profiles
  FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can delete own profile"
  ON public.athlete_profiles
  FOR DELETE
  USING (auth.uid() = id);

-- 4. Trigger: auto-create a default profile row when a new user registers
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.athlete_profiles (id, full_name)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data ->> 'full_name'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE PROCEDURE public.handle_new_user();

-- 5. updated_at auto-refresh trigger
CREATE OR REPLACE FUNCTION public.update_athlete_profile_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_athlete_profiles_updated_at ON public.athlete_profiles;
CREATE TRIGGER trg_athlete_profiles_updated_at
  BEFORE UPDATE ON public.athlete_profiles
  FOR EACH ROW
  EXECUTE PROCEDURE public.update_athlete_profile_timestamp();
