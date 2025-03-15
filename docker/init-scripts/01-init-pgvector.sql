-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create tables as needed
-- Note: Actual table creation is handled by the Python clients