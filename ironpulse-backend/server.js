const path = require('path');
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
require('dotenv').config();

const db = require('./db');
const authRoutes = require('./routes/auth');
const profileRoutes = require('./routes/profile');
const feedbackRoutes = require('./routes/feedback');
const workoutsRoutes = require('./routes/workouts');

const app = express();
const PORT = process.env.PORT || 5000;
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*';

// ============================================================================
// Core Middleware
// ============================================================================
app.use(cors({
  origin: CORS_ORIGIN === '*' ? true : CORS_ORIGIN,
  credentials: true
}));

app.use(morgan('dev'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Serve frontend static assets from parent directory
app.use(express.static(path.join(__dirname, '..')));

// ============================================================================
// Health & API Info Endpoints
// ============================================================================
app.get('/api', (req, res) => {
  res.status(200).json({
    service: 'IronPulse Fitness Backend API',
    status: 'ONLINE',
    version: '1.0.0',
    documentation: {
      auth: '/api/auth',
      profile: '/api/profile',
      feedback: '/api/feedback',
      workouts: '/api/workouts'
    }
  });
});

app.get('/health', async (req, res) => {
  try {
    const dbTest = await db.query('SELECT 1 AS alive');
    res.status(200).json({
      status: 'UP',
      database: dbTest.rows[0].alive === 1 ? 'CONNECTED' : 'UNKNOWN',
      timestamp: new Date().toISOString()
    });
  } catch (err) {
    res.status(503).json({
      status: 'DEGRADED',
      database: 'DISCONNECTED',
      error: err.message,
      timestamp: new Date().toISOString()
    });
  }
});

// ============================================================================
// API Route Registrations
// ============================================================================
app.use('/api/auth', authRoutes);
app.use('/api/profile', profileRoutes);
app.use('/api/feedback', feedbackRoutes);
app.use('/api/workouts', workoutsRoutes);

// ============================================================================
// 404 Not Found Handler
// ============================================================================
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: `Cannot ${req.method} ${req.originalUrl} - Endpoint not found.`
  });
});

// ============================================================================
// Global Error Handler
// ============================================================================
app.use((err, req, res, next) => {
  console.error('[Global Error Handler]:', err);
  const status = err.status || 500;
  res.status(status).json({
    success: false,
    message: err.message || 'Internal server error occurred.',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});

// ============================================================================
// Server Initialization
// ============================================================================
const server = app.listen(PORT, () => {
  console.log(`
=====================================================
  ⚡ IRONPULSE BACKEND API SERVICE ONLINE ⚡
  Listening on Port: http://localhost:${PORT}
  Environment:       ${process.env.NODE_ENV || 'development'}
=====================================================
  Endpoints:
    - [POST] /api/auth/signup
    - [POST] /api/auth/login
    - [GET]  /api/auth/me
    - [GET]  /api/profile
    - [PUT]  /api/profile
    - [PATCH]/api/profile/progress
    - [POST] /api/profile/reset
    - [POST] /api/feedback
    - [GET]  /api/feedback
    - [POST] /api/workouts
    - [GET]  /api/workouts
=====================================================
  `);
});

// Graceful Shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    db.pool.end(() => {
      console.log('PostgreSQL pool closed');
      process.exit(0);
    });
  });
});

module.exports = app;
