-- =============================================================================
-- busmora-ai DEV-ONLY database bootstrap.             See docs/adr/0007.
--
-- A stand-in for the busmora-api Drizzle migrations so busmora-ai can be
-- developed alone. It NEVER runs outside the local compose stack. Once
-- busmora-api publishes its real migrations, local development should use them
-- and this file should shrink to nothing.
--
-- What it mirrors from the approved design (BTD §7.5, BTD-ADR-08, BTD-ADR-09):
--   * ai_runtime      schema owned by the AI role (LangGraph checkpoints)
--   * brain_read      read-only eligibility views; the AI role can read the
--                     views and nothing else
--   * row-level security keyed to the workspace, enforced even for the views'
--     owner, so tenant isolation is exercised locally
--
-- PROVISIONAL, to be replaced by busmora-api's real definitions:
--   * every column name and type in the views below
--   * the session setting used for RLS: app.workspace_id
-- =============================================================================

-- Roles ----------------------------------------------------------------------
CREATE ROLE busmora_ai LOGIN PASSWORD 'busmora_ai_dev'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;

-- Owns the stand-in tables and views. Not a login role, not a superuser, so
-- FORCE ROW LEVEL SECURITY applies to it and therefore to its views.
CREATE ROLE dev_brain_owner NOLOGIN NOSUPERUSER NOBYPASSRLS;

-- ai_runtime: technical state written by ai-agent -----------------------------
CREATE SCHEMA ai_runtime AUTHORIZATION busmora_ai;

-- Stand-in base tables (busmora-api's brain module owns the real ones) ---------
CREATE SCHEMA dev_brain AUTHORIZATION dev_brain_owner;
SET ROLE dev_brain_owner;

CREATE TABLE dev_brain.items (
    item_id             uuid        PRIMARY KEY,
    workspace_id        uuid        NOT NULL,
    version             integer     NOT NULL DEFAULT 1,
    category            text        NOT NULL CHECK (category IN (
                            'company_profile', 'offering', 'audience', 'brand_rule',
                            'positioning', 'strategic_goal', 'channel', 'competitor',
                            'company_fact')),
    title               text        NOT NULL,
    content             jsonb       NOT NULL DEFAULT '{}'::jsonb,
    lifecycle           text        NOT NULL DEFAULT 'current',
    epistemic_kind      text        NOT NULL,
    approval_status     text        NOT NULL,
    verification_status text        NOT NULL DEFAULT 'unverified',
    provenance          jsonb       NOT NULL DEFAULT '{}'::jsonb,
    observed_at         timestamptz,
    deletion_generation bigint      NOT NULL DEFAULT 0,
    retrieval_eligible  boolean     NOT NULL DEFAULT false
);

CREATE TABLE dev_brain.relationships (
    relationship_id     uuid        PRIMARY KEY,
    workspace_id        uuid        NOT NULL,
    source_item_id      uuid        NOT NULL REFERENCES dev_brain.items (item_id),
    target_item_id      uuid        NOT NULL REFERENCES dev_brain.items (item_id),
    relation_type       text        NOT NULL,
    version             integer     NOT NULL DEFAULT 1,
    lifecycle           text        NOT NULL DEFAULT 'current',
    provenance          jsonb       NOT NULL DEFAULT '{}'::jsonb,
    deletion_generation bigint      NOT NULL DEFAULT 0,
    retrieval_eligible  boolean     NOT NULL DEFAULT false
);

CREATE TABLE dev_brain.procedural_rules (
    rule_id             uuid        PRIMARY KEY,
    workspace_id        uuid        NOT NULL,
    version             integer     NOT NULL DEFAULT 1,
    rule_text           text        NOT NULL,
    lifecycle           text        NOT NULL DEFAULT 'current',
    provenance          jsonb       NOT NULL DEFAULT '{}'::jsonb,
    deletion_generation bigint      NOT NULL DEFAULT 0,
    adopted             boolean     NOT NULL DEFAULT false
);

-- Workspace isolation: rows are visible only when app.workspace_id matches. With
-- no setting, nothing is visible.
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['items', 'relationships', 'procedural_rules'] LOOP
        EXECUTE format('ALTER TABLE dev_brain.%I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE dev_brain.%I FORCE ROW LEVEL SECURITY', t);
        EXECUTE format(
            'CREATE POLICY workspace_isolation ON dev_brain.%I USING '
            '(workspace_id = nullif(current_setting(''app.workspace_id'', true), '''')::uuid)',
            t);
    END LOOP;
END $$;

-- brain_read: the contract busmora-ai reads ------------------------------------
CREATE SCHEMA brain_read AUTHORIZATION dev_brain_owner;

-- Eligible = current and retrieval-eligible. Pending, rejected, retired,
-- superseded and deleted items never appear (FR-08, FR-11, FR-42).
CREATE VIEW brain_read.eligible_items_v1 AS
    SELECT item_id, workspace_id, version, category, title, content,
           epistemic_kind, approval_status, verification_status,
           provenance, observed_at, deletion_generation
    FROM dev_brain.items
    WHERE lifecycle = 'current' AND retrieval_eligible;

-- A relationship is eligible only if it and both endpoints are eligible.
CREATE VIEW brain_read.eligible_relationships_v1 AS
    SELECT r.relationship_id, r.workspace_id, r.source_item_id, r.target_item_id,
           r.relation_type, r.version, r.provenance, r.deletion_generation
    FROM dev_brain.relationships r
    JOIN dev_brain.items s ON s.item_id = r.source_item_id
                          AND s.lifecycle = 'current' AND s.retrieval_eligible
    JOIN dev_brain.items t ON t.item_id = r.target_item_id
                          AND t.lifecycle = 'current' AND t.retrieval_eligible
    WHERE r.lifecycle = 'current' AND r.retrieval_eligible;

CREATE VIEW brain_read.adopted_rules_v1 AS
    SELECT rule_id, workspace_id, version, rule_text, provenance, deletion_generation
    FROM dev_brain.procedural_rules
    WHERE lifecycle = 'current' AND adopted;

RESET ROLE;

-- Grants: the AI role reads the views only, never the base tables ---------------
GRANT USAGE ON SCHEMA brain_read TO busmora_ai;
GRANT SELECT ON ALL TABLES IN SCHEMA brain_read TO busmora_ai;
REVOKE ALL ON SCHEMA dev_brain FROM busmora_ai;
