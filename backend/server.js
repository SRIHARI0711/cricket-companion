const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

// Import routes
const cricketRoutes = require('./routes/cricketRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

// Routes
app.use('/api', cricketRoutes);

// Serve frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
    console.log(`Backend is running at http://localhost:${PORT}`);
    console.log(`Frontend is accessible at http://localhost:${PORT}`);
});
