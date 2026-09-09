const express = require('express');
const db = require('../db');
const authenticateJWT = require('../middleware/auth');

const router = express.Router();

// Feedback endpoints require authentication
router.use(authenticateJWT);

// ============================================================================
// POST /api/feedback - Submit star rating, suitability and comment
// ============================================================================
router.post('/', async (req, res) => {
  const { rating, isSuitable, comment } = req.body;

  const parsedRating = parseInt(rating, 10);
  if (isNaN(parsedRating) || parsedRating < 1 || parsedRating > 5) {
    return res.status(400).json({
      success: false,
      message: 'Rating must be an integer between 1 and 5.'
    });
  }

  const suitability = isSuitable !== undefined ? Boolean(isSuitable) : true;
  const userComment = comment ? String(comment).trim() : null;

  try {
    const client = await db.pool.connect();
    try {
      await client.query('BEGIN');

      const feedbackResult = await client.query(
        `INSERT INTO feedback (user_id, rating, is_suitable, comment)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [req.user.id, parsedRating, suitability, userComment]
      );

      // Update feedback_given flag in athlete profile
      await client.query(
        `UPDATE athlete_profiles
         SET feedback_given = TRUE
         WHERE user_id = $1`,
        [req.user.id]
      );

      await client.query('COMMIT');

      return res.status(201).json({
        success: true,
        message: 'Feedback submitted successfully. Thank you!',
        data: { feedback: feedbackResult.rows[0] }
      });
    } catch (txError) {
      await client.query('ROLLBACK');
      throw txError;
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Submit Feedback Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to submit feedback.'
    });
  }
});

// ============================================================================
// GET /api/feedback - Retrieve feedback history for the authenticated user
// ============================================================================
router.get('/', async (req, res) => {
  try {
    const result = await db.query(
      `SELECT id, user_id, rating, is_suitable, comment, created_at
       FROM feedback
       WHERE user_id = $1
       ORDER BY created_at DESC`,
      [req.user.id]
    );

    return res.status(200).json({
      success: true,
      data: {
        feedbackList: result.rows,
        total: result.rowCount
      }
    });
  } catch (error) {
    console.error('Get Feedback Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to retrieve feedback records.'
    });
  }
});

module.exports = router;
