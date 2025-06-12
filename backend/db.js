const mysql = require('mysql2');
require('dotenv').config();

const connection = mysql.createConnection({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || 'Hari@2005',
  database: process.env.DB_NAME || 'cricket_companion',
  multipleStatements: true
});

connection.connect(err => {
  if (err) {
    console.error('Database connection error:', err);
    process.exit(1);
  } else {
    console.log('Connected to MySQL database: cricket_companion');
  }
});

// Test the connection
connection.query('SELECT 1 as test', (err, results) => {
  if (err) {
    console.error('Database test query error:', err);
  } else {
    console.log('Database connection test successful');
  }
});

module.exports = connection;
