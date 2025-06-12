// API Base URL
const API_BASE_URL = 'http://localhost:5000/api';

// ============ AUTHENTICATION FUNCTIONALITY ============
const DEFAULT_CREDENTIALS = {
    username: 'admin',
    password: 'cricket123'
};

// Check if user is logged in on page load
document.addEventListener('DOMContentLoaded', function() {
    const isLoggedIn = localStorage.getItem('cricketAppLoggedIn');
    const username = localStorage.getItem('cricketAppUsername');
    
    if (isLoggedIn === 'true' && username) {
        showMainApp(username);
    } else {
        showLoginPage();
    }
    
    // Add login form event listener
    const loginForm = document.getElementById('loginForm');
    console.log('Login form found:', loginForm);
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
        console.log('Login form event listener added');
    } else {
        console.log('Login form not found!');
    }
});

function handleLogin(event) {
    console.log('Login form submitted');
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const username = formData.get('username');
    const password = formData.get('password');
    
    console.log('Username:', username, 'Password:', password);
    console.log('Expected:', DEFAULT_CREDENTIALS.username, DEFAULT_CREDENTIALS.password);
    
    // Validate credentials
    if (username === DEFAULT_CREDENTIALS.username && password === DEFAULT_CREDENTIALS.password) {
        console.log('Login successful');
        // Store login state
        localStorage.setItem('cricketAppLoggedIn', 'true');
        localStorage.setItem('cricketAppUsername', username);
        
        showMainApp(username);
        showNotification('Login successful! Welcome to Cricket Companion.', 'success');
    } else {
        console.log('Login failed');
        showNotification('Invalid credentials. Please try again.', 'error');
        
        // Clear the form
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        document.getElementById('username').focus();
    }
}

function handleLoginClick(event) {
    console.log('Login button clicked');
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    console.log('Username:', username, 'Password:', password);
    console.log('Expected:', DEFAULT_CREDENTIALS.username, DEFAULT_CREDENTIALS.password);
    
    // Validate credentials
    if (username === DEFAULT_CREDENTIALS.username && password === DEFAULT_CREDENTIALS.password) {
        console.log('Login successful');
        // Store login state
        localStorage.setItem('cricketAppLoggedIn', 'true');
        localStorage.setItem('cricketAppUsername', username);
        
        showMainApp(username);
        showNotification('Login successful! Welcome to Cricket Companion.', 'success');
    } else {
        console.log('Login failed');
        showNotification('Invalid credentials. Please try again.', 'error');
        
        // Clear the form
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        document.getElementById('username').focus();
    }
}

function showLoginPage() {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
    
    // Set up login form event listener
    setTimeout(() => {
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.querySelector('.login-btn');
        console.log('Setting up login form:', loginForm);
        console.log('Login button found:', loginBtn);
        
        if (loginForm) {
            // Remove any existing event listeners to avoid duplicates
            loginForm.removeEventListener('submit', handleLogin);
            loginForm.addEventListener('submit', handleLogin);
            console.log('Login form event listener added');
        }
        
        // Also add click event listener to the button as backup
        if (loginBtn) {
            loginBtn.removeEventListener('click', handleLoginClick);
            loginBtn.addEventListener('click', handleLoginClick);
            console.log('Login button click listener added');
        }
        
        // Focus on username field
        const usernameField = document.getElementById('username');
        if (usernameField) {
            usernameField.focus();
        }
    }, 100);
}

function showMainApp(username) {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainApp').style.display = 'flex';
    
    // Update welcome message in sidebar
    const welcomeUser = document.getElementById('welcomeUser');
    if (welcomeUser) {
        welcomeUser.textContent = `Welcome, ${username}!`;
    }
    
    // Update user info in header
    const userInfo = document.getElementById('userInfo');
    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');
    
    if (userInfo) {
        userInfo.classList.remove('hidden');
    }
    if (userName) {
        userName.textContent = username;
    }
    if (userAvatar) {
        userAvatar.textContent = username.charAt(0).toUpperCase();
    }
    
    // Setup navigation, theme toggle, and mobile toggle
    setupNavigation();
    setupThemeToggle();
    setupMobileToggle();
    
    // Setup logo click to go home
    setupLogoClick();
    
    // Setup logout buttons
    setupLogoutButtons();
    
    // Show home page by default
    showPage('home');
    
    // Set home nav item as active
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(nav => nav.classList.remove('active'));
    const homeNav = document.querySelector('.nav-item[data-page="home"]');
    if (homeNav) {
        homeNav.classList.add('active');
    }
}

function setupLogoutButtons() {
    // Setup logout buttons with event listeners as backup
    const logoutButtons = document.querySelectorAll('.logout-btn');
    
    logoutButtons.forEach(button => {
        // Remove any existing event listeners
        button.removeEventListener('click', logout);
        // Add new event listener
        button.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    });
}

function logout() {
    // Clear login state
    localStorage.removeItem('cricketAppLoggedIn');
    localStorage.removeItem('cricketAppUsername');
    
    // Hide user info in header
    const userInfo = document.getElementById('userInfo');
    if (userInfo) {
        userInfo.classList.add('hidden');
    }
    
    // Show login page
    showLoginPage();
    
    showNotification('You have been logged out successfully.', 'success');
}

// Global variables
let currentUser = null;

// Remove the duplicate initialization since we have authentication-based initialization above

// Navigation setup
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const page = this.getAttribute('data-page');
            showPage(page);
            
            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// Theme toggle setup
function setupThemeToggle() {
    const themeCheckbox = document.getElementById('themeCheckbox');
    const body = document.body;
    
    // Set initial state of checkbox based on current theme
    const currentTheme = body.getAttribute('data-theme');
    themeCheckbox.checked = currentTheme === 'light';
    
    // Add change event listener to checkbox
    themeCheckbox.addEventListener('change', function() {
        if (this.checked) {
            body.setAttribute('data-theme', 'light');
        } else {
            body.setAttribute('data-theme', 'dark');
        }
    });
}

// Mobile toggle setup
function setupMobileToggle() {
    const mobileToggle = document.getElementById('mobileToggle');
    const sidebar = document.getElementById('sidebar');
    
    mobileToggle.addEventListener('click', function() {
        sidebar.classList.toggle('active');
    });
}

// Logo click setup to go home
function setupLogoClick() {
    const appLogo = document.getElementById('appLogo');
    
    if (appLogo) {
        appLogo.addEventListener('click', function() {
            // Show the home page
            showPage('home');
            
            // Update active state in navigation
            const navItems = document.querySelectorAll('.nav-item');
            navItems.forEach(nav => nav.classList.remove('active'));
            const homeNav = document.querySelector('.nav-item[data-page="home"]');
            if (homeNav) {
                homeNav.classList.add('active');
            }
        });
    }
}

// Show specific page
function showPage(pageName) {
    // Hide all pages
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.add('hidden'));
    
    // Show selected page
    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) {
        targetPage.classList.remove('hidden');
        
        // Load data for specific pages
        switch(pageName) {
            case 'teams':
                loadTeams();
                break;
            case 'players':
                loadPlayers();
                break;
            case 'series':
                loadSeries();
                break;
            case 'matches':
                loadMatches();
                break;
            case 'scorecards':
                loadScorecards();
                break;
        }
    }
}

// ============ TEAMS FUNCTIONALITY ============
async function loadTeams() {
    try {
        const response = await fetch(`${API_BASE_URL}/teams`);
        const teams = await response.json();
        loadTeamsWithSearch(teams); // Use our search-enabled function
    } catch (error) {
        console.error('Error loading teams:', error);
        loadTeamsWithSearch([]); // Empty array on error
    }
}

function displayTeams(teams) {
    const tbody = document.getElementById('teamsTableBody');
    tbody.innerHTML = '';
    
    if (teams.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="5" style="text-align: center;">No teams found</td>`;
        tbody.appendChild(row);
        return;
    }
    
    teams.forEach(team => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${team.team_name}</td>
            <td>${team.coach}</td>
            <td>${team.captain}</td>
            <td>-</td>
            <td>
                <button class="btn btn-sm" onclick="editTeam(${team.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteTeam(${team.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAddTeamForm() {
    const formHtml = `
        <div class="modal" style="display: block;">
            <div class="modal-content">
                <span class="close" onclick="hideModal()">&times;</span>
                <h2>Add New Team</h2>
                <form id="addTeamForm" onsubmit="handleAddTeam(event)">
                    <div class="form-group">
                        <label for="teamName">Team Name:</label>
                        <input type="text" id="teamName" name="teamName" required>
                    </div>
                    <div class="form-group">
                        <label for="coach">Coach:</label>
                        <input type="text" id="coach" name="coach" required>
                    </div>
                    <div class="form-group">
                        <label for="captain">Captain:</label>
                        <input type="text" id="captain" name="captain" required>
                    </div>
                    <button type="submit" class="btn">Add Team</button>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

async function handleAddTeam(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const teamData = {
        team_name: formData.get('teamName'),
        coach: formData.get('coach'),
        captain: formData.get('captain')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/teams`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(teamData)
        });
        
        if (response.ok) {
            hideModal();
            loadTeams();
            showNotification('Team added successfully!');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to add team'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding team:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

// ============ PLAYERS FUNCTIONALITY ============
async function loadPlayers() {
    try {
        const response = await fetch(`${API_BASE_URL}/players`);
        const players = await response.json();
        loadPlayersWithSearch(players); // Use our search-enabled function
    } catch (error) {
        console.error('Error loading players:', error);
        loadPlayersWithSearch([]); // Empty array on error
    }
}

function displayPlayers(players) {
    const tbody = document.getElementById('playersTableBody');
    tbody.innerHTML = '';
    
    if (players.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="5" style="text-align: center;">No players found</td>`;
        tbody.appendChild(row);
        return;
    }
    
    players.forEach(player => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${player.name}</td>
            <td>${player.age}</td>
            <td>${player.role}</td>
            <td>${player.team}</td>
            <td>
                <button class="btn btn-sm" onclick="editPlayer(${player.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deletePlayer(${player.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAddPlayerForm() {
    const formHtml = `
        <div class="modal" style="display: block;">
            <div class="modal-content">
                <span class="close" onclick="hideModal()">&times;</span>
                <h2>Add New Player</h2>
                <form id="addPlayerForm" onsubmit="handleAddPlayer(event)">
                    <div class="form-group">
                        <label for="playerName">Name:</label>
                        <input type="text" id="playerName" name="playerName" required>
                    </div>
                    <div class="form-group">
                        <label for="playerAge">Age:</label>
                        <input type="number" id="playerAge" name="playerAge" required>
                    </div>
                    <div class="form-group">
                        <label for="playerRole">Role:</label>
                        <select id="playerRole" name="playerRole" required>
                            <option value="">Select Role</option>
                            <option value="Batsman">Batsman</option>
                            <option value="Bowler">Bowler</option>
                            <option value="All-rounder">All-rounder</option>
                            <option value="Wicket-keeper">Wicket-keeper</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="playerTeam">Team:</label>
                        <input type="text" id="playerTeam" name="playerTeam" required>
                    </div>
                    <button type="submit" class="btn">Add Player</button>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

async function handleAddPlayer(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const playerData = {
        name: formData.get('playerName'),
        age: parseInt(formData.get('playerAge')),
        role: formData.get('playerRole'),
        team: formData.get('playerTeam')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/players`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(playerData)
        });
        
        if (response.ok) {
            hideModal();
            loadPlayers();
            showNotification('Player added successfully!');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to add player'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding player:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

// ============ SERIES FUNCTIONALITY ============
async function loadSeries() {
    try {
        const response = await fetch(`${API_BASE_URL}/series`);
        const series = await response.json();
        loadSeriesWithSearch(series); // Use our search-enabled function
    } catch (error) {
        console.error('Error loading series:', error);
        loadSeriesWithSearch([]); // Empty array on error
    }
}

function displaySeries(series) {
    const tbody = document.getElementById('seriesTableBody');
    tbody.innerHTML = '';
    
    if (series.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6" style="text-align: center;">No series found</td>`;
        tbody.appendChild(row);
        return;
    }
    
    series.forEach(s => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${s.series_name}</td>
            <td>${new Date(s.start_date).toLocaleDateString()}</td>
            <td>${new Date(s.end_date).toLocaleDateString()}</td>
            <td>${s.status}</td>
            <td>-</td>
            <td>
                <button class="btn btn-sm" onclick="editSeries(${s.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteSeries(${s.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAddSeriesForm() {
    console.log('showAddSeriesForm called');
    const formHtml = `
        <div class="modal" style="display: block;">
            <div class="modal-content">
                <span class="close" onclick="hideModal()">&times;</span>
                <h2>Add New Series</h2>
                <form id="addSeriesForm" onsubmit="handleAddSeries(event)">
                    <div class="form-group">
                        <label for="seriesName">Series Name:</label>
                        <input type="text" id="seriesName" name="seriesName" required>
                    </div>
                    <div class="form-group">
                        <label for="startDate">Start Date:</label>
                        <input type="date" id="startDate" name="startDate" required>
                    </div>
                    <div class="form-group">
                        <label for="endDate">End Date:</label>
                        <input type="date" id="endDate" name="endDate" required>
                    </div>
                    <div class="form-group">
                        <label for="status">Status:</label>
                        <select id="status" name="status" required>
                            <option value="">Select Status</option>
                            <option value="Upcoming">Upcoming</option>
                            <option value="Ongoing">Ongoing</option>
                            <option value="Completed">Completed</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Add Series</button>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

async function handleAddSeries(event) {
    event.preventDefault();
    console.log('handleAddSeries called');
    const formData = new FormData(event.target);
    const seriesData = {
        series_name: formData.get('seriesName'),
        start_date: formData.get('startDate'),
        end_date: formData.get('endDate'),
        status: formData.get('status')
    };
    console.log('Series data:', seriesData);
    
    try {
        const response = await fetch(`${API_BASE_URL}/series`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(seriesData)
        });
        
        if (response.ok) {
            hideModal();
            loadSeries();
            showNotification('Series added successfully!');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to add series'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding series:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

// ============ MATCHES FUNCTIONALITY ============
async function loadMatches() {
    try {
        const response = await fetch(`${API_BASE_URL}/matches`);
        const matches = await response.json();
        loadMatchesWithSearch(matches); // Use our search-enabled function
    } catch (error) {
        console.error('Error loading matches:', error);
        loadMatchesWithSearch([]); // Empty array on error
    }
}

function displayMatches(matches) {
    const tbody = document.getElementById('matchesTableBody');
    tbody.innerHTML = '';
    
    if (matches.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6" style="text-align: center;">No matches found</td>`;
        tbody.appendChild(row);
        return;
    }
    
    matches.forEach(match => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${match.team1_name} vs ${match.team2_name}</td>
            <td>${match.series_name}</td>
            <td>${new Date(match.match_date).toLocaleDateString()}</td>
            <td>${match.venue}</td>
            <td>-</td>
            <td>
                <button class="btn btn-sm" onclick="editMatch(${match.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteMatch(${match.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAddMatchForm() {
    const formHtml = `
        <div class="modal" style="display: block;">
            <div class="modal-content">
                <span class="close" onclick="hideModal()">&times;</span>
                <h2>Add New Match</h2>
                <form id="addMatchForm" onsubmit="handleAddMatch(event)">
                    <div class="form-group">
                        <label for="seriesId">Series ID:</label>
                        <input type="number" id="seriesId" name="seriesId" required>
                    </div>
                    <div class="form-group">
                        <label for="team1Id">Team 1 ID:</label>
                        <input type="number" id="team1Id" name="team1Id" required>
                    </div>
                    <div class="form-group">
                        <label for="team2Id">Team 2 ID:</label>
                        <input type="number" id="team2Id" name="team2Id" required>
                    </div>
                    <div class="form-group">
                        <label for="matchDate">Match Date:</label>
                        <input type="date" id="matchDate" name="matchDate" required>
                    </div>
                    <div class="form-group">
                        <label for="venue">Venue:</label>
                        <input type="text" id="venue" name="venue" required>
                    </div>
                    <div class="form-group">
                        <label for="winnerId">Winner ID (optional):</label>
                        <input type="number" id="winnerId" name="winnerId">
                    </div>
                    <button type="submit" class="btn">Add Match</button>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

async function handleAddMatch(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const matchData = {
        series_id: parseInt(formData.get('seriesId')),
        team1_id: parseInt(formData.get('team1Id')),
        team2_id: parseInt(formData.get('team2Id')),
        match_date: formData.get('matchDate'),
        venue: formData.get('venue'),
        winner_id: formData.get('winnerId') ? parseInt(formData.get('winnerId')) : null
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/matches`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(matchData)
        });
        
        if (response.ok) {
            hideModal();
            loadMatches();
            showNotification('Match added successfully!');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to add match'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding match:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

// ============ SCORECARDS FUNCTIONALITY ============
async function loadScorecards() {
    try {
        const response = await fetch(`${API_BASE_URL}/scorecards`);
        const scorecards = await response.json();
        loadScorecardsWithSearch(scorecards); // Use our search-enabled function
    } catch (error) {
        console.error('Error loading scorecards:', error);
        loadScorecardsWithSearch([]); // Empty array on error
    }
}

function displayScorecards(scorecards) {
    const tbody = document.getElementById('scorecardsTableBody');
    tbody.innerHTML = '';
    
    if (scorecards.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="5" style="text-align: center;">No scorecards found</td>`;
        tbody.appendChild(row);
        return;
    }
    
    scorecards.forEach(scorecard => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${scorecard.player_name}</td>
            <td>Match ${scorecard.match_id}</td>
            <td>${scorecard.runs_scored}</td>
            <td>${scorecard.balls_faced}</td>
            <td>${scorecard.wickets_taken}</td>
            <td>
                <button class="btn btn-sm" onclick="editScorecard(${scorecard.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteScorecard(${scorecard.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ============ UTILITY FUNCTIONS ============
function hideModal() {
    const modal = document.querySelector('.modal');
    if (modal) {
        modal.remove();
    }
}

function showComingSoonAlert() {
    alert("This feature will be soon available!");
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem;
        background: ${type === 'error' ? '#ff4444' : '#44ff44'};
        color: white;
        border-radius: 8px;
        z-index: 1000;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// ============ LOGIN FUNCTIONALITY ============
function showLogin() {
    document.getElementById('loginModal').style.display = 'block';
}

function hideLogin() {
    document.getElementById('loginModal').style.display = 'none';
}

function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    // Simple demo login
    if (username && password) {
        currentUser = { username };
        document.getElementById('userInfo').classList.remove('hidden');
        document.getElementById('userName').textContent = username;
        document.getElementById('loginBtn').style.display = 'none';
        hideLogin();
        showNotification('Login successful!');
    }
}



// Placeholder functions for edit/delete operations
// ============ MODAL FUNCTIONALITY ============
function showFormModal() {
    document.getElementById('formModal').style.display = 'block';
}

function hideFormModal() {
    document.getElementById('formModal').style.display = 'none';
    document.getElementById('formContent').innerHTML = '';
}

// Helper function to load teams for dropdown
async function loadTeamsForDropdown(selectId, selectedTeamId = null) {
    try {
        const response = await fetch(`${API_BASE_URL}/teams`);
        const teams = await response.json();
        
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select a team</option>';
        
        teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team.id;
            option.textContent = team.name;
            if (selectedTeamId && team.id === selectedTeamId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading teams for dropdown:', error);
    }
}

// Helper function to load matches for dropdown
async function loadMatchesForDropdown(selectId, selectedMatchId = null) {
    try {
        const response = await fetch(`${API_BASE_URL}/matches`);
        const matches = await response.json();
        
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select a match</option>';
        
        matches.forEach(match => {
            const option = document.createElement('option');
            option.value = match.id;
            option.textContent = `${match.team1_name} vs ${match.team2_name} - ${match.match_date}`;
            if (selectedMatchId && match.id === selectedMatchId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading matches for dropdown:', error);
    }
}

// ============ EDIT FUNCTIONALITY ============
async function editTeam(id) {
    try {
        // Fetch team data
        const response = await fetch(`${API_BASE_URL}/teams/${id}`);
        const team = await response.json();
        
        if (response.ok) {
            // Create edit form modal
            const formHtml = `
                <div class="modal" style="display: block;">
                    <div class="modal-content">
                        <span class="close" onclick="hideModal()">&times;</span>
                        <h2>Edit Team</h2>
                        <form id="editTeamForm" onsubmit="handleEditTeam(event, ${team.id})">
                            <div class="form-group">
                                <label for="editTeamName">Team Name:</label>
                                <input type="text" id="editTeamName" name="teamName" value="${team.team_name || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editCoach">Coach:</label>
                                <input type="text" id="editCoach" name="coach" value="${team.coach || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editCaptain">Captain:</label>
                                <input type="text" id="editCaptain" name="captain" value="${team.captain || ''}" required>
                            </div>
                            <button type="submit" class="btn">Update Team</button>
                            <button type="button" class="btn btn-secondary" onclick="hideModal()">Cancel</button>
                        </form>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', formHtml);
        } else {
            showNotification('Error loading team data', 'error');
        }
    } catch (error) {
        console.error('Error loading team:', error);
        showNotification('Error loading team data', 'error');
    }
}

async function handleEditTeam(event, teamId) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const teamData = {
        team_name: formData.get('teamName'),
        coach: formData.get('coach'),
        captain: formData.get('captain')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(teamData)
        });
        
        if (response.ok) {
            hideModal();
            loadTeams();
            showNotification('Team updated successfully!', 'success');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to update team'}`, 'error');
        }
    } catch (error) {
        console.error('Error updating team:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

async function editPlayer(id) {
    try {
        // Fetch player data
        const response = await fetch(`${API_BASE_URL}/players/${id}`);
        const player = await response.json();
        
        if (response.ok) {
            // First load teams for the dropdown
            const teamsResponse = await fetch(`${API_BASE_URL}/teams`);
            const teams = await teamsResponse.json();
            
            let teamsOptions = '<option value="">Select a team</option>';
            teams.forEach(team => {
                const selected = player.team_id === team.id ? 'selected' : '';
                teamsOptions += `<option value="${team.id}" ${selected}>${team.team_name}</option>`;
            });
            
            // Create edit form modal
            const formHtml = `
                <div class="modal" style="display: block;">
                    <div class="modal-content">
                        <span class="close" onclick="hideModal()">&times;</span>
                        <h2>Edit Player</h2>
                        <form id="editPlayerForm" onsubmit="handleEditPlayer(event, ${player.id})">
                            <div class="form-group">
                                <label for="editPlayerName">Player Name:</label>
                                <input type="text" id="editPlayerName" name="playerName" value="${player.name || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editPlayerAge">Age:</label>
                                <input type="number" id="editPlayerAge" name="age" value="${player.age || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editPlayerRole">Role:</label>
                                <select id="editPlayerRole" name="role" required>
                                    <option value="Batsman" ${player.role === 'Batsman' ? 'selected' : ''}>Batsman</option>
                                    <option value="Bowler" ${player.role === 'Bowler' ? 'selected' : ''}>Bowler</option>
                                    <option value="All-rounder" ${player.role === 'All-rounder' ? 'selected' : ''}>All-rounder</option>
                                    <option value="Wicket-keeper" ${player.role === 'Wicket-keeper' ? 'selected' : ''}>Wicket-keeper</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editPlayerTeam">Team:</label>
                                <select id="editPlayerTeam" name="teamId" required>
                                    ${teamsOptions}
                                </select>
                            </div>
                            <button type="submit" class="btn">Update Player</button>
                            <button type="button" class="btn btn-secondary" onclick="hideModal()">Cancel</button>
                        </form>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', formHtml);
        } else {
            showNotification('Error loading player data', 'error');
        }
    } catch (error) {
        console.error('Error loading player:', error);
        showNotification('Error loading player data', 'error');
    }
}

async function handleEditPlayer(event, playerId) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const playerData = {
        name: formData.get('playerName'),
        age: parseInt(formData.get('age')),
        role: formData.get('role'),
        team_id: parseInt(formData.get('teamId'))
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/players/${playerId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(playerData)
        });
        
        if (response.ok) {
            hideModal();
            loadPlayers();
            showNotification('Player updated successfully!', 'success');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to update player'}`, 'error');
        }
    } catch (error) {
        console.error('Error updating player:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

async function editSeries(id) {
    try {
        // Fetch series data
        const response = await fetch(`${API_BASE_URL}/series/${id}`);
        const series = await response.json();
        
        if (response.ok) {
            // Create edit form modal
            const formHtml = `
                <div class="modal" style="display: block;">
                    <div class="modal-content">
                        <span class="close" onclick="hideModal()">&times;</span>
                        <h2>Edit Series</h2>
                        <form id="editSeriesForm" onsubmit="handleEditSeries(event, ${series.id})">
                            <div class="form-group">
                                <label for="editSeriesName">Series Name:</label>
                                <input type="text" id="editSeriesName" name="seriesName" value="${series.series_name || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editStartDate">Start Date:</label>
                                <input type="date" id="editStartDate" name="startDate" value="${series.start_date || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editEndDate">End Date:</label>
                                <input type="date" id="editEndDate" name="endDate" value="${series.end_date || ''}" required>
                            </div>
                            <button type="submit" class="btn">Update Series</button>
                            <button type="button" class="btn btn-secondary" onclick="hideModal()">Cancel</button>
                        </form>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', formHtml);
        } else {
            showNotification('Error loading series data', 'error');
        }
    } catch (error) {
        console.error('Error loading series:', error);
        showNotification('Error loading series data', 'error');
    }
}

async function handleEditSeries(event, seriesId) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const seriesData = {
        series_name: formData.get('seriesName'),
        start_date: formData.get('startDate'),
        end_date: formData.get('endDate')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/series/${seriesId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(seriesData)
        });
        
        if (response.ok) {
            hideModal();
            loadSeries();
            showNotification('Series updated successfully!', 'success');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to update series'}`, 'error');
        }
    } catch (error) {
        console.error('Error updating series:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

async function editMatch(id) {
    try {
        // Fetch match data and teams
        const [matchResponse, teamsResponse, seriesResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/matches/${id}`),
            fetch(`${API_BASE_URL}/teams`),
            fetch(`${API_BASE_URL}/series`)
        ]);
        
        const match = await matchResponse.json();
        const teams = await teamsResponse.json();
        const series = await seriesResponse.json();
        
        if (matchResponse.ok) {
            // Build teams options
            let teamsOptions = '<option value="">Select a team</option>';
            teams.forEach(team => {
                teamsOptions += `<option value="${team.id}">${team.team_name}</option>`;
            });
            
            // Build series options
            let seriesOptions = '<option value="">Select a series</option>';
            series.forEach(s => {
                const selected = match.series_id === s.id ? 'selected' : '';
                seriesOptions += `<option value="${s.id}" ${selected}>${s.series_name}</option>`;
            });
            
            // Create edit form modal
            const formHtml = `
                <div class="modal" style="display: block;">
                    <div class="modal-content">
                        <span class="close" onclick="hideModal()">&times;</span>
                        <h2>Edit Match</h2>
                        <form id="editMatchForm" onsubmit="handleEditMatch(event, ${match.id})">
                            <div class="form-group">
                                <label for="editMatchSeries">Series:</label>
                                <select id="editMatchSeries" name="seriesId" required>
                                    ${seriesOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editMatchTeam1">Team 1:</label>
                                <select id="editMatchTeam1" name="team1Id" required>
                                    ${teamsOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editMatchTeam2">Team 2:</label>
                                <select id="editMatchTeam2" name="team2Id" required>
                                    ${teamsOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editMatchDate">Match Date:</label>
                                <input type="date" id="editMatchDate" name="matchDate" value="${match.match_date || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editMatchVenue">Venue:</label>
                                <input type="text" id="editMatchVenue" name="venue" value="${match.venue || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="editMatchWinner">Winner:</label>
                                <select id="editMatchWinner" name="winnerId">
                                    <option value="">No winner yet</option>
                                    ${teamsOptions}
                                </select>
                            </div>
                            <button type="submit" class="btn">Update Match</button>
                            <button type="button" class="btn btn-secondary" onclick="hideModal()">Cancel</button>
                        </form>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', formHtml);
            
            // Set selected values
            document.getElementById('editMatchTeam1').value = match.team1_id || '';
            document.getElementById('editMatchTeam2').value = match.team2_id || '';
            document.getElementById('editMatchWinner').value = match.winner_id || '';
        } else {
            showNotification('Error loading match data', 'error');
        }
    } catch (error) {
        console.error('Error loading match:', error);
        showNotification('Error loading match data', 'error');
    }
}

async function handleEditMatch(event, matchId) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const matchData = {
        series_id: parseInt(formData.get('seriesId')),
        team1_id: parseInt(formData.get('team1Id')),
        team2_id: parseInt(formData.get('team2Id')),
        match_date: formData.get('matchDate'),
        venue: formData.get('venue'),
        winner_id: formData.get('winnerId') ? parseInt(formData.get('winnerId')) : null
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/matches/${matchId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(matchData)
        });
        
        if (response.ok) {
            hideModal();
            loadMatches();
            showNotification('Match updated successfully!', 'success');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to update match'}`, 'error');
        }
    } catch (error) {
        console.error('Error updating match:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

async function editScorecard(id) {
    try {
        // Fetch scorecard data and related data
        const [scorecardResponse, playersResponse, matchesResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/scorecards/${id}`),
            fetch(`${API_BASE_URL}/players`),
            fetch(`${API_BASE_URL}/matches`)
        ]);
        
        const scorecard = await scorecardResponse.json();
        const players = await playersResponse.json();
        const matches = await matchesResponse.json();
        
        if (scorecardResponse.ok) {
            // Build players options
            let playersOptions = '<option value="">Select a player</option>';
            players.forEach(player => {
                const selected = scorecard.player_id === player.id ? 'selected' : '';
                playersOptions += `<option value="${player.id}" ${selected}>${player.name}</option>`;
            });
            
            // Build matches options
            let matchesOptions = '<option value="">Select a match</option>';
            matches.forEach(match => {
                const selected = scorecard.match_id === match.id ? 'selected' : '';
                matchesOptions += `<option value="${match.id}" ${selected}>Match ${match.id}</option>`;
            });
            
            // Create edit form modal
            const formHtml = `
                <div class="modal" style="display: block;">
                    <div class="modal-content">
                        <span class="close" onclick="hideModal()">&times;</span>
                        <h2>Edit Scorecard</h2>
                        <form id="editScorecardForm" onsubmit="handleEditScorecard(event, ${scorecard.id})">
                            <div class="form-group">
                                <label for="editScorecardPlayer">Player:</label>
                                <select id="editScorecardPlayer" name="playerId" required>
                                    ${playersOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editScorecardMatch">Match:</label>
                                <select id="editScorecardMatch" name="matchId" required>
                                    ${matchesOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editRunsScored">Runs Scored:</label>
                                <input type="number" id="editRunsScored" name="runsScored" value="${scorecard.runs_scored || 0}" required min="0">
                            </div>
                            <div class="form-group">
                                <label for="editBallsFaced">Balls Faced:</label>
                                <input type="number" id="editBallsFaced" name="ballsFaced" value="${scorecard.balls_faced || 0}" required min="0">
                            </div>
                            <div class="form-group">
                                <label for="editWicketsTaken">Wickets Taken:</label>
                                <input type="number" id="editWicketsTaken" name="wicketsTaken" value="${scorecard.wickets_taken || 0}" required min="0" max="10">
                            </div>
                            <button type="submit" class="btn">Update Scorecard</button>
                            <button type="button" class="btn btn-secondary" onclick="hideModal()">Cancel</button>
                        </form>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', formHtml);
        } else {
            showNotification('Error loading scorecard data', 'error');
        }
    } catch (error) {
        console.error('Error loading scorecard:', error);
        showNotification('Error loading scorecard data', 'error');
    }
}

async function handleEditScorecard(event, scorecardId) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const scorecardData = {
        player_id: parseInt(formData.get('playerId')),
        match_id: parseInt(formData.get('matchId')),
        runs_scored: parseInt(formData.get('runsScored')),
        balls_faced: parseInt(formData.get('ballsFaced')),
        wickets_taken: parseInt(formData.get('wicketsTaken'))
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/scorecards/${scorecardId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scorecardData)
        });
        
        if (response.ok) {
            hideModal();
            loadScorecards();
            showNotification('Scorecard updated successfully!', 'success');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to update scorecard'}`, 'error');
        }
    } catch (error) {
        console.error('Error updating scorecard:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}

// ============ DELETE FUNCTIONALITY ============
async function deleteTeam(id) {
    if (confirm('Are you sure you want to delete this team? This action cannot be undone.')) {
        try {
            const response = await fetch(`${API_BASE_URL}/teams/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showNotification('Team deleted successfully!', 'success');
                loadTeams(); // Reload the teams list
            } else {
                const errorData = await response.json();
                showNotification(`Error: ${errorData.error || 'Failed to delete team'}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting team:', error);
            showNotification(`Network error: ${error.message}`, 'error');
        }
    }
}

async function deletePlayer(id) {
    if (confirm('Are you sure you want to delete this player? This action cannot be undone.')) {
        try {
            const response = await fetch(`${API_BASE_URL}/players/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showNotification('Player deleted successfully!', 'success');
                loadPlayers(); // Reload the players list
            } else {
                const errorData = await response.json();
                showNotification(`Error: ${errorData.error || 'Failed to delete player'}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting player:', error);
            showNotification(`Network error: ${error.message}`, 'error');
        }
    }
}

async function deleteSeries(id) {
    if (confirm('Are you sure you want to delete this series? This action cannot be undone.')) {
        try {
            const response = await fetch(`${API_BASE_URL}/series/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showNotification('Series deleted successfully!', 'success');
                loadSeries(); // Reload the series list
            } else {
                const errorData = await response.json();
                showNotification(`Error: ${errorData.error || 'Failed to delete series'}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting series:', error);
            showNotification(`Network error: ${error.message}`, 'error');
        }
    }
}

async function deleteMatch(id) {
    if (confirm('Are you sure you want to delete this match? This action cannot be undone.')) {
        try {
            const response = await fetch(`${API_BASE_URL}/matches/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showNotification('Match deleted successfully!', 'success');
                loadMatches(); // Reload the matches list
            } else {
                const errorData = await response.json();
                showNotification(`Error: ${errorData.error || 'Failed to delete match'}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting match:', error);
            showNotification(`Network error: ${error.message}`, 'error');
        }
    }
}

async function deleteScorecard(id) {
    if (confirm('Are you sure you want to delete this scorecard? This action cannot be undone.')) {
        try {
            const response = await fetch(`${API_BASE_URL}/scorecards/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showNotification('Scorecard deleted successfully!', 'success');
                loadScorecards(); // Reload the scorecards list
            } else {
                const errorData = await response.json();
                showNotification(`Error: ${errorData.error || 'Failed to delete scorecard'}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting scorecard:', error);
            showNotification(`Network error: ${error.message}`, 'error');
        }
    }
}

function showAddScorecardForm() {
    const formHtml = `
        <div class="modal" style="display: block;">
            <div class="modal-content">
                <span class="close" onclick="hideModal()">&times;</span>
                <h2>Add New Scorecard</h2>
                <form id="addScorecardForm" onsubmit="handleAddScorecard(event)">
                    <div class="form-group">
                        <label for="playerId">Player ID:</label>
                        <input type="number" id="playerId" name="playerId" required>
                    </div>
                    <div class="form-group">
                        <label for="matchId">Match ID:</label>
                        <input type="number" id="matchId" name="matchId" required>
                    </div>
                    <div class="form-group">
                        <label for="runsScored">Runs Scored:</label>
                        <input type="number" id="runsScored" name="runsScored" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="ballsFaced">Balls Faced:</label>
                        <input type="number" id="ballsFaced" name="ballsFaced" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="wicketsTaken">Wickets Taken:</label>
                        <input type="number" id="wicketsTaken" name="wicketsTaken" min="0" required>
                    </div>
                    <button type="submit" class="btn">Add Scorecard</button>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

async function handleAddScorecard(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const scorecardData = {
        player_id: parseInt(formData.get('playerId')),
        match_id: parseInt(formData.get('matchId')),
        runs_scored: parseInt(formData.get('runsScored')),
        balls_faced: parseInt(formData.get('ballsFaced')),
        wickets_taken: parseInt(formData.get('wicketsTaken'))
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/scorecards`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scorecardData)
        });
        
        if (response.ok) {
            hideModal();
            loadScorecards();
            showNotification('Scorecard added successfully!');
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error || 'Failed to add scorecard'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding scorecard:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    }
}



