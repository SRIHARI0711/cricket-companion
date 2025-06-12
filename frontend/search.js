// Search functionality for all sections

// Global data arrays for filtering
let allTeams = [];
let allPlayers = [];
let allSeries = [];
let allMatches = [];
let allScorecards = [];

// Teams search setup
function setupTeamSearch() {
    const searchInput = document.getElementById('teamSearch');
    if (searchInput) {
        // Clear any existing event listeners
        const newSearchInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newSearchInput, searchInput);
        
        // Add new event listener
        newSearchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            
            if (searchTerm === '') {
                displayTeams(allTeams); // Show all teams when search is empty
                return;
            }
            
            // Filter teams based on search term
            const filteredTeams = allTeams.filter(team => {
                return (
                    team.team_name.toLowerCase().includes(searchTerm) ||
                    team.coach.toLowerCase().includes(searchTerm) ||
                    team.captain.toLowerCase().includes(searchTerm)
                );
            });
            
            displayTeams(filteredTeams);
        });
    }
}

// Players search setup
function setupPlayerSearch() {
    const searchInput = document.getElementById('playerSearch');
    if (searchInput) {
        // Clear any existing event listeners
        const newSearchInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newSearchInput, searchInput);
        
        // Add new event listener
        newSearchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            
            if (searchTerm === '') {
                displayPlayers(allPlayers); // Show all players when search is empty
                return;
            }
            
            // Filter players based on search term
            const filteredPlayers = allPlayers.filter(player => {
                return (
                    player.name.toLowerCase().includes(searchTerm) ||
                    player.team.toLowerCase().includes(searchTerm) ||
                    player.role.toLowerCase().includes(searchTerm)
                );
            });
            
            displayPlayers(filteredPlayers);
        });
    }
}

// Series search setup
function setupSeriesSearch() {
    const searchInput = document.getElementById('seriesSearch');
    if (searchInput) {
        // Clear any existing event listeners
        const newSearchInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newSearchInput, searchInput);
        
        // Add new event listener
        newSearchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            
            if (searchTerm === '') {
                displaySeries(allSeries); // Show all series when search is empty
                return;
            }
            
            // Filter series based on search term
            const filteredSeries = allSeries.filter(series => {
                return (
                    (series.series_name && series.series_name.toLowerCase().includes(searchTerm)) ||
                    (series.status && series.status.toLowerCase().includes(searchTerm)) ||
                    (series.start_date && new Date(series.start_date).toLocaleDateString().includes(searchTerm)) ||
                    (series.end_date && new Date(series.end_date).toLocaleDateString().includes(searchTerm))
                );
            });
            
            displaySeries(filteredSeries);
        });
    }
}

// Matches search setup
function setupMatchSearch() {
    const searchInput = document.getElementById('matchSearch');
    if (searchInput) {
        // Clear any existing event listeners
        const newSearchInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newSearchInput, searchInput);
        
        // Add new event listener
        newSearchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            
            if (searchTerm === '') {
                displayMatches(allMatches); // Show all matches when search is empty
                return;
            }
            
            // Filter matches based on search term
            const filteredMatches = allMatches.filter(match => {
                return (
                    (match.team1_name && match.team1_name.toLowerCase().includes(searchTerm)) ||
                    (match.team2_name && match.team2_name.toLowerCase().includes(searchTerm)) ||
                    (match.series_name && match.series_name.toLowerCase().includes(searchTerm)) ||
                    (match.venue && match.venue.toLowerCase().includes(searchTerm)) ||
                    (match.match_date && new Date(match.match_date).toLocaleDateString().includes(searchTerm))
                );
            });
            
            displayMatches(filteredMatches);
        });
    }
}

// Scorecards search setup
function setupScorecardSearch() {
    const searchInput = document.getElementById('scorecardSearch');
    if (searchInput) {
        // Clear any existing event listeners
        const newSearchInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newSearchInput, searchInput);
        
        // Add new event listener
        newSearchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            
            if (searchTerm === '') {
                displayScorecards(allScorecards); // Show all scorecards when search is empty
                return;
            }
            
            // Filter scorecards based on search term - search across ALL fields
            const filteredScorecards = allScorecards.filter(scorecard => {
                // Create a string with all searchable properties to perform a global search
                const searchableText = [
                    scorecard.player_name || '',
                    scorecard.match_id ? `Match ${scorecard.match_id}` : '',
                    scorecard.runs_scored ? scorecard.runs_scored.toString() : '',
                    scorecard.balls_faced ? scorecard.balls_faced.toString() : '',
                    scorecard.wickets_taken ? scorecard.wickets_taken.toString() : '',
                    scorecard.team_name || '',
                    scorecard.match_date ? new Date(scorecard.match_date).toLocaleDateString() : '',
                    scorecard.venue || '',
                    scorecard.series_name || '',
                    scorecard.innings || '',
                    scorecard.batting_position ? scorecard.batting_position.toString() : '',
                    scorecard.bowling_figures || '',
                    scorecard.economy_rate ? scorecard.economy_rate.toString() : '',
                    scorecard.status || ''
                ].join(' ').toLowerCase();
                
                return searchableText.includes(searchTerm);
            });
            
            displayScorecards(filteredScorecards);
        });
    }
}

// Modified load functions to store data and setup search
function loadTeamsWithSearch(teams) {
    allTeams = teams;
    displayTeams(teams);
    setupTeamSearch();
}

function loadPlayersWithSearch(players) {
    allPlayers = players;
    displayPlayers(players);
    setupPlayerSearch();
}

function loadSeriesWithSearch(series) {
    allSeries = series;
    displaySeries(series);
    setupSeriesSearch();
}

function loadMatchesWithSearch(matches) {
    allMatches = matches;
    displayMatches(matches);
    setupMatchSearch();
}

function loadScorecardsWithSearch(scorecards) {
    allScorecards = scorecards;
    displayScorecards(scorecards);
    setupScorecardSearch();
}