-- Drop existing tables if they exist
IF OBJECT_ID('scorecards', 'U') IS NOT NULL DROP TABLE scorecards;
IF OBJECT_ID('matches', 'U') IS NOT NULL DROP TABLE matches;
IF OBJECT_ID('series', 'U') IS NOT NULL DROP TABLE series;
IF OBJECT_ID('players', 'U') IS NOT NULL DROP TABLE players;
IF OBJECT_ID('teams', 'U') IS NOT NULL DROP TABLE teams;

-- Teams table
CREATE TABLE teams (
    id INT IDENTITY(1,1) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    coach VARCHAR(100),
    captain VARCHAR(100),
    created_at DATETIME DEFAULT GETDATE()
);

-- Players table
CREATE TABLE players (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    role VARCHAR(20) CHECK (role IN ('Batsman', 'Bowler', 'All-rounder', 'Wicket-keeper')) NOT NULL,
    team VARCHAR(100),
    created_at DATETIME DEFAULT GETDATE()
);

-- Series table
CREATE TABLE series (
    id INT IDENTITY(1,1) PRIMARY KEY,
    series_name VARCHAR(150) NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) CHECK (status IN ('Upcoming', 'Ongoing', 'Completed')) DEFAULT 'Upcoming',
    created_at DATETIME DEFAULT GETDATE()
);

-- Matches table
CREATE TABLE matches (
    id INT IDENTITY(1,1) PRIMARY KEY,
    series_id INT,
    team1_id INT,
    team2_id INT,
    match_date DATE,
    venue VARCHAR(200),
    winner_id INT,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
    FOREIGN KEY (team1_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (team2_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (winner_id) REFERENCES teams(id) ON DELETE SET NULL
);

-- Scorecards table
CREATE TABLE scorecards (
    id INT IDENTITY(1,1) PRIMARY KEY,
    player_id INT,
    match_id INT,
    runs_scored INT DEFAULT 0,
    balls_faced INT DEFAULT 0,
    wickets_taken INT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
);

-- Insert sample data
INSERT INTO teams (team_name, coach, captain) VALUES
('Royal Challengers Bengaluru', 'Andy Flower', 'Rajat Patidar'),
('Punjab Kings', 'Ricky Ponting', 'Shreyas Iyer'),
('Kochi Tuskers Kerala', 'Geoff Lawson', 'Mahela Jayawardene'),
('Delhi Capitals', 'Hemang Badani', 'Axar Patel'),
('Rising Pune Supergiant', 'Stephen Fleming', 'Steve Smith'),
('Rajasthan Royals', 'Kumar Sangakkara', 'Riyan Parag'),
('Gujarat Lions', 'Brad Hodge', 'Suresh Raina'),
('Sunrisers Hyderabad', 'Daniel Vettori', 'Pat Cummins'),
('Lucknow Super Giants', 'Justin Langer', 'Rishabh Pant'),
('Mumbai Indians', 'Mahela Jayawardene', 'Rohit Sharma'),
('Chennai Super Kings', 'Stephen Fleming', 'MS Dhoni'),
('Kolkata Knight Riders', 'Chandrakant Pandit', 'Shreyas Iyer');

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