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
const NODE_ENV = process.env.NODE_ENV || 'development';

// ============================================================================
// CORS Configuration
// Supports Localhost, Production Vercel Domain & Configurable FRONTEND_URL
// ============================================================================
const allowedOrigins = [
  'https://semprojironpulse.vercel.app',
  'http://localhost:5000',
  'http://localhost:3000',
  'http://localhost:5500',
  'http://127.0.0.1:5500',
  'http://127.0.0.1:5000'
];

if (process.env.FRONTEND_URL) {
  const customOrigin = process.env.FRONTEND_URL.replace(/\/$/, '');
  if (!allowedOrigins.includes(customOrigin)) {
    allowedOrigins.push(customOrigin);
  }
}

app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (like mobile apps, curl, or server-to-server)
    if (!origin) return callback(null, true);

    if (allowedOrigins.includes(origin) || NODE_ENV !== 'production') {
      return callback(null, true);
    }

    const msg = `CORS Error: Origin '${origin}' is not authorized to access this API.`;
    return callback(new Error(msg), false);
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Request Logging
app.use(morgan(NODE_ENV === 'production' ? 'combined' : 'dev'));

// JSON Body Parser
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Serve frontend static assets if hosted together
app.use(express.static(path.join(__dirname, '..')));

// ============================================================================
// Health & API Info Endpoints
// ============================================================================
app.get('/api', (req, res) => {
  res.status(200).json({
    service: 'IronPulse Fitness Backend API',
    status: 'ONLINE',
    version: '1.0.0',
    environment: NODE_ENV,
    endpoints: {
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
      error: NODE_ENV === 'production' ? 'Database connection error' : err.message,
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
// Centralized Error Handler (Never leak secrets or full traces in prod)
// ============================================================================
app.use((err, req, res, next) => {
  console.error('[Error Handler]:', err.message);
  const status = err.status || (err.message.includes('CORS') ? 403 : 500);
  res.status(status).json({
    success: false,
    message: err.message || 'Internal server error occurred.',
    ...(NODE_ENV === 'development' && { stack: err.stack })
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
  Environment:       ${NODE_ENV}
  Allowed Origins:   ${allowedOrigins.join(', ')}
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
