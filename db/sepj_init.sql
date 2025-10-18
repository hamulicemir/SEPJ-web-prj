
-- ============================================================================
-- SEPJ: Multi‑Incident Incident Reporting – Init Schema + Seed (Documented)
-- Local Postgres only.
-- ============================================================================
-- # Datei in den Container kopieren
-- % docker login
-- % docker compose cp db/sepj_init.sql db:/sepj_init.sql
-- % docker compose exec db psql -U sepj -d sepj -f /sepj_init.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- 1) RAW REPORTS – Original transcripts
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_reports (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title       TEXT,
  body        TEXT NOT NULL,
  language    TEXT DEFAULT 'de',
  source      TEXT,
  created_by  UUID,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
  );
CREATE INDEX IF NOT EXISTS idx_raw_reports_created_at ON raw_reports(created_at DESC);

-- ============================================================================
-- 2) INCIDENTS – Events extracted from reports
-- ============================================================================
CREATE TABLE IF NOT EXISTS incidents (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id      UUID NOT NULL REFERENCES raw_reports(id) ON DELETE CASCADE,
  incident_type  TEXT NOT NULL,
  title          TEXT,
  description    TEXT,
  status         TEXT NOT NULL DEFAULT 'new',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_incidents_by_report ON incidents(report_id);
CREATE INDEX IF NOT EXISTS idx_incidents_by_type ON incidents(incident_type);

-- ============================================================================
-- 3) INCIDENT TYPES – Stammdaten pro Vorfallstyp
-- ============================================================================
CREATE TABLE IF NOT EXISTS incident_types (
  code        TEXT PRIMARY KEY,  -- 'koerperverletzung', 'einbruch', ...
  name        TEXT NOT NULL,
  description TEXT,
  prompt_ref  TEXT,              -- z. B. Referenz auf verwendeten Prompt
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 4) INCIDENT QUESTIONS – Fragen für Formulare pro Typ
-- ============================================================================
CREATE TABLE IF NOT EXISTS incident_questions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_type TEXT NOT NULL REFERENCES incident_types(code) ON DELETE CASCADE,
  question_key  TEXT NOT NULL,
  label         TEXT NOT NULL,
  answer_type   TEXT NOT NULL,     -- 'string'|'date'|'people[]'|...
  required      BOOLEAN DEFAULT TRUE,
  order_index   INT DEFAULT 0,
  UNIQUE (incident_type, question_key)
);

-- ============================================================================
-- 5) STRUCTURED ANSWERS – Per-incident attribute values
-- ============================================================================
CREATE TABLE IF NOT EXISTS structured_answers (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id   UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  question_key  TEXT NOT NULL,
  value_json    JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (incident_id, question_key)
);
CREATE INDEX IF NOT EXISTS idx_answers_incident ON structured_answers(incident_id);

-- ============================================================================
-- 6) FINAL REPORTS – Generated report text per incident
-- ============================================================================
CREATE TABLE IF NOT EXISTS final_reports (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id    UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  body_md        TEXT NOT NULL,
  model_name     TEXT,
  created_by     UUID,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 7) LLM RUNS – Model observability / audit logs
-- ============================================================================
CREATE TABLE IF NOT EXISTS llm_runs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  purpose           TEXT NOT NULL,
  report_id         UUID REFERENCES raw_reports(id) ON DELETE SET NULL,
  incident_id       UUID REFERENCES incidents(id) ON DELETE SET NULL,
  model_name        TEXT NOT NULL,
  request_json      JSONB NOT NULL,
  response_json     JSONB,
  tokens_prompt     INT,
  tokens_completion INT,
  latency_ms        INT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_llm_runs_by_incident ON llm_runs(incident_id, created_at DESC);

-- ============================================================================
-- 8) PROMPTS – Prompt-Stammdaten
-- ============================================================================
CREATE TABLE IF NOT EXISTS prompts (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT NOT NULL,
  purpose        TEXT NOT NULL,      -- 'classify'|'extract'|'report'
  version_tag    TEXT DEFAULT 'v1',
  content        TEXT NOT NULL,      -- eigentlicher Prompt-Text
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- ============================================================================

-- ============================================================================
-- SEED: INCIDENT TYPES (Vorfallstypen)
-- ============================================================================
INSERT INTO incident_types (code, name, description, prompt_ref)
VALUES
  ('einbruch',          'Einbruch',          'Unbefugtes Eindringen in ein Gebäude oder Raum', 'prompt_einbruch_v1'),
  ('sachbeschaedigung', 'Sachbeschädigung',  'Zerstörung oder Beschädigung fremden Eigentums', 'prompt_sach_v1'),
  ('koerperverletzung', 'Körperverletzung',  'Physische Auseinandersetzungen zwischen Personen', 'prompt_koerp_v1'),
  ('brandstiftung',     'Brandstiftung',     'Vorsätzliches oder fahrlässiges Entzünden von Sachen', 'prompt_brand_v1'),
  ('selbstverletzung',  'Selbstverletzung',  'Selbstzugefügte Verletzungen', 'prompt_selbst_v1'),
  ('diebstahl',         'Diebstahl',         'Entwendung von fremdem Eigentum', 'prompt_diebstahl_v1')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SEED: INCIDENT QUESTIONS (Fragenkataloge pro Typ)
-- ============================================================================
-- Gemeinsame Grundfragen
INSERT INTO incident_questions (incident_type, question_key, label, answer_type, required, order_index)
VALUES
  ('einbruch',          'when',         'Wann passierte es?',          'datetime', TRUE, 10),
  ('einbruch',          'where',        'Wo passierte es?',            'string',   TRUE, 20),
  ('einbruch',          'who_involved', 'Wer war beteiligt?',          'people[]', TRUE, 30),
  ('einbruch',          'consequences', 'Welche Folgen gab es?',       'string',   TRUE, 40),
  ('einbruch',          'witnesses',    'Gab es Zeugen?',              'people[]', FALSE, 50),

  ('sachbeschaedigung', 'when',         'Wann passierte es?',          'datetime', TRUE, 10),
  ('sachbeschaedigung', 'where',        'Wo passierte es?',            'string',   TRUE, 20),
  ('sachbeschaedigung', 'who_involved', 'Wer war beteiligt?',          'people[]', TRUE, 30),
  ('sachbeschaedigung', 'consequences', 'Welche Schäden entstanden?',  'string',   TRUE, 40),
  ('sachbeschaedigung', 'witnesses',    'Gab es Zeugen?',              'people[]', FALSE, 50),

  ('koerperverletzung', 'when',         'Wann passierte es?',          'datetime', TRUE, 10),
  ('koerperverletzung', 'where',        'Wo passierte es?',            'string',   TRUE, 20),
  ('koerperverletzung', 'who_involved', 'Wer war beteiligt?',          'people[]', TRUE, 30),
  ('koerperverletzung', 'opfer',        'Wer ist das Opfer?',          'people[]', TRUE, 40),
  ('koerperverletzung', 'taeter',       'Wer ist der Täter?',          'people[]', TRUE, 50),
  ('koerperverletzung', 'consequences', 'Welche Verletzungen gab es?', 'string',   TRUE, 60),
  ('koerperverletzung', 'witnesses',    'Gab es Zeugen?',              'people[]', FALSE, 70),

  ('brandstiftung',     'when',         'Wann wurde das Feuer bemerkt?','datetime', TRUE, 10),
  ('brandstiftung',     'where',        'Wo brannte es?',              'string',   TRUE, 20),
  ('brandstiftung',     'who_involved', 'Wer war vor Ort?',            'people[]', TRUE, 30),
  ('brandstiftung',     'consequences', 'Welche Schäden entstanden?',  'string',   TRUE, 40),

  ('selbstverletzung',  'when',         'Wann geschah die Selbstverletzung?', 'datetime', TRUE, 10),
  ('selbstverletzung',  'where',        'Wo geschah es?',                    'string',   TRUE, 20),
  ('selbstverletzung',  'who_involved', 'Wer war beteiligt?',                'people[]', FALSE, 30),
  ('selbstverletzung',  'consequences', 'Welche Verletzungen?',             'string',   TRUE, 40),

  ('diebstahl',         'when',         'Wann passierte es?',               'datetime', TRUE, 10),
  ('diebstahl',         'where',        'Wo passierte es?',                 'string',   TRUE, 20),
  ('diebstahl',         'who_involved', 'Wer war beteiligt?',               'people[]', TRUE, 30),
  ('diebstahl',         'consequences', 'Was wurde entwendet?',             'string',   TRUE, 40),
  ('diebstahl',         'witnesses',    'Gab es Zeugen?',                   'people[]', FALSE, 50)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SEED: Beispielhafte Rohberichte (mit mehreren Vorfällen)
-- ============================================================================
INSERT INTO raw_reports (title, body, source, language) VALUES
  ('Schulhof Auseinandersetzung',
   'Gestern gegen 18:30 gerieten A und B auf dem Schulhof in Streit. B erlitt eine Prellung am Arm.',
   'speech-to-text', 'de'),

  ('Kellerbrand in Wohnhaus',
   'Am 20.09.2025 wurde Rauch im Keller festgestellt. Ein Karton brannte, die Feuerwehr löschte schnell. Niemand verletzt.',
   'email', 'de'),

  ('Fahrraddiebstahl am Bahnhof',
   'Heute Vormittag wurde das angeschlossene Fahrrad von C am Bahnhof entwendet. Schloss lag aufgebrochen daneben.',
   'sms', 'de'),

  ('Mehrere Vorfälle in einer Nacht',
   'Gegen 23 Uhr wurde eine Kellertür aufgebrochen. Kurz darauf brannte ein Mülleimer vor dem Eingang. Beim Versuch, den Täter zu stellen, kam es zu einer Rangelei.',
   'speech-to-text', 'de'),

  ('Schnittverletzung beim Kochen',
   'Heute früh um 07:10 schnitt sich D versehentlich beim Schneiden am Finger. Der Schnitt wurde vor Ort versorgt.',
   'note', 'de');