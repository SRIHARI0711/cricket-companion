const express = require('express');
const router = express.Router();
const db = require('../db');

// ============ PLAYERS ROUTES ============
// Get all players
router.get('/players', (req, res) => {
  console.log('GET /api/players - Fetching all players');
  db.query('SELECT * FROM players ORDER BY created_at DESC', (err, results) => {
    if (err) {
      console.error('Error fetching players:', err);
      return res.status(500).json({ error: err.message });
    }
    console.log(`Found ${results.length} players`);
    res.json(results);
  });
});

// Get a single player by ID
router.get('/players/:id', (req, res) => {
  const { id } = req.params;
  console.log('GET /api/players/:id - Fetching player with ID:', id);
  db.query('SELECT * FROM players WHERE id = ?', [id], (err, results) => {
    if (err) {
      console.error('Error fetching player:', err);
      return res.status(500).json({ error: err.message });
    }
    if (results.length === 0) {
      return res.status(404).json({ error: 'Player not found' });
    }
    console.log('Found player:', results[0]);
    res.json(results[0]);
  });
});

// Add a new player
router.post('/players', (req, res) => {
  const { name, age, role, team } = req.body;
  console.log('POST /api/players - Adding player:', { name, age, role, team });
  
  if (!name || !age || !role || !team) {
    return res.status(400).json({ error: 'All fields are required' });
  }
  
  db.query(
    'INSERT INTO players (name, age, role, team) VALUES (?, ?, ?, ?)',
    [name, age, role, team],
    (err, result) => {
      if (err) {
        console.error('Error adding player:', err);
        return res.status(500).json({ error: err.message });
      }
      console.log('Player added successfully with ID:', result.insertId);
      res.json({ message: 'Player added successfully', id: result.insertId });
    }
  );
});

// Update a player
router.put('/players/:id', (req, res) => {
  const { id } = req.params;
  const { name, age, role, team } = req.body;
  db.query(
    'UPDATE players SET name = ?, age = ?, role = ?, team = ? WHERE id = ?',
    [name, age, role, team, id],
    (err, result) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Player updated' });
    }
  );
});

// Delete a player
router.delete('/players/:id', (req, res) => {
  const { id } = req.params;
  db.query('DELETE FROM players WHERE id = ?', [id], (err, result) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ message: 'Player deleted' });
  });
});

// ============ TEAMS ROUTES ============
// Get all teams
router.get('/teams', (req, res) => {
  console.log('GET /api/teams - Fetching all teams');
  db.query('SELECT * FROM teams ORDER BY created_at DESC', (err, results) => {
    if (err) {
      console.error('Error fetching teams:', err);
      return res.status(500).json({ error: err.message });
    }
    console.log(`Found ${results.length} teams`);
    res.json(results);
  });
});

// Get a single team by ID
router.get('/teams/:id', (req, res) => {
  const { id } = req.params;
  console.log('GET /api/teams/:id - Fetching team with ID:', id);
  db.query('SELECT * FROM teams WHERE id = ?', [id], (err, results) => {
    if (err) {
      console.error('Error fetching team:', err);
      return res.status(500).json({ error: err.message });
    }
    if (results.length === 0) {
      return res.status(404).json({ error: 'Team not found' });
    }
    console.log('Found team:', results[0]);
    res.json(results[0]);
  });
});

// Add a new team
router.post('/teams', (req, res) => {
  const { team_name, coach, captain } = req.body;
  db.query(
    'INSERT INTO teams (team_name, coach, captain) VALUES (?, ?, ?)',
    [team_name, coach, captain],
    (err, result) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Team added', id: result.insertId });
    }
  );
});

// Update a team
router.put('/teams/:id', (req, res) => {
  const { id } = req.params;
  const { team_name, coach, captain } = req.body;
  db.query(
    'UPDATE teams SET team_name = ?, coach = ?, captain = ? WHERE id = ?',
    [team_name, coach, captain, id],
    (err, result) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Team updated' });
    }
  );
});

// Delete a team
router.delete('/teams/:id', (req, res) => {
  const { id } = req.params;
  db.query('DELETE FROM teams WHERE id = ?', [id], (err, result) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ message: 'Team deleted' });
  });
});

// ============ SERIES ROUTES ============
// Get all series
router.get('/series', (req, res) => {
  db.query('SELECT * FROM series', (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

// Get a single series by ID
router.get('/series/:id', (req, res) => {
  const { id } = req.params;
  console.log('GET /api/series/:id - Fetching series with ID:', id);
  db.query('SELECT * FROM series WHERE id = ?', [id], (err, results) => {
    if (err) {
      console.error('Error fetching series:', err);
      return res.status(500).json({ error: err.message });
    }
    if (results.length === 0) {
      return res.status(404).json({ error: 'Series not found' });
    }
    console.log('Found series:', results[0]);
    res.json(results[0]);
  });
});

// Add a new series
router.post('/series', (req, res) => {
  const { series_name, start_date, end_date, status } = req.body;
  db.query(
    'INSERT INTO series (series_name, start_date, end_date, status) VALUES (?, ?, ?, ?)',
    [series_name, start_date, end_date, status],
    (err, result) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Series added', id: result.insertId });
    }
  );
});

// Update a series
router.put('/series/:id', (req, res) => {
  const { id } = req.params;
  const { series_name, start_date, end_date, status } = req.body;
  console.log('PUT /api/series/:id - Updating series with ID:', id);
  db.query(
    'UPDATE series SET series_name = ?, start_date = ?, end_date = ?, status = ? WHERE id = ?',
    [series_name, start_date, end_date, status || 'upcoming', id],
    (err, result) => {
      if (err) {
        console.error('Error updating series:', err);
        return res.status(500).json({ error: err.message });
      }
      console.log('Series updated successfully');
      res.json({ message: 'Series updated' });
    }
  );
});

// Delete a series
router.delete('/series/:id', (req, res) => {
  const { id } = req.params;
  db.query('DELETE FROM series WHERE id = ?', [id], (err, result) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ message: 'Series deleted' });
  });
});

// ============ MATCHES ROUTES ============
// Get all matches
router.get('/matches', (req, res) => {
  db.query(`
    SELECT m.*, s.series_name, t1.team_name as team1_name, t2.team_name as team2_name
    FROM matches m
    LEFT JOIN series s ON m.series_id = s.id
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
  `, (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

// Get a single match by ID
router.get('/matches/:id', (req, res) => {
  const { id } = req.params;
  console.log('GET /api/matches/:id - Fetching match with ID:', id);
  db.query(`
    SELECT m.*, s.series_name, t1.team_name as team1_name, t2.team_name as team2_name
    FROM matches m
    LEFT JOIN series s ON m.series_id = s.id
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    WHERE m.id = ?
  `, [id], (err, results) => {
    if (err) {
      console.error('Error fetching match:', err);
      return res.status(500).json({ error: err.message });
    }
    if (results.length === 0) {
      return res.status(404).json({ error: 'Match not found' });
    }
    console.log('Found match:', results[0]);
    res.json(results[0]);
  });
});

// Add a new match
router.post('/matches', (req, res) => {
  const { series_id, team1_id, team2_id, match_date, venue, winner_id } = req.body;
  db.query(
    'INSERT INTO matches (series_id, team1_id, team2_id, match_date, venue, winner_id) VALUES (?, ?, ?, ?, ?, ?)',
    [series_id, team1_id, team2_id, match_date, venue, winner_id],
    (err, result) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Match added', id: result.insertId });
    }
  );
});

// Update a match
router.put('/matches/:id', (req, res) => {
  const { id } = req.params;
  const { series_id, team1_id, team2_id, match_date, venue, winner_id } = req.body;
  console.log('PUT /api/matches/:id - Updating match with ID:', id);
  db.query(
    'UPDATE matches SET series_id = ?, team1_id = ?, team2_id = ?, match_date = ?, venue = ?, winner_id = ? WHERE id = ?',
    [series_id, team1_id, team2_id, match_date, venue, winner_id, id],
    (err, result) => {
      if (err) {
        console.error('Error updating match:', err);
        return res.status(500).json({ error: err.message });
      }
      console.log('Match updated successfully');
      res.json({ message: 'Match updated' });
    }
  );
});

// Delete a match
router.delete('/matches/:id', (req, res) => {
  const { id } = req.params;
  db.query('DELETE FROM matches WHERE id = ?', [id], (err, result) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ message: 'Match deleted' });
  });
});

// ============ SCORECARDS ROUTES ============
// Get all scorecards
router.get('/scorecards', (req, res) => {
  db.query(`
    SELECT sc.*, p.name as player_name, m.id as match_id
    FROM scorecards sc
    LEFT JOIN players p ON sc.player_id = p.id
    LEFT JOIN matches m ON sc.match_id = m.id
  `, (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

// Get a single scorecard by ID
router.get('/scorecards/:id', (req, res) => {
  const { id } = req.params;
  console.log('GET /api/scorecards/:id - Fetching scorecard with ID:', id);
  db.query(`
    SELECT sc.*, p.name as player_name, m.id as match_id
    FROM scorecards sc
    LEFT JOIN players p ON sc.player_id = p.id
    LEFT JOIN matches m ON sc.match_id = m.id
    WHERE sc.id = ?
  `, [id], (err, results) => {
    if (err) {
      console.error('Error fetching scorecard:', err);
      return res.status(500).json({ error: err.message });
    }
    if (results.length === 0) {
      return res.status(404).json({ error: 'Scorecard not found' });
    }
    console.log('Found scorecard:', results[0]);
    res.json(results[0]);
  });
});

// Add a new scorecard
router.post('/scorecards', (req, res) => {
  const { player_id, match_id, runs_scored, balls_faced, wickets_taken } = req.body;
  db.query(
    'INSERT INTO scorecards (player_id, match_id, runs_scored, balls_faced, wickets_taken) VALUES (?, ?, ?, ?, ?)',
    [player_id, match_id, runs_scored, balls_faced, wickets_taken],
    (err, result) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Scorecard added', id: result.insertId });
    }
  );
});

// Update a scorecard
router.put('/scorecards/:id', (req, res) => {
  const { id } = req.params;
  const { player_id, match_id, runs_scored, balls_faced, wickets_taken } = req.body;
  console.log('PUT /api/scorecards/:id - Updating scorecard with ID:', id);
  db.query(
    'UPDATE scorecards SET player_id = ?, match_id = ?, runs_scored = ?, balls_faced = ?, wickets_taken = ? WHERE id = ?',
    [player_id, match_id, runs_scored, balls_faced, wickets_taken, id],
    (err, result) => {
      if (err) {
        console.error('Error updating scorecard:', err);
        return res.status(500).json({ error: err.message });
      }
      console.log('Scorecard updated successfully');
      res.json({ message: 'Scorecard updated' });
    }
  );
});

// Delete a scorecard
router.delete('/scorecards/:id', (req, res) => {
  const { id } = req.params;
  db.query('DELETE FROM scorecards WHERE id = ?', [id], (err, result) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ message: 'Scorecard deleted' });
  });
});

module.exports = router;
