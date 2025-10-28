-- VoiceAI Call Analysis Database Schema
-- Designed for storing call metrics for 30+ managers with inbound/outbound call analysis

-- ============================================================================
-- MANAGERS TABLE
-- ============================================================================
CREATE TABLE managers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255),
    department VARCHAR(100),
    hire_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CALL RECORDS TABLE
-- ============================================================================
CREATE TABLE call_records (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(255) NOT NULL UNIQUE, -- Google Drive file ID
    file_name VARCHAR(500) NOT NULL,
    manager_id INTEGER NOT NULL REFERENCES managers(id),
    call_type VARCHAR(20) NOT NULL CHECK (call_type IN ('Входящий', 'Исходящий')),
    call_date TIMESTAMP,
    file_size BIGINT,
    mime_type VARCHAR(100),
    transcription_text TEXT,
    tagged_dialogue TEXT,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CHECKLIST ANALYSIS TABLE
-- ============================================================================
CREATE TABLE checklist_analysis (
    id SERIAL PRIMARY KEY,
    call_record_id INTEGER NOT NULL REFERENCES call_records(id) ON DELETE CASCADE,
    
    -- Stage GREETING scores
    greeting_time_before_manager DECIMAL(3,1) DEFAULT 0 CHECK (greeting_time_before_manager IN (0, 0.5, 1)),
    greeting_corporate_greeting DECIMAL(3,1) DEFAULT 0 CHECK (greeting_corporate_greeting IN (0, 0.5, 1)),
    greeting_tone_friendly DECIMAL(3,1) DEFAULT 0 CHECK (greeting_tone_friendly IN (0, 0.5, 1)),
    greeting_no_rush_words DECIMAL(3,1) DEFAULT 0 CHECK (greeting_no_rush_words IN (0, 0.5, 1)),
    greeting_states_purpose DECIMAL(3,1) DEFAULT 0 CHECK (greeting_states_purpose IN (0, 0.5, 1)),
    greeting_no_convenient_phrase DECIMAL(3,1) DEFAULT 0 CHECK (greeting_no_convenient_phrase IN (0, 0.5, 1)),
    greeting_no_address_phrase DECIMAL(3,1) DEFAULT 0 CHECK (greeting_no_address_phrase IN (0, 0.5, 1)),
    greeting_total DECIMAL(4,1) GENERATED ALWAYS AS (
        greeting_time_before_manager + greeting_corporate_greeting + greeting_tone_friendly + 
        greeting_no_rush_words + greeting_states_purpose + greeting_no_convenient_phrase + greeting_no_address_phrase
    ) STORED,
    
    -- Stage CONTACT ESTABLISHMENT scores
    contact_addresses_by_name DECIMAL(3,1) DEFAULT 0 CHECK (contact_addresses_by_name IN (0, 0.5, 1)),
    contact_no_interrupt DECIMAL(3,1) DEFAULT 0 CHECK (contact_no_interrupt IN (0, 0.5, 1)),
    contact_simple_language DECIMAL(3,1) DEFAULT 0 CHECK (contact_simple_language IN (0, 0.5, 1)),
    contact_avoids_formal_tone DECIMAL(3,1) DEFAULT 0 CHECK (contact_avoids_formal_tone IN (0, 0.5, 1)),
    contact_communicates_equal DECIMAL(3,1) DEFAULT 0 CHECK (contact_communicates_equal IN (0, 0.5, 1)),
    contact_uses_small_talk DECIMAL(3,1) DEFAULT 0 CHECK (contact_uses_small_talk IN (0, 0.5, 1)),
    contact_gives_compliment DECIMAL(3,1) DEFAULT 0 CHECK (contact_gives_compliment IN (0, 0.5, 1)),
    contact_uses_humor DECIMAL(3,1) DEFAULT 0 CHECK (contact_uses_humor IN (0, 0.5, 1)),
    contact_total DECIMAL(4,1) GENERATED ALWAYS AS (
        contact_addresses_by_name + contact_no_interrupt + contact_simple_language + 
        contact_avoids_formal_tone + contact_communicates_equal + contact_uses_small_talk + 
        contact_gives_compliment + contact_uses_humor
    ) STORED,
    
    -- Stage PROGRAMMING scores
    programming_uses_at_start DECIMAL(3,1) DEFAULT 0 CHECK (programming_uses_at_start IN (0, 0.5, 1)),
    programming_leads_conversation DECIMAL(3,1) DEFAULT 0 CHECK (programming_leads_conversation IN (0, 0.5, 1)),
    programming_total DECIMAL(4,1) GENERATED ALWAYS AS (
        programming_uses_at_start + programming_leads_conversation
    ) STORED,
    
    -- Stage NEED IDENTIFICATION scores
    need_asks_required_questions DECIMAL(3,1) DEFAULT 0 CHECK (need_asks_required_questions IN (0, 0.5, 1)),
    need_finds_business_area DECIMAL(3,1) DEFAULT 0 CHECK (need_finds_business_area IN (0, 0.5, 1)),
    need_total DECIMAL(4,1) GENERATED ALWAYS AS (
        need_asks_required_questions + need_finds_business_area
    ) STORED,
    
    -- Stage PRESENTATION scores
    presentation_presents_company DECIMAL(3,1) DEFAULT 0 CHECK (presentation_presents_company IN (0, 0.5, 1)),
    presentation_services_with_benefits DECIMAL(3,1) DEFAULT 0 CHECK (presentation_services_with_benefits IN (0, 0.5, 1)),
    presentation_mentions_cases DECIMAL(3,1) DEFAULT 0 CHECK (presentation_mentions_cases IN (0, 0.5, 1)),
    presentation_offers_proposal DECIMAL(3,1) DEFAULT 0 CHECK (presentation_offers_proposal IN (0, 0.5, 1)),
    presentation_knows_product DECIMAL(3,1) DEFAULT 0 CHECK (presentation_knows_product IN (0, 0.5, 1)),
    presentation_total DECIMAL(4,1) GENERATED ALWAYS AS (
        presentation_presents_company + presentation_services_with_benefits + 
        presentation_mentions_cases + presentation_offers_proposal + presentation_knows_product
    ) STORED,
    
    -- Stage HANDLING OBJECTIONS scores
    objections_handles_fully DECIMAL(3,1) DEFAULT 0 CHECK (objections_handles_fully IN (0, 0.5, 1)),
    objections_agrees_empathizes DECIMAL(3,1) DEFAULT 0 CHECK (objections_agrees_empathizes IN (0, 0.5, 1)),
    objections_arguments_match DECIMAL(3,1) DEFAULT 0 CHECK (objections_arguments_match IN (0, 0.5, 1)),
    objections_no_argue DECIMAL(3,1) DEFAULT 0 CHECK (objections_no_argue IN (0, 0.5, 1)),
    objections_offers_proposal DECIMAL(3,1) DEFAULT 0 CHECK (objections_offers_proposal IN (0, 0.5, 1)),
    objections_total DECIMAL(4,1) GENERATED ALWAYS AS (
        objections_handles_fully + objections_agrees_empathizes + objections_arguments_match + 
        objections_no_argue + objections_offers_proposal
    ) STORED,
    
    -- Stage CLOSING scores
    closing_asks_questions_remain DECIMAL(3,1) DEFAULT 0 CHECK (closing_asks_questions_remain IN (0, 0.5, 1)),
    closing_clarifies_proposal_send DECIMAL(3,1) DEFAULT 0 CHECK (closing_clarifies_proposal_send IN (0, 0.5, 1)),
    closing_asks_service_date DECIMAL(3,1) DEFAULT 0 CHECK (closing_asks_service_date IN (0, 0.5, 1)),
    closing_summarizes_conversation DECIMAL(3,1) DEFAULT 0 CHECK (closing_summarizes_conversation IN (0, 0.5, 1)),
    closing_states_next_steps DECIMAL(3,1) DEFAULT 0 CHECK (closing_states_next_steps IN (0, 0.5, 1)),
    closing_leaves_contacts DECIMAL(3,1) DEFAULT 0 CHECK (closing_leaves_contacts IN (0, 0.5, 1)),
    closing_total DECIMAL(4,1) GENERATED ALWAYS AS (
        closing_asks_questions_remain + closing_clarifies_proposal_send + closing_asks_service_date + 
        closing_summarizes_conversation + closing_states_next_steps + closing_leaves_contacts
    ) STORED,
    
    -- Overall total
    overall_total DECIMAL(5,1) GENERATED ALWAYS AS (
        greeting_total + contact_total + programming_total + need_total + 
        presentation_total + objections_total + closing_total
    ) STORED,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AI ANALYSIS TABLE (Structured Analysis)
-- ============================================================================
CREATE TABLE ai_analysis (
    id SERIAL PRIMARY KEY,
    call_record_id INTEGER NOT NULL REFERENCES call_records(id) ON DELETE CASCADE,
    
    -- Basic information
    summary TEXT,
    client_talks_most TEXT,
    client_name VARCHAR(255),
    style_adaptation TEXT,
    target_client TEXT,
    client_needs TEXT,
    manager_responsible VARCHAR(255),
    
    -- Evaluation scores (0-100)
    contact_establishment_value DECIMAL(5,2) CHECK (contact_establishment_value >= 0 AND contact_establishment_value <= 100),
    contact_establishment_explanation TEXT,
    
    qualification_value DECIMAL(5,2) CHECK (qualification_value >= 0 AND qualification_value <= 100),
    qualification_explanation TEXT,
    
    needs_identification_value DECIMAL(5,2) CHECK (needs_identification_value >= 0 AND needs_identification_value <= 100),
    needs_identification_explanation TEXT,
    
    product_presentation_value DECIMAL(5,2) CHECK (product_presentation_value >= 0 AND product_presentation_value <= 100),
    product_presentation_explanation TEXT,
    
    objection_handling_value DECIMAL(5,2) CHECK (objection_handling_value >= 0 AND objection_handling_value <= 100),
    objection_handling_explanation TEXT,
    
    closing_value DECIMAL(5,2) CHECK (closing_value >= 0 AND closing_value <= 100),
    closing_explanation TEXT,
    
    sale_probability_value DECIMAL(5,2) CHECK (sale_probability_value >= 0 AND sale_probability_value <= 100),
    sale_probability_explanation TEXT,
    
    -- Additional fields
    hidden_objections TEXT,
    next_step TEXT,
    
    -- Average score calculation
    average_score DECIMAL(5,2) GENERATED ALWAYS AS (
        (COALESCE(contact_establishment_value, 0) + COALESCE(qualification_value, 0) + 
         COALESCE(needs_identification_value, 0) + COALESCE(product_presentation_value, 0) + 
         COALESCE(objection_handling_value, 0) + COALESCE(closing_value, 0)) / 6
    ) STORED,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LEGACY QUALITY SCORES TABLE (for backward compatibility)
-- ============================================================================
CREATE TABLE legacy_quality_scores (
    id SERIAL PRIMARY KEY,
    call_record_id INTEGER NOT NULL REFERENCES call_records(id) ON DELETE CASCADE,
    call_type VARCHAR(20),
    greeting_score DECIMAL(3,1) DEFAULT 0,
    contact_score DECIMAL(3,1) DEFAULT 0,
    presentation_score DECIMAL(3,1) DEFAULT 0,
    objection_handling_score DECIMAL(3,1) DEFAULT 0,
    closing_score DECIMAL(3,1) DEFAULT 0,
    greeting_stage_total DECIMAL(4,1) DEFAULT 0,
    contact_stage_total DECIMAL(4,1) DEFAULT 0,
    presentation_stage_total DECIMAL(4,1) DEFAULT 0,
    objection_stage_total DECIMAL(4,1) DEFAULT 0,
    closing_stage_total DECIMAL(4,1) DEFAULT 0,
    total_score DECIMAL(5,1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
CREATE INDEX idx_call_records_manager_id ON call_records(manager_id);
CREATE INDEX idx_call_records_call_type ON call_records(call_type);
CREATE INDEX idx_call_records_call_date ON call_records(call_date);
CREATE INDEX idx_call_records_file_id ON call_records(file_id);
CREATE INDEX idx_checklist_analysis_call_record_id ON checklist_analysis(call_record_id);
CREATE INDEX idx_ai_analysis_call_record_id ON ai_analysis(call_record_id);
CREATE INDEX idx_managers_name ON managers(name);
CREATE INDEX idx_managers_status ON managers(status);

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- Manager Performance Summary View
CREATE VIEW manager_performance_summary AS
SELECT 
    m.id as manager_id,
    m.name as manager_name,
    m.department,
    COUNT(cr.id) as total_calls,
    COUNT(CASE WHEN cr.call_type = 'Входящий' THEN 1 END) as inbound_calls,
    COUNT(CASE WHEN cr.call_type = 'Исходящий' THEN 1 END) as outbound_calls,
    AVG(ca.overall_total) as avg_checklist_score,
    AVG(aa.average_score) as avg_ai_score,
    MAX(cr.call_date) as last_call_date,
    COUNT(CASE WHEN cr.call_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as calls_last_30_days
FROM managers m
LEFT JOIN call_records cr ON m.id = cr.manager_id
LEFT JOIN checklist_analysis ca ON cr.id = ca.call_record_id
LEFT JOIN ai_analysis aa ON cr.id = aa.call_record_id
WHERE m.status = 'active'
GROUP BY m.id, m.name, m.department;

-- Daily Performance View
CREATE VIEW daily_performance AS
SELECT 
    DATE(cr.call_date) as call_date,
    m.name as manager_name,
    cr.call_type,
    COUNT(cr.id) as calls_count,
    AVG(ca.overall_total) as avg_checklist_score,
    AVG(aa.average_score) as avg_ai_score,
    AVG(aa.sale_probability_value) as avg_sale_probability
FROM call_records cr
JOIN managers m ON cr.manager_id = m.id
LEFT JOIN checklist_analysis ca ON cr.id = ca.call_record_id
LEFT JOIN ai_analysis aa ON cr.id = aa.call_record_id
WHERE cr.call_date IS NOT NULL
GROUP BY DATE(cr.call_date), m.name, cr.call_type
ORDER BY call_date DESC, manager_name;

-- Stage Performance Analysis View
CREATE VIEW stage_performance_analysis AS
SELECT 
    m.name as manager_name,
    cr.call_type,
    COUNT(ca.id) as total_analyzed_calls,
    AVG(ca.greeting_total) as avg_greeting_score,
    AVG(ca.contact_total) as avg_contact_score,
    AVG(ca.programming_total) as avg_programming_score,
    AVG(ca.need_total) as avg_need_score,
    AVG(ca.presentation_total) as avg_presentation_score,
    AVG(ca.objections_total) as avg_objections_score,
    AVG(ca.closing_total) as avg_closing_score,
    AVG(ca.overall_total) as avg_overall_score
FROM managers m
JOIN call_records cr ON m.id = cr.manager_id
JOIN checklist_analysis ca ON cr.id = ca.call_record_id
GROUP BY m.name, cr.call_type;

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample managers
INSERT INTO managers (name, email, department) VALUES 
('Елизавета Петрова', 'elizaveta@westcol.ru', 'Sales'),
('Владимир Иванов', 'vladimir@westcol.ru', 'Sales'),
('Надежда Сидорова', 'nadezhda@westcol.ru', 'Sales'),
('Анастасия Кузнецова', 'anastasia@westcol.ru', 'Sales'),
('Дмитрий Морозов', 'dmitry@westcol.ru', 'Sales');

-- ============================================================================
-- FUNCTIONS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_managers_updated_at BEFORE UPDATE ON managers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_records_updated_at BEFORE UPDATE ON call_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();