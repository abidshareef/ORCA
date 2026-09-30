-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Locations table
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    geom GEOMETRY(PointZ, 4326), -- Point with Depth (Z)
    depth FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ecosystem observations table
CREATE TABLE ecosystem_observations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    temperature FLOAT,
    salinity FLOAT,
    dissolved_oxygen FLOAT,
    ph FLOAT,
    chlorophyll FLOAT,
    turbidity FLOAT,
    pollution FLOAT,
    biodiversity FLOAT,
    fisheries FLOAT,
    current FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agents table
CREATE TABLE agents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE
);

-- Agent runs table
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(50) REFERENCES agents(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    input_data JSONB,
    status VARCHAR(50) -- ANALYZING, COMPLETE, ERROR
);

-- Agent findings table
CREATE TABLE agent_findings (
    id SERIAL PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    finding TEXT,
    prediction FLOAT,
    confidence FLOAT,
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Evidence table
CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    finding_id INTEGER REFERENCES agent_findings(id),
    source VARCHAR(255),
    evidence_type VARCHAR(50), -- SENSOR, DOCUMENT, HISTORICAL
    content TEXT,
    relevance FLOAT,
    confidence FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE,
    location_id INTEGER REFERENCES locations(id)
);

-- Risk assessments table
CREATE TABLE risk_assessments (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    risk_score FLOAT,
    risk_level VARCHAR(20), -- LOW, MODERATE, HIGH, CRITICAL
    confidence FLOAT,
    ecosystem_health_index FLOAT,
    explanation TEXT,
    recommendation TEXT
);

-- Anomalies table
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    parameter VARCHAR(50),
    value FLOAT,
    z_score FLOAT,
    severity VARCHAR(20), -- NORMAL, WATCH, ANOMALY
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    risk_assessment_id INTEGER REFERENCES risk_assessments(id),
    severity VARCHAR(20),
    event_description TEXT,
    status VARCHAR(20), -- ACTIVE, ACKNOWLEDGED, DISMISSED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Knowledge base (RAG)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    source_url TEXT,
    embedding vector(1536), -- Assuming OpenAI embeddings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge graph entities
CREATE TABLE knowledge_entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    type VARCHAR(50), -- Species, Habitat, Parameter, etc.
    description TEXT
);

-- Knowledge graph relationships
CREATE TABLE knowledge_relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_entities(id),
    target_id INTEGER REFERENCES knowledge_entities(id),
    relation_type VARCHAR(50), -- CAUSES, AFFECTS, DEPENDS_ON, etc.
    weight FLOAT DEFAULT 1.0
);

-- Indexes for performance
CREATE INDEX idx_observations_timestamp ON ecosystem_observations(timestamp);
CREATE INDEX idx_observations_location ON ecosystem_observations(location_id);
CREATE INDEX idx_risk_timestamp ON risk_assessments(timestamp);
CREATE INDEX idx_locations_geom ON locations USING GIST(geom);
