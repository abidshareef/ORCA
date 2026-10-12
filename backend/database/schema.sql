-- ORCA PostgreSQL/PostGIS schema.
-- Demo analysis defaults to checked-in JSON and does not require this database.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    geom GEOMETRY(PointZ, 4326) NOT NULL,
    depth DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecosystem_observations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temperature DOUBLE PRECISION,
    salinity DOUBLE PRECISION,
    dissolved_oxygen DOUBLE PRECISION,
    ph DOUBLE PRECISION,
    chlorophyll DOUBLE PRECISION,
    turbidity DOUBLE PRECISION,
    pollution DOUBLE PRECISION,
    biodiversity DOUBLE PRECISION,
    fisheries DOUBLE PRECISION,
    current DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(50) REFERENCES agents(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    input_data JSONB,
    status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS agent_findings (
    id SERIAL PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    finding TEXT,
    prediction DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    reasoning TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    finding_id INTEGER REFERENCES agent_findings(id),
    source VARCHAR(255),
    evidence_type VARCHAR(50),
    content TEXT,
    relevance DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    timestamp TIMESTAMPTZ,
    location_id INTEGER REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    risk_score DOUBLE PRECISION,
    risk_level VARCHAR(20),
    confidence DOUBLE PRECISION,
    ecosystem_health_index DOUBLE PRECISION,
    explanation TEXT,
    recommendation TEXT
);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    parameter VARCHAR(50),
    value DOUBLE PRECISION,
    z_score DOUBLE PRECISION,
    severity VARCHAR(20),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    risk_assessment_id INTEGER REFERENCES risk_assessments(id),
    severity VARCHAR(20),
    event_description TEXT,
    status VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ
);

-- JSONB keeps the schema compatible with the repository's PostGIS image.
-- Replace with pgvector only when a pgvector-enabled database is configured.
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    source_url TEXT,
    embedding JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    type VARCHAR(50),
    description TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_entities(id),
    target_id INTEGER REFERENCES knowledge_entities(id),
    relation_type VARCHAR(50),
    weight DOUBLE PRECISION DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_observations_timestamp
    ON ecosystem_observations(timestamp);
CREATE INDEX IF NOT EXISTS idx_observations_location
    ON ecosystem_observations(location_id);
CREATE INDEX IF NOT EXISTS idx_risk_timestamp
    ON risk_assessments(timestamp);
CREATE INDEX IF NOT EXISTS idx_locations_geom
    ON locations USING GIST(geom);
