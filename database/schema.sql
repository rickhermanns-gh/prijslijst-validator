-- Prijslijst Validator Database Schema

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(100) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Upload sessions
CREATE TABLE upload_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  supplier VARCHAR(100) NOT NULL,  -- "ZR", "Eijffinger", "Artex", etc.
  file_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(512),
  status VARCHAR(50) DEFAULT 'pending',  -- pending, scan1_done, scan2_done, validation_done, exported

  -- Scan 1 results
  scan1_result JSONB,  -- {total: 836, with_specs: 717, complete: 566, ...}
  scan1_started_at TIMESTAMPTZ,
  scan1_completed_at TIMESTAMPTZ,

  -- Scan 2 results
  scan2_result JSONB,  -- {additional_items: 45, updated_count: ...}
  scan2_started_at TIMESTAMPTZ,
  scan2_completed_at TIMESTAMPTZ,

  -- Validation & Export
  validation_completed_at TIMESTAMPTZ,
  csv_export_path VARCHAR(512),
  csv_export_url VARCHAR(512),

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_upload_sessions_user_id ON upload_sessions(user_id);
CREATE INDEX idx_upload_sessions_status ON upload_sessions(status);

-- Validation items (ontbrekende specs)
CREATE TABLE validation_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES upload_sessions(id) ON DELETE CASCADE,

  item_number VARCHAR(20) NOT NULL,
  item_name VARCHAR(255),
  supplier VARCHAR(100),

  -- What's missing
  missing_fields VARCHAR[] DEFAULT '{}',  -- ["breedte", "rapport", "samenstelling"]

  -- User input (page reference)
  page_number INT,
  column_reference VARCHAR(100),  -- "column 2", "right side", etc.
  cell_reference VARCHAR(255),    -- user description of where they found it
  user_notes TEXT,

  -- Status
  validated BOOLEAN DEFAULT FALSE,
  validated_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_validation_items_session_id ON validation_items(session_id);
CREATE INDEX idx_validation_items_validated ON validation_items(validated);

-- Audit log
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action VARCHAR(100) NOT NULL,  -- "login", "upload", "scan1_start", "scan2_start", "validate_item", "export"
  session_id UUID REFERENCES upload_sessions(id) ON DELETE SET NULL,
  resource_type VARCHAR(50),     -- "upload_session", "validation_item"
  resource_id VARCHAR(255),
  metadata JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_session_id ON audit_log(session_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- Health check table (voor Railway)
CREATE TABLE health_check (
  id SERIAL PRIMARY KEY,
  checked_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO health_check (checked_at) VALUES (NOW());
