const express = require('express');
const axios = require('axios');
const router = express.Router();

const FASTAPI_BASE_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

/**
 * @route   GET /api/analytics/player/:id/stats
 * @desc    Proxy player career stats request to FastAPI service
 */
router.get('/player/:id/stats', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await axios.get(`${FASTAPI_BASE_URL}/player/${id}/stats`, {
      params: req.query
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('Error proxying player stats to FastAPI:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    res.status(500).json({ error: 'Failed to communicate with Analytics Service (FastAPI)' });
  }
});

/**
 * @route   POST /api/analytics/predict/win
 * @desc    Proxy win probability prediction request to FastAPI service
 */
router.post('/predict/win', async (req, res) => {
  try {
    const response = await axios.post(`${FASTAPI_BASE_URL}/predict/win`, req.body);
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('Error proxying win prediction to FastAPI:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    res.status(500).json({ error: 'Failed to communicate with Analytics Service (FastAPI)' });
  }
});

/**
 * @route   GET /api/analytics/player/:id/form
 * @desc    Proxy player form predictor request to FastAPI service
 */
router.get('/player/:id/form', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await axios.get(`${FASTAPI_BASE_URL}/player/${id}/form`, {
      params: req.query
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('Error proxying player form to FastAPI:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    res.status(500).json({ error: 'Failed to communicate with Analytics Service (FastAPI)' });
  }
});

/**
 * @route   GET /api/analytics/clusters
 * @desc    Proxy player clusters request to FastAPI service
 */
router.get('/clusters', async (req, res) => {
  try {
    const response = await axios.get(`${FASTAPI_BASE_URL}/clusters`, {
      params: req.query
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('Error proxying player clusters to FastAPI:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    res.status(500).json({ error: 'Failed to communicate with Analytics Service (FastAPI)' });
  }
});

module.exports = router;
