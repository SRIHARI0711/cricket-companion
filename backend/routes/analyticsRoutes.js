const express = require('express');
const axios = require('axios');
const router = express.Router();

const FASTAPI_BASE_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

// Axios instance with a 5-second timeout for proxy calls
const fastapiClient = axios.create({
  baseURL: FASTAPI_BASE_URL,
  timeout: 5000,
});

/**
 * Helper function to handle errors when proxying requests to FastAPI.
 * Gracefully returns JSON error response when FastAPI is down or fails.
 */
function handleProxyError(error, res, endpointName) {
  console.error(`[Analytics Proxy Error] ${endpointName}:`, error.message);

  // Case 1: FastAPI service responded with an HTTP status code (4xx, 5xx)
  if (error.response) {
    return res.status(error.response.status).json(error.response.data);
  }

  // Case 2: FastAPI service is unreachable / down / connection refused / timeout
  const isConnectionError =
    error.code === 'ECONNREFUSED' ||
    error.code === 'ETIMEDOUT' ||
    error.code === 'ENOTFOUND' ||
    error.code === 'ECONNABORTED';

  const statusCode = isConnectionError ? 503 : 500;

  return res.status(statusCode).json({
    error: isConnectionError ? 'Analytics Service Unavailable' : 'Analytics Proxy Error',
    message: isConnectionError
      ? 'The Python FastAPI analytics service is currently unreachable.'
      : 'An unexpected error occurred while proxying request to analytics service.',
    details: error.message,
    code: error.code || 'SERVICE_UNREACHABLE'
  });
}

/**
 * @route   GET /api/analytics/health
 * @desc    Check if the Python FastAPI analytics service is reachable
 */
router.get('/health', async (req, res) => {
  try {
    const response = await fastapiClient.get('/health', { timeout: 3000 });
    res.status(200).json({
      status: 'ok',
      message: 'Python FastAPI analytics service is reachable',
      fastapi: response.data
    });
  } catch (error) {
    console.error('[Analytics Health Check Failed]:', error.message);
    res.status(503).json({
      status: 'down',
      message: 'Python FastAPI analytics service is unreachable',
      error: error.message,
      code: error.code || 'SERVICE_DOWN'
    });
  }
});

/**
 * @route   GET /api/analytics/player/:id/stats
 * @desc    Proxy player career stats request to FastAPI service
 */
router.get('/player/:id/stats', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await fastapiClient.get(`/player/${id}/stats`, {
      params: req.query
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, `GET /player/${req.params.id}/stats`);
  }
});

/**
 * @route   POST /api/analytics/predict/win
 * @desc    Proxy win probability prediction request to FastAPI service
 */
router.post('/predict/win', async (req, res) => {
  try {
    const response = await fastapiClient.post('/predict/win', req.body);
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, 'POST /predict/win');
  }
});

/**
 * @route   GET /api/analytics/player/:id/form
 * @desc    Proxy player form predictor request to FastAPI service
 */
router.get('/player/:id/form', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await fastapiClient.get(`/player/${id}/form`, {
      params: req.query
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, `GET /player/${req.params.id}/form`);
  }
});

/**
 * @route   GET /api/analytics/team/:id/stats
 * @desc    Proxy team stats request to FastAPI service
 */
router.get('/team/:id/stats', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await fastapiClient.get(`/team/${id}/stats`);
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, `GET /team/${req.params.id}/stats`);
  }
});

/**
 * @route   GET /api/analytics/teams/winrates
 * @desc    Proxy bulk team winrates request to FastAPI service
 */
router.get('/teams/winrates', async (req, res) => {
  try {
    const response = await fastapiClient.get('/teams/winrates');
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, 'GET /teams/winrates');
  }
});

/**
 * @route   GET /api/analytics/team/:id/winrate
 * @desc    Proxy team winrate request to FastAPI service
 */
router.get('/team/:id/winrate', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await fastapiClient.get(`/team/${id}/winrate`);
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, `GET /team/${req.params.id}/winrate`);
  }
});

/**
 * @route   GET /api/analytics/match/compare
 * @desc    Proxy head-to-head match comparison request to FastAPI service
 */
router.get('/match/compare', async (req, res) => {
  try {
    const response = await fastapiClient.get('/match/compare', {
      params: req.query
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, 'GET /match/compare');
  }
});

/**
 * @route   GET /api/analytics/clusters
 * @desc    Proxy player clusters request to FastAPI service
 */
router.get('/clusters', async (req, res) => {
  try {
    const response = await fastapiClient.get('/clusters', {
      params: req.query
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    handleProxyError(error, res, 'GET /clusters');
  }
});

module.exports = router;
