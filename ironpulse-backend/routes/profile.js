const express = require('express');
const db = require('../db');
const authenticateJWT = require('../middleware/auth');

const router = express.Router();

// All profile routes require authentication
router.use(authenticateJWT);

// ============================================================================
// GET /api/profile - Fetch current user's athlete profile
// ============================================================================
router.get('/', async (req, res) => {
  try {
    const result = await db.query(
      `SELECT * FROM athlete_profiles WHERE user_id = $1`,
      [req.user.id]
    );

    if (result.rows.length === 0) {
      // If profile doesn't exist yet, create default
      const insertResult = await db.query(
        `INSERT INTO athlete_profiles (user_id)
         VALUES ($1)
         RETURNING *`,
        [req.user.id]
      );
      return res.status(200).json({
        success: true,
        data: { profile: insertResult.rows[0] }
      });
    }

    return res.status(200).json({
      success: true,
      data: { profile: result.rows[0] }
    });
  } catch (error) {
    console.error('Fetch Profile Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to fetch athlete profile.'
    });
  }
});

// ============================================================================
// PUT /api/profile - Upsert / Update athlete assessment and body metrics
// ============================================================================
router.put('/', async (req, res) => {
  const {
    gender,
    focusArea,
    goals,
    motivation,
    pushupLevel,
    activityLevel,
    weeklyTrainingDays,
    firstDay,
    weight,
    weightUnit,
    height,
    heightUnit,
    avatarUrl,
    customImage,
    streak,
    completedWorkouts,
    totalTargetWorkouts,
    consistency,
    feedbackGiven
  } = req.body;

  try {
    const queryText = `
      INSERT INTO athlete_profiles (
        user_id,
        gender,
        focus_area,
        goals,
        motivation,
        pushup_level,
        activity_level,
        weekly_training_days,
        first_day,
        weight,
        weight_unit,
        height,
        height_unit,
        avatar_url,
        custom_image,
        streak,
        completed_workouts,
        total_target_workouts,
        consistency,
        feedback_given
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
      ON CONFLICT (user_id) DO UPDATE SET
        gender = COALESCE(EXCLUDED.gender, athlete_profiles.gender),
        focus_area = COALESCE(EXCLUDED.focus_area, athlete_profiles.focus_area),
        goals = COALESCE(EXCLUDED.goals, athlete_profiles.goals),
        motivation = COALESCE(EXCLUDED.motivation, athlete_profiles.motivation),
        pushup_level = COALESCE(EXCLUDED.pushup_level, athlete_profiles.pushup_level),
        activity_level = COALESCE(EXCLUDED.activity_level, athlete_profiles.activity_level),
        weekly_training_days = COALESCE(EXCLUDED.weekly_training_days, athlete_profiles.weekly_training_days),
        first_day = COALESCE(EXCLUDED.first_day, athlete_profiles.first_day),
        weight = COALESCE(EXCLUDED.weight, athlete_profiles.weight),
        weight_unit = COALESCE(EXCLUDED.weight_unit, athlete_profiles.weight_unit),
        height = COALESCE(EXCLUDED.height, athlete_profiles.height),
        height_unit = COALESCE(EXCLUDED.height_unit, athlete_profiles.height_unit),
        avatar_url = COALESCE(EXCLUDED.avatar_url, athlete_profiles.avatar_url),
        custom_image = COALESCE(EXCLUDED.custom_image, athlete_profiles.custom_image),
        streak = COALESCE(EXCLUDED.streak, athlete_profiles.streak),
        completed_workouts = COALESCE(EXCLUDED.completed_workouts, athlete_profiles.completed_workouts),
        total_target_workouts = COALESCE(EXCLUDED.total_target_workouts, athlete_profiles.total_target_workouts),
        consistency = COALESCE(EXCLUDED.consistency, athlete_profiles.consistency),
        feedback_given = COALESCE(EXCLUDED.feedback_given, athlete_profiles.feedback_given)
      RETURNING *;
    `;

    const values = [
      req.user.id,
      gender || 'Male',
      Array.isArray(focusArea) ? focusArea : ['Chest', 'Arms'],
      Array.isArray(goals) ? goals : ['Build Muscle'],
      Array.isArray(motivation) ? motivation : ['Improve Health'],
      pushupLevel || 'Beginner',
      activityLevel || 'Moderately Active',
      weeklyTrainingDays ? parseInt(weeklyTrainingDays, 10) : 3,
      firstDay || 'Monday',
      weight !== undefined ? parseFloat(weight) : 68.0,
      weightUnit || 'KG',
      height !== undefined ? parseFloat(height) : 175.0,
      heightUnit || 'CM',
      avatarUrl || 'assets/male.png',
      customImage || null,
      streak !== undefined ? parseInt(streak, 10) : 0,
      completedWorkouts !== undefined ? parseInt(completedWorkouts, 10) : 0,
      totalTargetWorkouts !== undefined ? parseInt(totalTargetWorkouts, 10) : 12,
      consistency !== undefined ? parseInt(consistency, 10) : 0,
      feedbackGiven !== undefined ? Boolean(feedbackGiven) : false
    ];

    const result = await db.query(queryText, values);

    return res.status(200).json({
      success: true,
      message: 'Athlete profile updated successfully.',
      data: { profile: result.rows[0] }
    });
  } catch (error) {
    console.error('Update Profile Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to update athlete profile.'
    });
  }
});

// ============================================================================
// PATCH /api/profile/progress - Increment workout count, streak & consistency
// ============================================================================
router.patch('/progress', async (req, res) => {
  const { streak, completedWorkouts, consistency, feedbackGiven } = req.body;

  try {
    const updateFields = [];
    const values = [req.user.id];
    let paramIndex = 2;

    if (streak !== undefined) {
      updateFields.push(`streak = $${paramIndex++}`);
      values.push(parseInt(streak, 10));
    }
    if (completedWorkouts !== undefined) {
      updateFields.push(`completed_workouts = $${paramIndex++}`);
      values.push(parseInt(completedWorkouts, 10));
    }
    if (consistency !== undefined) {
      updateFields.push(`consistency = $${paramIndex++}`);
      values.push(parseInt(consistency, 10));
    }
    if (feedbackGiven !== undefined) {
      updateFields.push(`feedback_given = $${paramIndex++}`);
      values.push(Boolean(feedbackGiven));
    }

    if (updateFields.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'No progress fields provided to update.'
      });
    }

    const queryText = `
      UPDATE athlete_profiles
      SET ${updateFields.join(', ')}
      WHERE user_id = $1
      RETURNING *;
    `;

    const result = await db.query(queryText, values);

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Profile not found.'
      });
    }

    return res.status(200).json({
      success: true,
      message: 'Progress updated successfully.',
      data: { profile: result.rows[0] }
    });
  } catch (error) {
    console.error('Update Progress Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to update workout progress.'
    });
  }
});

// ============================================================================
// POST /api/profile/reset - Reset athlete profile to default values
// ============================================================================
router.post('/reset', async (req, res) => {
  try {
    const resetQuery = `
      UPDATE athlete_profiles
      SET
        gender = 'Male',
        focus_area = ARRAY['Chest', 'Arms']::TEXT[],
        goals = ARRAY['Build Muscle']::TEXT[],
        motivation = ARRAY['Improve Health']::TEXT[],
        pushup_level = 'Beginner',
        activity_level = 'Moderately Active',
        weekly_training_days = 3,
        first_day = 'Monday',
        weight = 68.00,
        weight_unit = 'KG',
        height = 175.00,
        height_unit = 'CM',
        avatar_url = 'assets/male.png',
        custom_image = NULL,
        streak = 0,
        completed_workouts = 0,
        total_target_workouts = 12,
        consistency = 0,
        feedback_given = FALSE
      WHERE user_id = $1
      RETURNING *;
    `;

    const result = await db.query(resetQuery, [req.user.id]);

    return res.status(200).json({
      success: true,
      message: 'Profile metrics reset to defaults.',
      data: { profile: result.rows[0] }
    });
  } catch (error) {
    console.error('Reset Profile Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to reset profile.'
    });
  }
});

module.exports = router;
