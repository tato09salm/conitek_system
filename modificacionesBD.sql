BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='events') THEN
    CREATE TABLE events (
      id SERIAL PRIMARY KEY,
      name VARCHAR(200) UNIQUE NOT NULL,
      event_date DATE NOT NULL,
      location VARCHAR(200) NOT NULL,
      capacity INTEGER NOT NULL DEFAULT 500,
      current_count INTEGER NOT NULL DEFAULT 0,
      is_active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_events_date ON events(event_date);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='event_registration') THEN
    CREATE TABLE event_registration (
      id SERIAL PRIMARY KEY,
      event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
      participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
      status VARCHAR(20) NOT NULL DEFAULT 'Pendiente' CHECK (status IN ('Pendiente','Confirmada','Cancelada')),
      payment_reference VARCHAR(100) UNIQUE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT uq_event_registration UNIQUE(event_id, participant_id)
    );
    CREATE INDEX idx_evreg_event ON event_registration(event_id);
    CREATE INDEX idx_evreg_status ON event_registration(status);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='event_speaker') THEN
    CREATE TABLE event_speaker (
      id SERIAL PRIMARY KEY,
      event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
      participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
      CONSTRAINT uq_event_speaker UNIQUE(event_id, participant_id)
    );
    CREATE INDEX idx_evspeaker_event ON event_speaker(event_id);
  END IF;
END $$;

COMMIT;

--2 modif

-- Alinear tabla usada por la app
-- 1) Verificar si existe la tabla 'participants'
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND table_name IN ('participants','participant');

-- 2) Si trabajas con 'participants', garantizar la columna phone
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema='public' AND table_name='participants'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='participants' AND column_name='phone'
    ) THEN
      ALTER TABLE participants ADD COLUMN phone VARCHAR(20);
    END IF;
  END IF;
END $$;

-- 3) Si en tu BD solo existe 'participant' (singular), tienes dos opciones:
--    a) migrar datos a 'participants' y usar la app tal cual
--    b) o renombrar la tabla para alinearla con el ORM (recomendado una sola vez):
-- ALTER TABLE participant RENAME TO participants;
-- Y luego asegurarte de las columnas:
-- ALTER TABLE participants ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

----=================
-- Añadir columna user_id en participants y FK a users
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='participants' AND column_name='user_id'
  ) THEN
    ALTER TABLE participants ADD COLUMN user_id INTEGER;
    ALTER TABLE participants
      ADD CONSTRAINT fk_participants_user
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
  END IF;
END $$;

-- Indexar DNI y username para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_participants_dni ON participants(dni);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);


--
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema='public' AND table_name='paper_files'
  ) THEN
    CREATE TABLE paper_files (
      id SERIAL PRIMARY KEY,
      paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
      filename VARCHAR(255),
      path TEXT,
      mime_type VARCHAR(100),
      uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_paper_files_paper ON paper_files(paper_id);
  END IF;
END $$;

COMMIT;


--===========
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='payments' AND column_name='approved_at'
  ) THEN
    ALTER TABLE payments ADD COLUMN approved_at TIMESTAMP;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='payments' AND column_name='approved_by'
  ) THEN
    ALTER TABLE payments ADD COLUMN approved_by INTEGER;
  END IF;
END $$;

COMMIT;

-- 
ALTER TABLE event_speaker
  ADD COLUMN IF NOT EXISTS paper_id INTEGER NULL;

ALTER TABLE event_speaker
  ADD CONSTRAINT event_speaker_paper_fk
  FOREIGN KEY (paper_id) REFERENCES papers(id);

ALTER TABLE event_speaker
  DROP CONSTRAINT IF EXISTS uq_event_speaker;

ALTER TABLE event_speaker
  ADD CONSTRAINT uq_event_speaker_triplet
  UNIQUE (event_id, participant_id, paper_id);

  --
  CREATE OR REPLACE FUNCTION prevent_duplicate_speaker()
RETURNS trigger AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM event_speaker
    WHERE event_id = NEW.event_id
      AND participant_id = NEW.participant_id
  ) THEN
    RAISE EXCEPTION 'Ponente ya asignado al evento';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_duplicate_speaker ON event_speaker;

CREATE TRIGGER trg_prevent_duplicate_speaker
BEFORE INSERT ON event_speaker
FOR EACH ROW EXECUTE FUNCTION prevent_duplicate_speaker();

ALTER TABLE event_speaker
  DROP CONSTRAINT IF EXISTS uq_event_speaker_triplet;

ALTER TABLE event_speaker
  ADD CONSTRAINT uq_event_speaker
  UNIQUE (event_id, participant_id);

--
