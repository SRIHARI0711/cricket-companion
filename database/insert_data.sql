-- Clean Insert Sample Data for Cricket Companion
-- Usage: mysql -u root -p cricket_companion < database/insert_data.sql

USE cricket_companion;

-- 1. Teams (Updated with exact coaches and captains from image)
INSERT INTO teams (id, team_name, coach, captain) VALUES
(1, 'Royal Challengers Bengaluru', 'Andy Flower', 'Rajat Patidar'),
(2, 'Punjab Kings', 'Ricky Ponting', 'Shreyas Iyer'),
(3, 'Kochi Tuskers Kerala', 'Geoff Lawson', 'Mahela Jayawardene'),
(4, 'Delhi Capitals', 'Hemang Badani', 'Axar Patel'),
(5, 'Rising Pune Supergiant', 'Stephen Fleming', 'Steve Smith'),
(6, 'Rajasthan Royals', 'Kumar Sangakkara', 'Riyan Parag'),
(7, 'Gujarat Lions', 'Brad Hodge', 'Suresh Raina'),
(8, 'Sunrisers Hyderabad', 'Daniel Vettori', 'Pat Cummins'),
(9, 'Lucknow Super Giants', 'Justin Langer', 'Rishabh Pant'),
(10, 'Mumbai Indians', 'Mahela Jayawardene', 'Rohit Sharma'),
(11, 'Chennai Super Kings', 'Stephen Fleming', 'MS Dhoni'),
(12, 'Kolkata Knight Riders', 'Chandrakant Pandit', 'Shreyas Iyer')
ON DUPLICATE KEY UPDATE coach=VALUES(coach), captain=VALUES(captain);

-- 2. Players (Original player roster preserved)
INSERT INTO players (id, name, age, role, team) VALUES
(1, 'Rohit Sharma', 37, 'Batsman', 'Mumbai Indians'),
(2, 'MS Dhoni', 43, 'Wicket-keeper', 'Chennai Super Kings'),
(3, 'Virat Kohli', 36, 'Batsman', 'Royal Challengers Bangalore'),
(4, 'Rishabh Pant', 27, 'Wicket-keeper', 'Delhi Capitals'),
(5, 'Jasprit Bumrah', 31, 'Bowler', 'Mumbai Indians'),
(6, 'Ravindra Jadeja', 36, 'All-rounder', 'Chennai Super Kings'),
(7, 'Glenn Maxwell', 36, 'All-rounder', 'Royal Challengers Bangalore'),
(8, 'Prithvi Shaw', 25, 'Batsman', 'Delhi Capitals'),
(9, 'Andre Russell', 36, 'All-rounder', 'Kolkata Knight Riders'),
(10, 'Shikhar Dhawan', 39, 'Batsman', 'Punjab Kings')
ON DUPLICATE KEY UPDATE age=VALUES(age), role=VALUES(role), team=VALUES(team);

-- 3. Series
INSERT INTO series (id, series_name, start_date, end_date, status) VALUES
(1, 'IPL 2024', '2024-03-22', '2024-05-26', 'Completed'),
(2, 'T20 World Cup 2024', '2024-06-01', '2024-06-29', 'Completed'),
(3, 'Asia Cup 2024', '2024-08-30', '2024-09-17', 'Completed'),
(4, 'IPL 2025', '2025-03-15', '2025-05-30', 'Upcoming')
ON DUPLICATE KEY UPDATE start_date=VALUES(start_date), end_date=VALUES(end_date), status=VALUES(status);

-- 4. Matches
INSERT INTO matches (id, series_id, team1_id, team2_id, match_date, venue, winner_id) VALUES
(1, 1, 10, 11, '2024-03-24', 'Wankhede Stadium, Mumbai', 10),
(2, 1, 1, 4, '2024-03-25', 'M. Chinnaswamy Stadium, Bangalore', 1),
(3, 1, 10, 1, '2024-03-28', 'Wankhede Stadium, Mumbai', 10),
(4, 1, 11, 4, '2024-03-29', 'MA Chidambaram Stadium, Chennai', 11)
ON DUPLICATE KEY UPDATE venue=VALUES(venue), winner_id=VALUES(winner_id);

-- 5. Scorecards
INSERT INTO scorecards (id, player_id, match_id, runs_scored, balls_faced, wickets_taken) VALUES
(1, 1, 1, 85, 60, 0),
(2, 2, 1, 45, 35, 0),
(3, 5, 1, 12, 8, 3),
(4, 3, 2, 92, 58, 0),
(5, 4, 2, 67, 45, 0),
(6, 7, 2, 35, 25, 2)
ON DUPLICATE KEY UPDATE runs_scored=VALUES(runs_scored), balls_faced=VALUES(balls_faced), wickets_taken=VALUES(wickets_taken);