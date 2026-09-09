const jwt = require('jsonwebtoken');

/**
 * Middleware to authenticate requests using JWT tokens.
 * Extracts token from 'Authorization: Bearer <token>' header.
 */
const authenticateJWT = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({
      success: false,
      message: 'Access denied. No authorization header provided.'
    });
  }

  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    return res.status(401).json({
      success: false,
      message: 'Access denied. Format must be "Bearer <token>".'
    });
  }

  const token = parts[1];
  const secret = process.env.JWT_SECRET || 'ironpulse_super_secret_jwt_key_change_in_production';

  try {
    const decoded = jwt.verify(token, secret);
    req.user = {
      id: decoded.id,
      email: decoded.email
    };
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        message: 'Token has expired. Please log in again.'
      });
    }
    return res.status(403).json({
      success: false,
      message: 'Invalid or malformed token.'
    });
  }
};

module.exports = authenticateJWT;
