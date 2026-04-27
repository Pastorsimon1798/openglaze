-- OpenGlaze Unified Database Schema
-- Works for both personal (SQLite) and cloud (PostgreSQL) modes
-- user_id is NULLABLE: NULL in personal mode, populated in cloud mode

-- Users table (synced with Kratos, used in cloud/demo mode)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,  -- Kratos identity ID
    email TEXT UNIQUE NOT NULL,
    studio_name TEXT,
    tier TEXT DEFAULT 'free' CHECK(tier IN ('free', 'pro', 'studio', 'education')),
    template_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Glazes: All studio glazes
CREATE TABLE IF NOT EXISTS glazes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    family TEXT,
    color TEXT,
    -- Extended columns for Glaze Lab features
    hex TEXT,                    -- Color swatch hex code
    chemistry TEXT,              -- Chemical composition description
    behavior TEXT,               -- How it behaves in firing
    layering TEXT,               -- Layering recommendations
    warning TEXT,                -- Known issues (e.g., Shino crawl)
    recipe TEXT,                 -- Recipe ingredients (JSON array)
    catalog_code TEXT,           -- Commercial catalog reference
    food_safe BOOLEAN DEFAULT NULL,  -- true=known food safe, false=not food safe, null=unknown
    notes TEXT,
    -- Cone / atmosphere / gamification columns
    cone TEXT,
    atmosphere TEXT CHECK(atmosphere IN ('oxidation', 'reduction', 'neutral', 'salt', 'wood')),
    base_type TEXT CHECK(base_type IN ('transparent', 'opaque', 'matte', 'satin', 'gloss', 'semi-opaque')),
    surface TEXT CHECK(surface IN ('smooth', 'textured', 'crystalline', 'runny')),
    transparency TEXT CHECK(transparency IN ('transparent', 'semi-opaque', 'opaque')),
    image_url TEXT,
    user_id TEXT,                -- NULL in personal mode, tenant ID in cloud
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingredients table (for recipe building)
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT CHECK(category IN ('flux', 'stabilizer', 'glassformer', 'colorant', 'opacifier', 'additive')),
    chemical_formula TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Combinations: Research-backed, user-predicted, confirmed, and surprise layering combos
CREATE TABLE IF NOT EXISTS combinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,                -- NULL in personal mode, tenant ID in cloud
    base TEXT NOT NULL,          -- Base glaze (applied first)
    top TEXT NOT NULL,           -- Top glaze (applied last)
    layers TEXT,                 -- JSON array, bottom to top: ["Tenmoku", "Celadon", "Chun Blue"]
    type TEXT NOT NULL CHECK(type IN ('research-backed', 'user-prediction', 'confirmed', 'surprise')),
    source TEXT,                 -- Where this combo came from: 'fired', 'community', 'manufacturer', 'chemistry_prediction'
    result TEXT,                 -- Visual result description
    chemistry TEXT,              -- Chemical explanation
    risk TEXT CHECK(risk IN ('low', 'medium', 'high')),
    effect TEXT CHECK(effect IN ('subtle', 'dramatic')),
    stage TEXT DEFAULT 'idea',   -- Pipeline stage: idea, predicting, testing, fired, documented
    prediction_grade TEXT DEFAULT 'unknown'
        CHECK(prediction_grade IN ('likely', 'possible', 'unlikely', 'unknown', 'confirmed', 'surprise')),
    notes TEXT,
    -- Gamification columns
    result_rating INTEGER CHECK(result_rating BETWEEN 1 AND 5),
    is_surprise BOOLEAN DEFAULT 0,
    surprise_rarity TEXT CHECK(surprise_rarity IN ('common', 'uncommon', 'rare', 'legendary')),
    discovered_by TEXT,
    replication_count INTEGER DEFAULT 0,
    photo_url TEXT,
    status TEXT DEFAULT 'untested' CHECK(status IN ('untested', 'predicted', 'in_kiln', 'tested', 'proven', 'failed', 'surprise')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chemistry Rules: Authoritative glaze chemistry knowledge
CREATE TABLE IF NOT EXISTS chemistry_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    conditions TEXT,
    outcomes TEXT,
    caveats TEXT,
    confidence TEXT DEFAULT 'high' CHECK(confidence IN ('high', 'medium', 'low')),
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chemistry_rules_category ON chemistry_rules(category);

-- Experiments: 6-stage experiment pipeline tracking
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    combination_id INTEGER,
    base_glaze TEXT NOT NULL,
    top_glaze TEXT NOT NULL,
    stage TEXT DEFAULT 'ideation' CHECK(stage IN ('ideation', 'prediction', 'application', 'firing', 'analysis', 'documentation')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'failed')),
    prediction TEXT,
    result TEXT,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    notes TEXT,
    photo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Inbox: Captured glaze ideas
CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    base TEXT NOT NULL,
    top TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Archive: Completed experiments (successful and failed)
CREATE TABLE IF NOT EXISTS archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    name TEXT NOT NULL,
    base_glaze TEXT NOT NULL,
    top_glaze TEXT NOT NULL,
    result TEXT,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    notes TEXT,
    photo TEXT,
    type TEXT NOT NULL CHECK(type IN ('successful', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Progress: Pipeline state tracking
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    user_id TEXT,
    stage TEXT DEFAULT 'ideation',
    status TEXT DEFAULT 'ready',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Templates: Shared glaze collections (cloud feature)
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    glazes_yaml TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Studios: Collaborative groups for sharing kiln testing
CREATE TABLE IF NOT EXISTS studios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    invite_code TEXT UNIQUE NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS studio_members (
    studio_id TEXT NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT DEFAULT 'member' CHECK(role IN ('admin', 'member')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (studio_id, user_id)
);

CREATE TABLE IF NOT EXISTS lab_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    studio_id TEXT NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    combination_id INTEGER NOT NULL,
    assigned_to TEXT,
    claimed_at TIMESTAMP,
    status TEXT DEFAULT 'claimed' CHECK(status IN ('claimed', 'in_progress', 'completed', 'released')),
    claimed_by_name TEXT
);

-- ==========================================================================
-- GAMIFICATION TABLES (from Source B)
-- ==========================================================================

-- User Stats: Points, streaks, badges tracking
CREATE TABLE IF NOT EXISTS user_stats (
    user_id TEXT PRIMARY KEY,
    points INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    streak_freeze_remaining INTEGER DEFAULT 2,
    last_activity_date TEXT,
    combinations_tested INTEGER DEFAULT 0,
    combinations_proven INTEGER DEFAULT 0,
    surprises_found INTEGER DEFAULT 0,
    predictions_correct INTEGER DEFAULT 0,
    predictions_total INTEGER DEFAULT 0,
    discoveries_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Badges: Earned achievements
CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    badge_type TEXT NOT NULL,
    badge_name TEXT NOT NULL,
    badge_icon TEXT,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, badge_type)
);

-- Activity Log: For streaks and engagement tracking
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    activity_type TEXT NOT NULL CHECK(activity_type IN (
        'combination_tested', 'prediction_made', 'prediction_resolved',
        'discovery_made', 'photo_uploaded', 'glaze_created', 'streak_maintained'
    )),
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================================
-- PREDICTIONS (human vs AI prediction market)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    combination_id INTEGER NOT NULL,
    predicted_outcome TEXT,
    confidence INTEGER CHECK(confidence BETWEEN 0 AND 100),
    is_ai BOOLEAN DEFAULT 0,
    ai_confidence INTEGER,
    ai_prediction TEXT,
    resolved BOOLEAN DEFAULT 0,
    user_correct BOOLEAN,
    points_earned INTEGER DEFAULT 0,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================================
-- FIRINGS (kiln logs)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS firings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    kiln_name TEXT,
    cone_target TEXT,
    atmosphere TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS firing_glazes (
    firing_id INTEGER NOT NULL,
    glaze_id INTEGER NOT NULL,
    position TEXT,
    notes TEXT,
    result_image_url TEXT,
    PRIMARY KEY (firing_id, glaze_id)
);

-- ==========================================================================
-- INDEXES
-- ==========================================================================

CREATE INDEX IF NOT EXISTS idx_glazes_family ON glazes(family);
CREATE INDEX IF NOT EXISTS idx_glazes_user ON glazes(user_id);
CREATE INDEX IF NOT EXISTS idx_glazes_cone ON glazes(cone);
CREATE INDEX IF NOT EXISTS idx_combinations_type ON combinations(type);
CREATE INDEX IF NOT EXISTS idx_combinations_user ON combinations(user_id);
CREATE INDEX IF NOT EXISTS idx_combinations_status ON combinations(status);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_user ON experiments(user_id);
CREATE INDEX IF NOT EXISTS idx_archive_type ON archive(type);
CREATE INDEX IF NOT EXISTS idx_archive_user ON archive(user_id);
CREATE INDEX IF NOT EXISTS idx_studios_invite ON studios(invite_code);
CREATE INDEX IF NOT EXISTS idx_studio_members_user ON studio_members(user_id);
CREATE INDEX IF NOT EXISTS idx_lab_assignments_studio ON lab_assignments(studio_id);
CREATE INDEX IF NOT EXISTS idx_lab_assignments_combo ON lab_assignments(combination_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_combination_id ON predictions(combination_id);
CREATE INDEX IF NOT EXISTS idx_predictions_resolved ON predictions(resolved);
CREATE INDEX IF NOT EXISTS idx_badges_user_id ON badges(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_user_id ON activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_date ON activity_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_firings_user_id ON firings(user_id);

-- Insert initial progress record (for personal mode)
INSERT OR IGNORE INTO progress (id, stage, status, user_id) VALUES (1, 'ideation', 'ready', NULL);

-- Insert default ingredients
INSERT OR IGNORE INTO ingredients (name, category) VALUES
    ('Feldspar', 'flux'),
    ('Whiting', 'flux'),
    ('Dolomite', 'flux'),
    ('Talc', 'flux'),
    ('Zinc Oxide', 'flux'),
    ('Silica', 'glassformer'),
    ('Frit 3124', 'glassformer'),
    ('Frit 3134', 'glassformer'),
    ('Kaolin', 'stabilizer'),
    ('Ball Clay', 'stabilizer'),
    ('Bentonite', 'additive'),
    ('Cobalt Carbonate', 'colorant'),
    ('Copper Carbonate', 'colorant'),
    ('Iron Oxide', 'colorant'),
    ('Rutile', 'colorant'),
    ('Tin Oxide', 'opacifier'),
    ('Zircopax', 'opacifier');
