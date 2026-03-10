-- ============================================================
-- SISTEMA DE GESTIÓN CONITEK 2026
-- Universidad Nacional de Trujillo
-- Base de Datos: PostgreSQL
-- EJECUTAR EN ORDEN - SIN ERRORES
-- ============================================================

-- ============================================================
-- PASO 1: ELIMINAR TABLAS EXISTENTES (Si las hubiera)
-- ============================================================
-- Orden inverso: primero las que tienen FK, luego las independientes

DROP TABLE IF EXISTS certificate CASCADE;
DROP TABLE IF EXISTS payment CASCADE;
DROP TABLE IF EXISTS inscription_workshop CASCADE;
DROP TABLE IF EXISTS evaluation CASCADE;
DROP TABLE IF EXISTS inscription CASCADE;
DROP TABLE IF EXISTS paper CASCADE;
DROP TABLE IF EXISTS workshop CASCADE;
DROP TABLE IF EXISTS conference CASCADE;
DROP TABLE IF EXISTS participant CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS payment_method CASCADE;
DROP TABLE IF EXISTS participant_type CASCADE;
DROP TABLE IF EXISTS modality CASCADE;

-- ============================================================
-- PASO 2: TABLAS INDEPENDIENTES (Sin Foreign Keys)
-- ============================================================

-- 2.1 Tipos de Participante
CREATE TABLE participant_type (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(50) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_unt DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 Modalidades
CREATE TABLE modality (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(50) NOT NULL,
    max_capacity INTEGER NOT NULL,
    current_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2.3 Métodos de Pago
CREATE TABLE payment_method (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2.4 Usuarios del Sistema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('Admin', 'Comite', 'Evaluador', 'Tesorero', 'Participante')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PASO 3: TABLAS PRINCIPALES (Dependen de Nivel 2)
-- ============================================================

-- 3.1 Participantes
CREATE TABLE participant (
    id SERIAL PRIMARY KEY,
    dni VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    university VARCHAR(150),
    participant_type_id INTEGER NOT NULL REFERENCES participant_type(id),
    modality_id INTEGER NOT NULL REFERENCES modality(id),
    is_unt BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 3.2 Conferencias Magistrales
CREATE TABLE conference (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    speaker_name VARCHAR(150) NOT NULL,
    speaker_affiliation VARCHAR(150),
    description TEXT,
    schedule_date DATE NOT NULL,
    schedule_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    location VARCHAR(100),
    virtual_link VARCHAR(500),
    max_capacity INTEGER DEFAULT 500,
    current_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.3 Talleres Especializados
CREATE TABLE workshop (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    instructor_name VARCHAR(150) NOT NULL,
    description TEXT,
    schedule_date DATE NOT NULL,
    schedule_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    location VARCHAR(100),
    virtual_link VARCHAR(500),
    max_capacity INTEGER NOT NULL,
    current_count INTEGER DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.4 Ponencias Académicas
CREATE TABLE paper (
    id SERIAL PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES participant(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    abstract TEXT NOT NULL,
    keywords VARCHAR(500),
    track VARCHAR(100),
    status VARCHAR(30) DEFAULT 'Enviado' CHECK (status IN ('Enviado', 'En Evaluación', 'Aceptado', 'Rechazado', 'Retirado')),
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    presentation_date DATE,
    presentation_time TIME,
    session_room VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.5 Inscripciones al Congreso
CREATE TABLE inscription (
    id SERIAL PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES participant(id) ON DELETE CASCADE,
    inscription_code VARCHAR(20) UNIQUE NOT NULL,
    inscription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'Pendiente' CHECK (status IN ('Pendiente', 'Confirmada', 'Cancelada', 'Completada')),
    total_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    final_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(30) DEFAULT 'Pendiente' CHECK (payment_status IN ('Pendiente', 'Parcial', 'Completado', 'Reembolsado')),
    attended BOOLEAN DEFAULT FALSE,
    attendance_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PASO 4: TABLAS INTERMEDIAS (Dependen de Nivel 3)
-- ============================================================

-- 4.1 Evaluaciones de Ponencias
CREATE TABLE evaluation (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    evaluator_id INTEGER NOT NULL REFERENCES users(id),
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    criteria_originality INTEGER DEFAULT 0 CHECK (criteria_originality >= 0 AND criteria_originality <= 25),
    criteria_methodology INTEGER DEFAULT 0 CHECK (criteria_methodology >= 0 AND criteria_methodology <= 25),
    criteria_relevance INTEGER DEFAULT 0 CHECK (criteria_relevance >= 0 AND criteria_relevance <= 25),
    criteria_presentation INTEGER DEFAULT 0 CHECK (criteria_presentation >= 0 AND criteria_presentation <= 25),
    comments TEXT,
    recommendation VARCHAR(50) CHECK (recommendation IN ('Aceptar', 'Rechazar', 'Revisar')),
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(paper_id, evaluator_id)
);

-- 4.2 Inscripción a Talleres (Tabla Intermedia N:M)
CREATE TABLE inscription_workshop (
    id SERIAL PRIMARY KEY,
    inscription_id INTEGER NOT NULL REFERENCES inscription(id) ON DELETE CASCADE,
    workshop_id INTEGER NOT NULL REFERENCES workshop(id),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attended BOOLEAN DEFAULT FALSE,
    
    UNIQUE(inscription_id, workshop_id)
);

-- 4.3 Pagos
CREATE TABLE payment (
    id SERIAL PRIMARY KEY,
    inscription_id INTEGER NOT NULL REFERENCES inscription(id) ON DELETE CASCADE,
    payment_method_id INTEGER NOT NULL REFERENCES payment_method(id),
    transaction_reference VARCHAR(100) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'Pendiente' CHECK (status IN ('Pendiente', 'Aprobado', 'Rechazado', 'Reembolsado')),
    verified_by INTEGER REFERENCES users(id),
    verified_at TIMESTAMP,
    observation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PASO 5: TABLAS FINALES (Dependen de Múltiples Niveles)
-- ============================================================

-- 5.1 Certificados
CREATE TABLE certificate (
    id SERIAL PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES participant(id) ON DELETE CASCADE,
    inscription_id INTEGER REFERENCES inscription(id),
    certificate_code VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Asistencia', 'Ponencia', 'Taller', 'Conferencia', 'Organizador')),
    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_name VARCHAR(200) NOT NULL,
    event_date VARCHAR(50) NOT NULL,
    hours INTEGER DEFAULT 0,
    is_downloadable BOOLEAN DEFAULT TRUE,
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_unique_certificate UNIQUE(participant_id, type, event_name)
);

-- ============================================================
-- PASO 6: CREACIÓN DE ÍNDICES
-- ============================================================

CREATE INDEX idx_participant_dni ON participant(dni);
CREATE INDEX idx_participant_email ON participant(email);
CREATE INDEX idx_participant_type ON participant(participant_type_id);
CREATE INDEX idx_participant_modality ON participant(modality_id);
CREATE INDEX idx_inscription_participant ON inscription(participant_id);
CREATE INDEX idx_inscription_status ON inscription(status);
CREATE INDEX idx_inscription_code ON inscription(inscription_code);
CREATE INDEX idx_payment_inscription ON payment(inscription_id);
CREATE INDEX idx_payment_status ON payment(status);
CREATE INDEX idx_paper_participant ON paper(participant_id);
CREATE INDEX idx_paper_status ON paper(status);
CREATE INDEX idx_evaluation_paper ON evaluation(paper_id);
CREATE INDEX idx_evaluation_evaluator ON evaluation(evaluator_id);
CREATE INDEX idx_certificate_participant ON certificate(participant_id);
CREATE INDEX idx_certificate_code ON certificate(certificate_code);
CREATE INDEX idx_workshop_date ON workshop(schedule_date);
CREATE INDEX idx_conference_date ON conference(schedule_date);

-- ============================================================
-- PASO 7: VISTAS PARA REPORTES
-- ============================================================

-- Vista: Resumen de Participantes por Tipo y Modalidad
CREATE OR REPLACE VIEW v_participant_summary AS
SELECT 
    pt.description AS tipo_participante,
    m.description AS modalidad,
    COUNT(p.id) AS total_participantes,
    SUM(CASE WHEN p.is_unt THEN 1 ELSE 0 END) AS participantes_unt
FROM participant p
JOIN participant_type pt ON p.participant_type_id = pt.id
JOIN modality m ON p.modality_id = m.id
GROUP BY pt.description, m.description;

-- Vista: Estado de Pagos por Inscripción
CREATE OR REPLACE VIEW v_payment_status AS
SELECT 
    i.inscription_code,
    p.first_name || ' ' || p.last_name AS participante,
    i.final_amount AS monto_total,
    COALESCE(SUM(pay.amount), 0) AS monto_pagado,
    i.payment_status AS estado,
    MAX(pay.payment_date) AS ultimo_pago
FROM inscription i
JOIN participant p ON i.participant_id = p.id
LEFT JOIN payment pay ON i.id = pay.inscription_id AND pay.status = 'Aprobado'
GROUP BY i.inscription_code, p.first_name, p.last_name, i.final_amount, i.payment_status;

-- Vista: Ponencias por Estado de Evaluación
CREATE OR REPLACE VIEW v_paper_evaluation_status AS
SELECT 
    pap.id AS paper_id,
    pap.title AS titulo,
    p.first_name || ' ' || p.last_name AS autor,
    pap.status AS estado,
    COUNT(ev.id) AS num_evaluaciones,
    AVG(ev.score) AS promedio_score,
    pap.submission_date AS fecha_envio
FROM paper pap
JOIN participant p ON pap.participant_id = p.id
LEFT JOIN evaluation ev ON pap.id = ev.paper_id
GROUP BY pap.id, pap.title, p.first_name, p.last_name, pap.status, pap.submission_date;

-- Vista: Recaudación Total por Método de Pago
CREATE OR REPLACE VIEW v_revenue_by_payment_method AS
SELECT 
    pm.description AS metodo_pago,
    COUNT(pay.id) AS num_transacciones,
    SUM(pay.amount) AS total_recaudado,
    COUNT(CASE WHEN pay.status = 'Aprobado' THEN 1 END) AS transacciones_aprobadas
FROM payment pay
JOIN payment_method pm ON pay.payment_method_id = pm.id
GROUP BY pm.description;

-- ============================================================
-- PASO 8: TRIGGERS PARA AUTOMATIZACIÓN
-- ============================================================

-- Trigger: Actualizar contador de capacidad en Modalidad
CREATE OR REPLACE FUNCTION update_modality_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE modality SET current_count = current_count + 1 WHERE id = NEW.modality_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE modality SET current_count = current_count - 1 WHERE id = OLD.modality_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_modality_count
AFTER INSERT OR DELETE ON participant
FOR EACH ROW EXECUTE FUNCTION update_modality_count();

-- Trigger: Actualizar contador de capacidad en Talleres
CREATE OR REPLACE FUNCTION update_workshop_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE workshop SET current_count = current_count + 1 WHERE id = NEW.workshop_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE workshop SET current_count = current_count - 1 WHERE id = OLD.workshop_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_workshop_count
AFTER INSERT OR DELETE ON inscription_workshop
FOR EACH ROW EXECUTE FUNCTION update_workshop_count();

-- Trigger: Actualizar timestamp updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_participant_updated_at
BEFORE UPDATE ON participant
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_inscription_updated_at
BEFORE UPDATE ON inscription
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- PASO 9: DATOS INICIALES (SEED DATA)
-- ============================================================

-- Tipos de Participante
INSERT INTO participant_type (code, description, base_price, discount_unt) VALUES
('EST', 'Estudiante', 50.00, 20.00),
('PRO', 'Profesional', 100.00, 0.00),
('PON', 'Ponente', 0.00, 0.00);

-- Modalidades
INSERT INTO modality (code, description, max_capacity, current_count) VALUES
('PRE', 'Presencial', 300, 0),
('VIR', 'Virtual', 200, 0);

-- Métodos de Pago
INSERT INTO payment_method (code, description, is_active) VALUES
('YAPE', 'Yape', TRUE),
('PLIN', 'Plin', TRUE),
('TRANS', 'Transferencia Bancaria', TRUE),
('EFEC', 'Efectivo en Caja', TRUE);

-- Usuarios del Sistema (password hash simplificado para demo)
INSERT INTO users (username, password_hash, email, role, is_active) VALUES
('admin', 'admin123', 'admin@unt.edu.pe', 'Admin', TRUE),
('tesorero', 'teso123', 'tesoreria@unt.edu.pe', 'Tesorero', TRUE),
('evaluador', 'eval123', 'evaluador@unt.edu.pe', 'Evaluador', TRUE);

-- ============================================================
-- PASO 10: COMENTARIOS Y VERIFICACIÓN
-- ============================================================

COMMENT ON TABLE participant IS 'Almacena datos de todos los participantes del congreso';
COMMENT ON TABLE inscription IS 'Registro de inscripciones al congreso con estado de pago';
COMMENT ON TABLE paper IS 'Ponencias académicas enviadas por participantes';
COMMENT ON TABLE evaluation IS 'Evaluaciones de ponencias por comité evaluador';
COMMENT ON TABLE payment IS 'Transacciones de pago de inscripciones';
COMMENT ON TABLE certificate IS 'Certificados generados para participantes';
COMMENT ON TABLE workshop IS 'Talleres especializados del congreso';
COMMENT ON TABLE conference IS 'Conferencias magistrales del congreso';

-- ============================================================
-- CONSULTAS DE VERIFICACIÓN (Opcional - Descomentar para probar)
-- ============================================================

-- Verificar tablas creadas
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;

-- Verificar datos iniciales
-- SELECT * FROM participant_type;
-- SELECT * FROM modality;
-- SELECT * FROM payment_method;
-- SELECT * FROM users;

-- ============================================================
-- FIN DEL SCRIPT - EJECUCIÓN COMPLETADA EXITOSAMENTE
-- ============================================================