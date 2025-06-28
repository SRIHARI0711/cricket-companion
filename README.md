# 🏏 Cricket Companion

A comprehensive cricket management system built with Node.js, Express.js, and MySQL. This application provides a complete solution for managing cricket teams, players, series, matches, and scorecards with a modern web interface.

## ✨ Features

- **Team Management**: Create, view, update, and delete cricket teams with coach and captain information
- **Player Management**: Comprehensive player profiles with roles, ages, and team associations
- **Series Tracking**: Manage cricket series with start/end dates and status tracking
- **Match Management**: Schedule and track matches with venue and winner information
- **Scorecard System**: Detailed player performance tracking with runs, balls faced, and wickets
- **Modern UI**: Dark/light theme toggle with responsive design
- **Authentication**: Simple login system with default credentials
- **RESTful API**: Complete CRUD operations for all entities

## 🚀 Tech Stack

- **Backend**: Node.js, Express.js
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Dependencies**: 
  - cors (Cross-origin resource sharing)
  - dotenv (Environment variables)
  - mysql2 (MySQL database driver)
  - nodemon (Development server)

## 📋 Prerequisites

Before running this application, make sure you have:

- Node.js (v14 or higher)
- MySQL Server
- npm or yarn package manager

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cricket_companion
Install dependencies

npm install
Set up environment variables Create a .env file in the root directory:

DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=cricket_companion
PORT=5000
Set up the database

npm run setup-db
Start the application

# Production mode
npm start

# Development mode (with auto-restart)
npm run dev
Access the application Open your browser and navigate to http://localhost:5000

🔐 Default Login Credentials
Username: admin
Password: cricket123
📁 Project Structure
cricket_companion/
├── backend/
│   ├── server.js          # Main server file
│   ├── db.js              # Database connection
│   └── routes/
│       └── cricketRoutes.js # API routes
├── frontend/
│   ├── index.html         # Main HTML file
│   ├── style.css          # Styling
│   ├── script.js          # Main JavaScript
│   └── search.js          # Search functionality
├── database/
│   ├── setup.js           # Database setup script
│   ├── create_tables.sql  # Table creation queries
│   ├── insert_data.sql    # Sample data insertion
│   └── init.sql           # Database initialization
├── package.json           # Project dependencies
└── .gitignore            # Git ignore rules
🔌 API Endpoints
Players
GET /api/players - Get all players
GET /api/players/:id - Get player by ID
POST /api/players - Create new player
PUT /api/players/:id - Update player
DELETE /api/players/:id - Delete player
Teams
GET /api/teams - Get all teams
GET /api/teams/:id - Get team by ID
POST /api/teams - Create new team
PUT /api/teams/:id - Update team
DELETE /api/teams/:id - Delete team
Series
GET /api/series - Get all series
GET /api/series/:id - Get series by ID
POST /api/series - Create new series
PUT /api/series/:id - Update series
DELETE /api/series/:id - Delete series
Matches
GET /api/matches - Get all matches
GET /api/matches/:id - Get match by ID
POST /api/matches - Create new match
PUT /api/matches/:id - Update match
DELETE /api/matches/:id - Delete match
Scorecards
GET /api/scorecards - Get all scorecards
GET /api/scorecards/:id - Get scorecard by ID
POST /api/scorecards - Create new scorecard
PUT /api/scorecards/:id - Update scorecard
DELETE /api/scorecards/:id - Delete scorecard
🗄️ Database Schema
The application uses the following main tables:

teams: Team information (name, coach, captain)
players: Player details (name, age, role, team)
series: Cricket series (name, dates, status)
matches: Match details (teams, venue, date, winner)
scorecards: Player performance (runs, balls, wickets)
🎨 Features Overview
Dashboard
Welcome page with feature overview
Quick navigation to different sections
Theme toggle (dark/light mode)
Team Management
Add, edit, and delete teams
View team details with coach and captain info
Search functionality
Player Management
Comprehensive player profiles
Role-based categorization
Team association tracking
Series & Matches
Series creation and management
Match scheduling and results
Winner tracking
Scorecards
Detailed performance metrics
Player statistics tracking
Match-wise performance records
🚀 Development
Available Scripts
npm start - Start production server
npm run dev - Start development server with auto-reload
npm run setup-db - Initialize database with sample data
Development Mode
For development, use:

npm run dev
This will start the server with nodemon for automatic restarts on file changes.

🤝 Contributing
Fork the repository
Create a feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request
📝 License
This project is licensed under the ISC License.

👥 Authors
Chandan,
Srihari,
Gagan
🙏 Acknowledgments
Built with modern web technologies
Responsive design for all devices
RESTful API architecture
Comprehensive error handling
© 2025 Cricket Companion. All rights reserved.
