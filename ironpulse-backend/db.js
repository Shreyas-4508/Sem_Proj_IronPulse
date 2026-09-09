const { Pool } = require('pg');
require('dotenv').config();

// Initialize PostgreSQL connection pool
// Supports either full connection string (DATABASE_URL) or individual credentials
const poolConfig = process.env.DATABASE_URL
  ? {
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false
    }
  : {
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432', 10),
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'postgres',
      database: process.env.DB_NAME || 'ironpulse_db',
      ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false
    };

const pool = new Pool(poolConfig);

pool.on('connect', () => {
  console.log('[Database] Connected to PostgreSQL successfully.');
});

pool.on('error', (err) => {
  console.error('[Database] Unexpected error on idle PostgreSQL client:', err);
});

/**
 * Generic query executor
 * @param {string} text - SQL statement
 * @param {Array} params - Query parameters for prepared statements
 * @returns {Promise<pg.QueryResult>}
 */
const query = (text, params) => pool.query(text, params);

module.exports = {
  pool,
  query
};
