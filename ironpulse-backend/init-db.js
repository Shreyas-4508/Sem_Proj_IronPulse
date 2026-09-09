const fs = require('fs');
const path = require('path');
const { pool } = require('./db');

async function initializeDatabase() {
  console.log('[Init DB] Reading schema.sql...');
  const schemaPath = path.join(__dirname, 'schema.sql');

  try {
    const schemaSql = fs.readFileSync(schemaPath, 'utf8');
    console.log('[Init DB] Executing SQL schema against PostgreSQL database...');
    await pool.query(schemaSql);
    console.log('[Init DB] ✅ Database schema initialized successfully!');
    console.log('[Init DB] Tables created/verified: users, athlete_profiles, feedback, workout_sessions');
  } catch (err) {
    console.error('[Init DB] ❌ Failed to initialize database schema:', err.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

initializeDatabase();
