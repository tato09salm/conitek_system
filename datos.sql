BEGIN;
INSERT INTO users (username, email, password_hash, role, is_active)
SELECT 'admin','admin@unt.edu.pe','123','Admin',TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin');
INSERT INTO users (username, email, password_hash, role, is_active)
SELECT 'tesorero','tesoreria@unt.edu.pe','123','Tesorero',TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='tesorero');
INSERT INTO users (username, email, password_hash, role, is_active)
SELECT 'evaluador','evaluador@unt.edu.pe','123','Evaluador',TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='evaluador');
INSERT INTO participants (dni, full_name, email, university, p_type, modality, phone)
SELECT '12345678','Juan Pérez','juan.perez@correo.com','UNT','Estudiante','Presencial','999111222'
WHERE NOT EXISTS (SELECT 1 FROM participants WHERE dni='12345678');
INSERT INTO participants (dni, full_name, email, university, p_type, modality, phone)
SELECT '87654321','María López','maria.lopez@correo.com','UNT','Profesional','Virtual','988777666'
WHERE NOT EXISTS (SELECT 1 FROM participants WHERE dni='87654321');
INSERT INTO participants (dni, full_name, email, university, p_type, modality, phone)
SELECT '44556677','Carlos Ruiz','carlos.ruiz@correo.com','UNT','Ponente','Presencial','987654321'
WHERE NOT EXISTS (SELECT 1 FROM participants WHERE dni='44556677');
INSERT INTO participants (dni, full_name, email, university, p_type, modality, phone)
SELECT '11223344','Ana Torres','ana.torres@correo.com','UPAO','Estudiante','Virtual','912345678'
WHERE NOT EXISTS (SELECT 1 FROM participants WHERE dni='11223344');
INSERT INTO participants (dni, full_name, email, university, p_type, modality, phone)
SELECT '99887766','Luis García','luis.garcia@correo.com','UNT','Profesional','Presencial','923456789'
WHERE NOT EXISTS (SELECT 1 FROM participants WHERE dni='99887766');
INSERT INTO events (name, event_date, location, capacity, current_count, is_active)
SELECT 'CONITEK 2026 - Conferencias','2026-10-16','Trujillo',500,0,TRUE
WHERE NOT EXISTS (SELECT 1 FROM events WHERE name='CONITEK 2026 - Conferencias');
INSERT INTO events (name, event_date, location, capacity, current_count, is_active)
SELECT 'CONITEK 2026 - Talleres','2026-10-17','Trujillo',200,0,TRUE
WHERE NOT EXISTS (SELECT 1 FROM events WHERE name='CONITEK 2026 - Talleres');
INSERT INTO event_speaker (event_id, participant_id)
SELECT e.id, p.id
FROM events e, participants p
WHERE e.name='CONITEK 2026 - Conferencias' AND p.dni='44556677'
AND NOT EXISTS (
  SELECT 1 FROM event_speaker es
  WHERE es.event_id=e.id AND es.participant_id=p.id
);
INSERT INTO event_registration (event_id, participant_id, status, payment_reference)
SELECT e.id, p.id, 'Pendiente', 'EVT-REG-001'
FROM events e, participants p
WHERE e.name='CONITEK 2026 - Conferencias' AND p.dni='12345678'
AND NOT EXISTS (
  SELECT 1 FROM event_registration r
  WHERE r.event_id=e.id AND r.participant_id=p.id
);
INSERT INTO event_registration (event_id, participant_id, status, payment_reference)
SELECT e.id, p.id, 'Confirmada', 'EVT-REG-002'
FROM events e, participants p
WHERE e.name='CONITEK 2026 - Talleres' AND p.dni='87654321'
AND NOT EXISTS (
  SELECT 1 FROM event_registration r
  WHERE r.event_id=e.id AND r.participant_id=p.id
);
INSERT INTO payments (participant_id, amount, method, reference, status)
SELECT p.id, 120.00, 'Yape', 'EVT-REG-002', 'Aprobado'
FROM participants p
WHERE p.dni='87654321'
AND NOT EXISTS (SELECT 1 FROM payments pay WHERE pay.reference='EVT-REG-002');
INSERT INTO payments (participant_id, amount, method, reference, status)
SELECT p.id, 100.00, 'Plin', 'EVT-REG-001', 'Pendiente'
FROM participants p
WHERE p.dni='12345678'
AND NOT EXISTS (SELECT 1 FROM payments pay WHERE pay.reference='EVT-REG-001');
UPDATE events e SET current_count = sub.cnt
FROM (
  SELECT r.event_id, COUNT(*) AS cnt
  FROM event_registration r
  WHERE r.status='Confirmada'
  GROUP BY r.event_id
) sub
WHERE e.id=sub.event_id;
COMMIT;
