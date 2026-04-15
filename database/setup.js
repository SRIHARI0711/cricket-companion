const mysql = require('mysql2');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const connection = mysql.createConnection({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'username',
  password: process.env.DB_PASSWORD || 'password',
  database: process.env.DB_NAME || 'cricket_companion',
  multipleStatements: true
});

async function setupDatabase() {
  try {
    console.log('Connecting to MySQL...');
    
    // Test connection
    await new Promise((resolve, reject) => {
      connection.connect((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
    
    console.log('Connected to MySQL successfully!');
    
    // Read and execute create tables script
    console.log('Creating tables...');
    const createTablesSQL = fs.readFileSync(path.join(__dirname, 'create_tables.sql'), 'utf8');
    
    await new Promise((resolve, reject) => {
      connection.query(createTablesSQL, (err, results) => {
        if (err) reject(err);
        else resolve(results);
      });
    });
    
    console.log('Tables created successfully!');
    
    // Read and execute insert data script
    console.log('Inserting sample data...');
    const insertDataSQL = fs.readFileSync(path.join(__dirname, 'insert_data.sql'), 'utf8');
    
    await new Promise((resolve, reject) => {
      connection.query(insertDataSQL, (err, results) => {
        if (err) reject(err);
        else resolve(results);
      });
    });
    
    console.log('Sample data inserted successfully!');
    
    // Verify tables
    console.log('Verifying database setup...');
    const tables = await new Promise((resolve, reject) => {
      connection.query('SHOW TABLES', (err, results) => {
        if (err) reject(err);
        else resolve(results);
      });
    });
    
    console.log('Tables in database:');
    tables.forEach(table => {
      console.log(`- ${Object.values(table)[0]}`);
    });
    
    // Test data
    const teamCount = await new Promise((resolve, reject) => {
      connection.query('SELECT COUNT(*) as count FROM teams', (err, results) => {
        if (err) reject(err);
        else resolve(results[0].count);
      });
    });
    
    const playerCount = await new Promise((resolve, reject) => {
      connection.query('SELECT COUNT(*) as count FROM players', (err, results) => {
        if (err) reject(err);
        else resolve(results[0].count);
      });
    });
    
    console.log(`\nData verification:`);
    console.log(`- Teams: ${teamCount}`);
    console.log(`- Players: ${playerCount}`);
    
    console.log('\n✅ Database setup completed successfully!');
    
  } catch (error) {
    console.error('❌ Database setup failed:', error.message);
    process.exit(1);
  } finally {
    connection.end();
  }
}

// Run setup
setupDatabase();
