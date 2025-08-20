-- Enable useful extensions (safe to run if already present)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- JSONB works without an extension; GIN opclasses are built-in.

-- =========================
-- Core job (1 row per JOA)
-- =========================
CREATE TABLE IF NOT EXISTS job (
  job_id                BIGSERIAL PRIMARY KEY,

  -- Natural/business keys from USAJOBS
  position_id           TEXT NOT NULL,         -- e.g., "SW62210-05-1716..."
  matched_object_id     TEXT,                  -- often numeric string; not always stable across searches
  position_uri          TEXT NOT NULL,         -- canonical USAJOBS URL

  position_title        TEXT NOT NULL,
  organization_name     TEXT,
  department_name       TEXT,

  apply_uri             TEXT[] NOT NULL DEFAULT '{}',   -- preserve multiple apply links
  position_location_display TEXT,                        -- "Multiple Locations" etc.

  -- Pay summary (keep as integers in cents or whole dollars; here: whole dollars)
  pay_min               INTEGER,
  pay_max               INTEGER,
  pay_rate_interval_code TEXT,                            -- e.g., "PA", "PH"

  qualification_summary TEXT,

  publication_start_date TIMESTAMPTZ,
  application_close_date TIMESTAMPTZ,
  position_start_date    TIMESTAMPTZ,
  position_end_date      TIMESTAMPTZ,

  remote_indicator      BOOLEAN,
  telework_eligible     BOOLEAN,

  -- Lineage / durability
  source_event_time     TIMESTAMPTZ,
  ingest_run_id         TEXT,
  raw_json              JSONB NOT NULL,                  -- full descriptor for “reach-back”

  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Natural key we upsert on
  CONSTRAINT uk_job_position_id UNIQUE (position_id)
);

-- Helpful indexes for common access patterns
CREATE INDEX IF NOT EXISTS idx_job_pubstart ON job (publication_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_job_title_trgm ON job USING gin (position_title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_job_raw_json_gin ON job USING gin (raw_json);

-- ==================================
-- Details (1:1 with job, wide text)
-- ==================================
CREATE TABLE IF NOT EXISTS job_details (
  job_id                   BIGINT PRIMARY KEY REFERENCES job(job_id) ON DELETE CASCADE,
  job_summary              TEXT,
  low_grade                TEXT,
  high_grade               TEXT,
  promotion_potential      TEXT,
  organization_codes       TEXT,
  relocation               TEXT,
  hiring_path              TEXT[],      -- keep as array; can GIN-index later if needed
  mco_tags                 TEXT[],
  total_openings           TEXT,
  agency_marketing_statement TEXT,
  travel_code              TEXT,
  apply_online_url         TEXT,
  detail_status_url        TEXT,
  major_duties             TEXT,
  education                TEXT,
  requirements             TEXT,
  evaluations              TEXT,
  how_to_apply             TEXT,
  what_to_expect_next      TEXT,
  required_documents       TEXT,
  benefits                 TEXT,
  benefits_url             TEXT,
  benefits_display_default_text BOOLEAN,
  other_information        TEXT,
  key_requirements         TEXT[],
  within_area              TEXT,
  commute_distance         TEXT,
  service_type             TEXT,
  announcement_closing_type TEXT,
  agency_contact_email     TEXT,
  security_clearance       TEXT,
  drug_test_required       BOOLEAN,
  position_sensitivity     TEXT,
  adjudication_type        TEXT[],
  financial_disclosure     BOOLEAN,
  bargaining_unit_status   BOOLEAN,

  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==================================
-- Locations (N:1)
-- ==================================
CREATE TABLE IF NOT EXISTS job_location (
  job_id                    BIGINT NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
  loc_idx                   SMALLINT NOT NULL,   -- stable ordering from payload
  location_name             TEXT,
  country_code              TEXT,
  country_sub_division_code TEXT,
  city_name                 TEXT,
  latitude                  NUMERIC(9,6),
  longitude                 NUMERIC(9,6),

  PRIMARY KEY (job_id, loc_idx)
);

CREATE INDEX IF NOT EXISTS idx_job_location_city ON job_location (city_name);
-- If you later add PostGIS, you can store a geography point and index with GiST.

-- ==================================
-- Categories (N:1)
-- ==================================
CREATE TABLE IF NOT EXISTS job_category (
  job_id   BIGINT NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
  code     TEXT   NOT NULL,   -- e.g., "2210"
  name     TEXT,              -- e.g., "Information Technology Management"
  PRIMARY KEY (job_id, code)
);

-- ==================================
-- Grades (N:1)
-- ==================================
CREATE TABLE IF NOT EXISTS job_grade (
  job_id   BIGINT NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
  code     TEXT   NOT NULL,   -- e.g., "GS-13"
  PRIMARY KEY (job_id, code)
);

-- Optional: a generated column for future full-text search (title + summary)
-- Uncomment to enable; add a GIN index on it.
-- ALTER TABLE job
--   ADD COLUMN search_tsv tsvector
--     GENERATED ALWAYS AS (to_tsvector('english',
--       coalesce(position_title,'') || ' ' || coalesce(qualification_summary,''))) STORED;
-- CREATE INDEX IF NOT EXISTS idx_job_search_tsv ON job USING gin (search_tsv);

-- Lightweight updated_at maintenance (if you don’t want triggers)
-- Your upserts should set updated_at = NOW() on conflict.
