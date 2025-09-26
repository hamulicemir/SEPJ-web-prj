
-- ============================================================================
-- SEPJ: Multi‑Incident Incident Reporting – Init Schema + Seed (Documented)
-- Local Postgres only.
-- ============================================================================
-- # Datei in den Container kopieren
-- % docker login
-- % docker compose cp db/sepj_init.sql db:/sepj_init.sql
-- % docker compose exec db psql -U sepj -d sepj -f /sepj_init.sql
-- ============================================================================
-- Prerequisite extension for UUIDs:
--   CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- 1) RAW REPORTS
-- One original transcript/report may contain multiple incidents.
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_reports (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title            TEXT,                    -- optional title given by user/system
  body             TEXT NOT NULL,           -- raw transcript text (unmodified)
  language         TEXT DEFAULT 'de',       -- e.g. 'de', 'en'
  source           TEXT,                    -- e.g. 'speech-to-text', 'email', 'sms'
  created_by       UUID,                    -- optional user id (if you track users)
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_raw_reports_created_at ON raw_reports(created_at DESC);

COMMENT ON TABLE raw_reports IS 'Originale Rohberichte/Transkripte, noch nicht strukturiert.';
COMMENT ON COLUMN raw_reports.body IS 'Unveränderter Originaltext des Berichts/Transkripts.';

-- ============================================================================
-- 2) INCIDENTS
-- A report can contain multiple incidents (e.g., burglary + property damage).
-- All downstream data (answers, final report) attaches to an INCIDENT.
-- ============================================================================
CREATE TABLE IF NOT EXISTS incidents (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id            UUID NOT NULL REFERENCES raw_reports(id) ON DELETE CASCADE,
  incident_type        TEXT NOT NULL,       -- normalized code: 'einbruch'|'sachbeschaedigung'|'koerperverletzung'|...
  title                TEXT,                -- optional short title/summary
  description          TEXT,                -- optional free-form summary for reviewers
  span_json            JSONB,               -- {spans:[{start,end,quote}]} parts of raw text that support this incident
  template_version_id  UUID,                -- concrete template version chosen for this incident (FK set after selection)
  status               TEXT NOT NULL DEFAULT 'new',  -- 'new'|'in_progress'|'complete'|'archived'
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_incidents_by_report ON incidents(report_id);
CREATE INDEX IF NOT EXISTS idx_incidents_by_type ON incidents(incident_type);

COMMENT ON TABLE incidents IS 'Einzelner Vorfall innerhalb eines Rohberichts (ein Report kann mehrere Incidents haben).';
COMMENT ON COLUMN incidents.span_json IS 'Belegt die Textstellen im Rohtext, die diesen Vorfall stützen (Offsets & Zitate).';
COMMENT ON COLUMN incidents.template_version_id IS 'Verknüpfung zur genutzten Template-Version (nach Auswahl gesetzt).';

-- ============================================================================
-- 3) TEMPLATES (versioned) & QUESTIONS
-- Templates define required/optional questions per incident type. Versions freeze
-- question sets for auditability and reproducibility of past reports.
-- ============================================================================
CREATE TABLE IF NOT EXISTS templates (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_type    TEXT NOT NULL,      -- same normalized codes as incidents.incident_type
  name             TEXT NOT NULL,      -- display name (e.g., 'Körperverletzung Standard')
  is_active        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_templates_type_name ON templates(incident_type, name);

COMMENT ON TABLE templates IS 'Template-Metadaten pro Vorfallstyp (unabhängig von Versionen).';

CREATE TABLE IF NOT EXISTS template_versions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id      UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
  version_tag      TEXT NOT NULL,      -- e.g. 'v1', '2025-09-26-a'
  language         TEXT DEFAULT 'de',
  description      TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (template_id, version_tag)
);

COMMENT ON TABLE template_versions IS 'Versionierte Ausprägungen eines Templates mit festem Fragenkatalog.';

CREATE TABLE IF NOT EXISTS template_questions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_version_id UUID NOT NULL REFERENCES template_versions(id) ON DELETE CASCADE,
  key              TEXT NOT NULL,      -- stable machine key: 'when'|'where'|'who_involved'|...
  label            TEXT NOT NULL,      -- human-friendly caption for UI
  description      TEXT,               -- help text for users
  answer_type      TEXT NOT NULL,      -- 'string'|'enum'|'date'|'datetime'|'people[]'|'location'...
  required         BOOLEAN NOT NULL DEFAULT TRUE,
  order_index      INT NOT NULL DEFAULT 0,
  constraints_json JSONB,              -- e.g., enums: {"enum":["leicht","schwer"]}
  UNIQUE (template_version_id, key)
);
CREATE INDEX IF NOT EXISTS idx_template_questions_order ON template_questions(template_version_id, order_index);

COMMENT ON TABLE template_questions IS 'Fragenkatalog pro Template-Version; Reihenfolge über order_index.';
COMMENT ON COLUMN template_questions.answer_type IS 'Antworttyp für Validierung/Rendering (z. B. datetime, people[]).';

-- ============================================================================
-- 4) STRUCTURED ANSWERS (per INCIDENT)
-- One row per incident & question. status marks auto-extracted vs. confirmed etc.
-- ============================================================================
CREATE TABLE IF NOT EXISTS structured_answers (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id          UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  template_version_id  UUID NOT NULL REFERENCES template_versions(id),
  question_id          UUID NOT NULL REFERENCES template_questions(id),
  status               TEXT NOT NULL DEFAULT 'auto',   -- 'auto'|'confirmed'|'unknown'|'rejected'
  value_json           JSONB,                           -- normalized value; structure depends on answer_type
  evidence_json        JSONB,                           -- spans that support the answer
  created_by           UUID,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (incident_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_answers_incident ON structured_answers(incident_id);

COMMENT ON TABLE structured_answers IS 'Strukturierte Antworten je Incident & Frage (eine Zeile pro Frage).';
COMMENT ON COLUMN structured_answers.status IS 'Qualitäts-/Bearbeitungsstatus: auto, confirmed, unknown, rejected.';

-- ============================================================================
-- 5) FINAL REPORTS (per INCIDENT)
-- Formal, human-readable report text produced from structured answers.
-- Multiple versions may exist over time (keep latest by created_at).
-- ============================================================================
CREATE TABLE IF NOT EXISTS final_reports (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id          UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  template_version_id  UUID NOT NULL REFERENCES template_versions(id),
  body_md              TEXT NOT NULL,         -- final report text (Markdown/Plaintext)
  format               TEXT NOT NULL DEFAULT 'markdown',
  model_name           TEXT,                  -- generator identifier (e.g., 'gemma2:2b')
  prompt_version       TEXT,                  -- prompt recipe/version used
  created_by           UUID,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_final_reports_incident ON final_reports(incident_id, created_at DESC);

COMMENT ON TABLE final_reports IS 'Formelle Berichtstexte je Incident (ggf. mehrere Stände über die Zeit).';

-- ============================================================================
-- 6) LLM RUNS (observability/audit)
-- Optional but useful to trace prompts/responses and model behavior over time.
-- ============================================================================
CREATE TABLE IF NOT EXISTS llm_runs (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  purpose            TEXT NOT NULL,  -- 'classify'|'extract'|'report'
  report_id          UUID REFERENCES raw_reports(id) ON DELETE SET NULL,
  incident_id        UUID REFERENCES incidents(id) ON DELETE SET NULL,
  model_name         TEXT NOT NULL,
  request_json       JSONB NOT NULL, -- prompt + options (temperature, num_ctx, etc.)
  response_json      JSONB,          -- raw model output (optionally truncated)
  tokens_prompt      INT,
  tokens_completion  INT,
  latency_ms         INT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_llm_runs_by_incident ON llm_runs(incident_id, created_at DESC);

COMMENT ON TABLE llm_runs IS 'Protokoll jedes LLM-Aufrufs zur Nachvollziehbarkeit (Debug, Kosten, Qualität).';

-- ============================================================================
-- 7) SEED: Templates (Einbruch, Sachbeschädigung, Körperverletzung) + v1
-- Minimal, shared question set for all three types (customize later per type).
-- ============================================================================
WITH seeds AS (
  INSERT INTO templates (incident_type, name) VALUES
    ('einbruch',           'Einbruch Standard'),
    ('sachbeschaedigung',  'Sachbeschädigung Standard'),
    ('koerperverletzung',  'Körperverletzung Standard'),
    ('brandstiftung',      'Brandstiftung Standard'),
    ('selbstverletzung',   'Selbstverletzung Standard'),
    ('diebstahl',          'Diebstahl Standard')
  ON CONFLICT DO NOTHING
  RETURNING id, incident_type
),
vers AS (
  INSERT INTO template_versions (template_id, version_tag, language, description)
  SELECT id, 'v1', 'de', incident_type || ' v1' FROM seeds
  ON CONFLICT DO NOTHING
  RETURNING id, template_id
)
-- Grundfragen
INSERT INTO template_questions (template_version_id, key, label, description, answer_type, required, order_index, constraints_json)
SELECT vers.id, q.key, q.label, q.description, q.answer_type, q.required, q.order_index, q.constraints_json
FROM vers
JOIN LATERAL (
  VALUES
    ('when','Wann passierte es?','Zeitpunkt/Zeitraum','datetime',TRUE,10,NULL::jsonb),
    ('where','Wo passierte es?','Ort/Adresse','string',TRUE,20,NULL::jsonb),
    ('who_involved','Wer war beteiligt?','Beteiligte Personen','people[]',TRUE,30,NULL::jsonb),
    ('consequences','Welche Folgen gab es?','Verletzungen/Schäden','string',TRUE,40,NULL::jsonb),
    ('witnesses','Gab es Zeugen?','Zeugenliste','people[]',FALSE,50,NULL::jsonb)
) AS q(key,label,description,answer_type,required,order_index,constraints_json) ON TRUE;

-- Typ-spezifische Zusatzfragen (Brandstiftung, Selbstverletzung, Diebstahl, Einbruch, Sachbeschädigung, Körperverletzung)
-- (gekürzt, siehe vorherige Nachricht für Details)

-- ============================================================================ 
-- 8) Reports & Incidents (5 Berichte)
-- ============================================================================

-- Beispielhafte Reports mit Multi-Incidents
INSERT INTO raw_reports (title, body, source, language) VALUES
  ('Schulhof Auseinandersetzung','Gestern gegen 18:30 gerieten A und B auf dem Schulhof in Streit. B erlitt eine Prellung am Arm.','speech-to-text','de'),
  ('Kellerbrand in Wohnhaus','Am 20.09.2025 wurde Rauch im Keller festgestellt. Ein Karton brannte, die Feuerwehr löschte schnell. Niemand verletzt.','email','de'),
  ('Fahrraddiebstahl am Bahnhof','Heute Vormittag wurde das angeschlossene Fahrrad von C am Bahnhof entwendet. Schloss lag aufgebrochen daneben.','sms','de'),
  ('Mehrere Vorfälle in einer Nacht','Gegen 23 Uhr wurde eine Kellertür aufgebrochen. Kurz darauf brannte ein Mülleimer vor dem Eingang. Beim Versuch, den Täter zu stellen, kam es zu einer Rangelei.','speech-to-text','de'),
  ('Schnittverletzung beim Kochen','Heute früh um 07:10 schnitt sich D versehentlich beim Schneiden am Finger. Der Schnitt wurde vor Ort versorgt.','note','de');

-- Danach Incidents erzeugen (pro Report die passenden Typen, wie oben beschrieben).
-- Danach structured_answers + final_reports Beispiel für Körperverletzung & Diebstahl.