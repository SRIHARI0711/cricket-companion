-- Cricket Companion Database Schema
-- Use database
USE cricket_companion;

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    coach VARCHAR(100),
    captain VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players table
CREATE TABLE IF NOT EXISTS players (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    role ENUM('Batsman', 'Bowler', 'All-rounder', 'Wicket-keeper') NOT NULL,
    team VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Series table
CREATE TABLE IF NOT EXISTS series (
    id INT AUTO_INCREMENT PRIMARY KEY,
    series_name VARCHAR(150) NOT NULL,
    start_date DATE,
    end_date DATE,
    status ENUM('Upcoming', 'Ongoing', 'Completed') DEFAULT 'Upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    series_id INT,
    team1_id INT,
    team2_id INT,
    match_date DATE,
    venue VARCHAR(200),
    winner_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
    FOREIGN KEY (team1_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (team2_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (winner_id) REFERENCES teams(id) ON DELETE SET NULL
);

-- Scorecards table
CREATE TABLE IF NOT EXISTS scorecards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    match_id INT,
    runs_scored INT DEFAULT 0,
    balls_faced INT DEFAULT 0,
    wickets_taken INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
);

-- Insert sample data
-- Teams
INSERT INTO teams (team_name, coach, captain) VALUES
('Mumbai Indians', 'Mahela Jayawardene', 'Rohit Sharma'),
('Chennai Super Kings', 'Stephen Fleming', 'MS Dhoni'),
('Royal Challengers Bangalore', 'Mike Hesson', 'Faf du Plessis'),
('Delhi Capitals', 'Ricky Ponting', 'Rishabh Pant'),
('Kolkata Knight Riders', 'Brendon McCullum', 'Shreyas Iyer'),
('Punjab Kings', 'Trevor Bayliss', 'Shikhar Dhawan');

-- Players
INSERT INTO players (name, age, role, team) VALUES
('Rohit Sharma', 37, 'Batsman', 'Mumbai Indians'),
('MS Dhoni', 43, 'Wicket-keeper', 'Chennai Super Kings'),
('Virat Kohli', 36, 'Batsman', 'Royal Challengers Bangalore'),
('Rishabh Pant', 27, 'Wicket-keeper', 'Delhi Capitals'),
('Jasprit Bumrah', 31, 'Bowler', 'Mumbai Indians'),
('Ravindra Jadeja', 36, 'All-rounder', 'Chennai Super Kings'),
('Glenn Maxwell', 36, 'All-rounder', 'Royal Challengers Bangalore'),
('Prithvi Shaw', 25, 'Batsman', 'Delhi Capitals'),
('Andre Russell', 36, 'All-rounder', 'Kolkata Knight Riders'),
('Shikhar Dhawan', 39, 'Batsman', 'Punjab Kings');

-- Series
INSERT INTO series (series_name, start_date, end_date, status) VALUES
('IPL 2024', '2024-03-22', '2024-05-26', 'Completed'),
('T20 World Cup 2024', '2024-06-01', '2024-06-29', 'Completed'),
('IPL 2025', '2025-03-15', '2025-05-30', 'Upcoming'),
('Asia Cup 2024', '2024-08-30', '2024-09-17', 'Completed');

-- Matches (sample)
INSERT INTO matches (series_id, team1_id, team2_id, match_date, venue, winner_id) VALUES
(1, 1, 2, '2024-03-24', 'Wankhede Stadium, Mumbai', 1),
(1, 3, 4, '2024-03-25', 'M. Chinnaswamy Stadium, Bangalore', 3),
(1, 1, 3, '2024-03-28', 'Wankhede Stadium, Mumbai', 1),
(1, 2, 4, '2024-03-29', 'MA Chidambaram Stadium, Chennai', 2);

-- Scorecards (sample)
INSERT INTO scorecards (player_id, match_id, runs_scored, balls_faced, wickets_taken) VALUES
(1, 1, 85, 60, 0),  -- Rohit Sharma
(2, 1, 45, 35, 0),  -- MS Dhoni
(5, 1, 12, 8, 3),   -- Jasprit Bumrah
(3, 2, 92, 58, 0),  -- Virat Kohli
(4, 2, 67, 45, 0),  -- Rishabh Pant
(7, 2, 35, 25, 2);  -- Glenn Maxwell

-- Create indexes for better performance
CREATE INDEX idx_players_team ON players(team);
CREATE INDEX idx_matches_series ON matches(series_id);
CREATE INDEX idx_scorecards_player ON scorecards(player_id);
CREATE INDEX idx_scorecards_match ON scorecards(match_id);