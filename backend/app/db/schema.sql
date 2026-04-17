-- ============================================================
-- AI-Powered HCP Interaction Logger — PostgreSQL Schema
-- ============================================================
-- Database: crm_db
-- Description: Schema for pharma field reps to log interactions
--              with Healthcare Professionals (HCPs).
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. HCPs — Healthcare Professional profiles
-- ============================================================
CREATE TABLE hcps (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    specialty       VARCHAR(150) NOT NULL,
    location        VARCHAR(255),
    hospital        VARCHAR(255),
    email           VARCHAR(255),
    phone           VARCHAR(50),
    notes           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hcps_name ON hcps (name);
CREATE INDEX idx_hcps_specialty ON hcps (specialty);
CREATE INDEX idx_hcps_location ON hcps (location);

-- ============================================================
-- 2. Interactions — Logged meetings / calls with HCPs
-- ============================================================
CREATE TABLE interactions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hcp_id              UUID NOT NULL REFERENCES hcps(id) ON DELETE CASCADE,
    interaction_type    VARCHAR(50) NOT NULL CHECK (interaction_type IN (
                            'in-person', 'virtual', 'phone', 'email', 'conference'
                        )),
    date                DATE NOT NULL,
    time                TIME,
    attendees           TEXT,
    topics_discussed    TEXT,
    outcomes            TEXT,
    follow_up_actions   TEXT,
    sentiment           VARCHAR(20) CHECK (sentiment IN (
                            'positive', 'neutral', 'negative'
                        )),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_interactions_hcp_id ON interactions (hcp_id);
CREATE INDEX idx_interactions_date ON interactions (date DESC);
CREATE INDEX idx_interactions_type ON interactions (interaction_type);
CREATE INDEX idx_interactions_sentiment ON interactions (sentiment);

-- ============================================================
-- 3. Materials Shared — Collateral shared during interactions
-- ============================================================
CREATE TABLE materials_shared (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id    UUID NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
    material_name     VARCHAR(255) NOT NULL,
    material_type     VARCHAR(100) NOT NULL CHECK (material_type IN (
                          'brochure', 'clinical_study', 'presentation',
                          'product_info', 'sample_card', 'other'
                      )),
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_materials_interaction_id ON materials_shared (interaction_id);

-- ============================================================
-- 4. Samples Distributed — Drug samples given to HCPs
-- ============================================================
CREATE TABLE samples_distributed (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id    UUID NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
    sample_name       VARCHAR(255) NOT NULL,
    quantity          INTEGER NOT NULL CHECK (quantity > 0),
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_samples_interaction_id ON samples_distributed (interaction_id);

-- ============================================================
-- 5. Follow-Up Suggestions — AI-generated or manual suggestions
-- ============================================================
CREATE TABLE follow_up_suggestions (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id    UUID NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
    suggestion_text   TEXT NOT NULL,
    generated_by_ai   BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_follow_ups_interaction_id ON follow_up_suggestions (interaction_id);
CREATE INDEX idx_follow_ups_ai ON follow_up_suggestions (generated_by_ai);

-- ============================================================
-- Auto-update trigger for updated_at columns
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_hcps_updated_at
    BEFORE UPDATE ON hcps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_interactions_updated_at
    BEFORE UPDATE ON interactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
