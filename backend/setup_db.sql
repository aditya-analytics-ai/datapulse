-- Run this in MySQL Workbench to set up DataPulse database
-- Only needed if tables are not auto-created by the server

CREATE DATABASE IF NOT EXISTS datapulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE datapulse;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) NULL,
    avatar VARCHAR(500) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scrape_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url TEXT NOT NULL,
    page_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    row_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS scraped_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    data JSON,
    cleaned BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES scrape_jobs(id) ON DELETE CASCADE
);

SELECT 'DataPulse database setup complete!' AS status;
