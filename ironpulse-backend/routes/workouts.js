const express = require('express');
const db = require('../db');
const authenticateJWT = require('../middleware/auth');

const router = express.Router();

// Workout history endpoints require authentication
router.use(authenticateJWT);

// ============================================================================
// POST /api/workouts - Log a completed workout session
// ============================================================================
router.post('/', async (req, res) => {
  const {
    routineName,
    durationSeconds,
    exercisesCompleted,
    totalExercises,
    notes
  } = req.body;

  if (!routineName) {
    return res.status(400).json({
      success: false,
      message: 'Routine name is required.'
    });
  }

  const duration = durationSeconds !== undefined ? parseInt(durationSeconds, 10) : 0;
  const completed = exercisesCompleted !== undefined ? parseInt(exercisesCompleted, 10) : 4;
  const total = totalExercises !== undefined ? parseInt(totalExercises, 10) : 4;

  const client = await db.pool.connect();
  try {
    await client.query('BEGIN');

    // 1. Insert workout session record
    const workoutResult = await client.query(
      `INSERT INTO workout_sessions (
        user_id,
        routine_name,
        duration_seconds,
        exercises_completed,
        total_exercises,
        notes
      )
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *`,
      [req.user.id, routineName, duration, completed, total, notes || null]
    );

    // 2. Fetch current profile to calculate progress updates
    const profileRes = await client.query(
      `SELECT streak, completed_workouts, total_target_workouts FROM athlete_profiles WHERE user_id = $1`,
      [req.user.id]
    );

    let updatedProfile = null;
    if (profileRes.rows.length > 0) {
      const current = profileRes.rows[0];
      const newCompleted = Math.min(current.total_target_workouts, current.completed_workouts + 1);
      const newStreak = current.streak + 1;
      const newConsistency = Math.min(100, Math.round((newCompleted / current.total_target_workouts) * 100));

      const updateRes = await client.query(
        `UPDATE athlete_profiles
         SET
           streak = $1,
           completed_workouts = $2,
           consistency = $3
         WHERE user_id = $4
         RETURNING streak, completed_workouts, total_target_workouts, consistency`,
        [newStreak, newCompleted, newConsistency, req.user.id]
      );
      updatedProfile = updateRes.rows[0];
    }

    await client.query('COMMIT');

    return res.status(201).json({
      success: true,
      message: 'Workout session recorded successfully! Keep pushing!',
      data: {
        workout: workoutResult.rows[0],
        profileProgress: updatedProfile
      }
    });
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Log Workout Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to record workout session.'
    });
  } finally {
    client.release();
  }
});

// ============================================================================
// GET /api/workouts - Retrieve workout session history and stats
// ============================================================================
router.get('/', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit || '50', 10);
    const offset = parseInt(req.query.offset || '0', 10);

    // Fetch history
    const sessionsResult = await db.query(
      `SELECT id, routine_name, duration_seconds, exercises_completed, total_exercises, notes, created_at
       FROM workout_sessions
       WHERE user_id = $1
       ORDER BY created_at DESC
       LIMIT $2 OFFSET $3`,
      [req.user.id, limit, offset]
    );

    // Aggregate statistics
    const statsResult = await db.query(
      `SELECT
         COUNT(*)::INTEGER AS total_sessions,
         COALESCE(SUM(duration_seconds), 0)::INTEGER AS total_seconds,
         COALESCE(SUM(exercises_completed), 0)::INTEGER AS total_exercises_completed
       FROM workout_sessions
       WHERE user_id = $1`,
      [req.user.id]
    );

    const stats = statsResult.rows[0];
    const totalMinutes = Math.round(stats.total_seconds / 60);

    return res.status(200).json({
      success: true,
      data: {
        sessions: sessionsResult.rows,
        stats: {
          totalSessions: stats.total_sessions,
          totalDurationMinutes: totalMinutes,
          totalExercisesCompleted: stats.total_exercises_completed
        }
      }
    });
  } catch (error) {
    console.error('Get Workouts Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to retrieve workout history.'
    });
  }
});

module.exports = router;
