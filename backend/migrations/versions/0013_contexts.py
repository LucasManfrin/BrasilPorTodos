"""Immutable context versions, trusted human reviews and publications."""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE contexts (
	author_id UUID NOT NULL, 
	is_example BOOLEAN DEFAULT false NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_contexts PRIMARY KEY (id), 
	CONSTRAINT fk_contexts_author_id_users FOREIGN KEY(author_id) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_contexts_author_id ON contexts (author_id)
    """)
    op.execute("""
CREATE TABLE context_versions (
	context_id UUID NOT NULL, 
	version_number INTEGER NOT NULL, 
	created_by UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_context_versions PRIMARY KEY (id), 
	CONSTRAINT uq_context_version_number UNIQUE (context_id, version_number), 
	CONSTRAINT uq_context_version_hash UNIQUE (id, content_hash), 
	CONSTRAINT ck_context_versions_version_number CHECK (version_number > 0), 
	CONSTRAINT ck_context_versions_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT ck_context_versions_payload_object CHECK (jsonb_typeof(payload) = 'object'), 
	CONSTRAINT fk_context_versions_context_id_contexts FOREIGN KEY(context_id) REFERENCES contexts (id), 
	CONSTRAINT fk_context_versions_created_by_users FOREIGN KEY(created_by) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_context_versions_context_id ON context_versions (context_id)
    """)
    op.execute("""
CREATE TABLE context_reviews (
	context_version_id UUID NOT NULL, 
	review_number INTEGER NOT NULL, 
	reviewer_id UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	decision VARCHAR(20) NOT NULL, 
	payload JSONB NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_context_reviews PRIMARY KEY (id), 
	CONSTRAINT uq_context_review_number UNIQUE (context_version_id, review_number), 
	CONSTRAINT uq_context_review_target UNIQUE (id, context_version_id, content_hash), 
	CONSTRAINT fk_context_review_version_hash FOREIGN KEY(context_version_id, content_hash) REFERENCES context_versions (id, content_hash), 
	CONSTRAINT ck_context_reviews_review_number CHECK (review_number > 0), 
	CONSTRAINT ck_context_reviews_decision CHECK (decision IN ('ACCEPT','REQUEST_CHANGES')), 
	CONSTRAINT ck_context_reviews_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT ck_context_reviews_payload_object CHECK (jsonb_typeof(payload) = 'object'), 
	CONSTRAINT fk_context_reviews_reviewer_id_users FOREIGN KEY(reviewer_id) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_context_reviews_context_version_id ON context_reviews (context_version_id)
    """)
    op.execute("""
CREATE TABLE context_publications (
	context_version_id UUID NOT NULL, 
	review_id UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	published_by UUID NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_context_publications PRIMARY KEY (id), 
	CONSTRAINT uq_context_publication_version UNIQUE (context_version_id), 
	CONSTRAINT fk_context_publication_version_hash FOREIGN KEY(context_version_id, content_hash) REFERENCES context_versions (id, content_hash), 
	CONSTRAINT fk_context_publication_review_target FOREIGN KEY(review_id, context_version_id, content_hash) REFERENCES context_reviews (id, context_version_id, content_hash), 
	CONSTRAINT ck_context_publications_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT fk_context_publications_published_by_users FOREIGN KEY(published_by) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE FUNCTION bpt_context_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE owner_id uuid;
BEGIN
    SELECT author_id INTO owner_id FROM contexts WHERE id=NEW.context_id FOR UPDATE;
    IF NEW.payload->>'id' IS DISTINCT FROM NEW.context_id::text
       OR NEW.payload->>'author_id' IS DISTINCT FROM owner_id::text
       OR (NEW.payload->>'revision')::integer IS DISTINCT FROM NEW.version_number
       OR NEW.payload->>'contract_version' IS DISTINCT FROM '1.0.0'
       OR (NEW.payload->>'updated_at')::timestamptz IS DISTINCT FROM NEW.created_at
       OR NEW.version_number IS DISTINCT FROM (SELECT COALESCE(max(version_number),0)+1 FROM context_versions WHERE context_id=NEW.context_id)
       OR NEW.created_by IS DISTINCT FROM owner_id
    THEN RAISE EXCEPTION 'Invalid context version identity' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER context_version_insert BEFORE INSERT ON context_versions
FOR EACH ROW EXECUTE FUNCTION bpt_context_version_insert();

CREATE FUNCTION bpt_context_review_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target context_versions%ROWTYPE; identity_row contexts%ROWTYPE; reviewer users%ROWTYPE;
BEGIN
    SELECT * INTO target FROM context_versions WHERE id=NEW.context_version_id;
    SELECT * INTO identity_row FROM contexts WHERE id=target.context_id FOR UPDATE;
    SELECT * INTO reviewer FROM users WHERE id=NEW.reviewer_id FOR SHARE;
    IF reviewer.id IS NULL OR NOT reviewer.is_active OR reviewer.role <> 'ADMIN'
       OR reviewer.id=identity_row.author_id
       OR target.version_number IS DISTINCT FROM (SELECT max(version_number) FROM context_versions WHERE context_id=target.context_id)
       OR EXISTS(SELECT 1 FROM context_publications WHERE context_version_id=target.id)
       OR NEW.review_number IS DISTINCT FROM (SELECT COALESCE(max(review_number),0)+1 FROM context_reviews WHERE context_version_id=target.id)
       OR NEW.payload->>'context_id' IS DISTINCT FROM target.context_id::text
       OR (NEW.payload->>'context_revision')::integer IS DISTINCT FROM target.version_number
       OR NEW.payload->>'content_hash' IS DISTINCT FROM target.content_hash
       OR NEW.content_hash IS DISTINCT FROM target.content_hash
       OR NEW.payload->>'reviewer_id' IS DISTINCT FROM reviewer.id::text
       OR NEW.payload->>'decision' IS DISTINCT FROM NEW.decision
       OR NEW.payload->>'contract_version' IS DISTINCT FROM '1.0.0'
       OR (NEW.payload->>'reviewed_at')::timestamptz IS DISTINCT FROM NEW.created_at
       OR NEW.created_at < target.created_at
       OR jsonb_typeof(NEW.payload->'references_checked') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(NEW.payload->'scopes_checked') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(NEW.payload->'alternatives_checked') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(NEW.payload->'limitations_checked') IS DISTINCT FROM 'boolean'
       OR COALESCE(length(btrim(NEW.payload->>'rationale')),0)=0
    THEN RAISE EXCEPTION 'Invalid context review' USING ERRCODE='23514'; END IF;
    IF NEW.decision='ACCEPT' AND (
        NEW.payload->'references_checked' IS DISTINCT FROM 'true'::jsonb OR
        NEW.payload->'scopes_checked' IS DISTINCT FROM 'true'::jsonb OR
        NEW.payload->'alternatives_checked' IS DISTINCT FROM 'true'::jsonb OR
        NEW.payload->'limitations_checked' IS DISTINCT FROM 'true'::jsonb
    ) THEN RAISE EXCEPTION 'Incomplete context review checklist' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER context_review_insert BEFORE INSERT ON context_reviews
FOR EACH ROW EXECUTE FUNCTION bpt_context_review_insert();

CREATE FUNCTION bpt_context_publication_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target context_versions%ROWTYPE; identity_row contexts%ROWTYPE; accepted context_reviews%ROWTYPE; reviewer users%ROWTYPE; author_row users%ROWTYPE;
BEGIN
    SELECT * INTO target FROM context_versions WHERE id=NEW.context_version_id;
    SELECT * INTO identity_row FROM contexts WHERE id=target.context_id FOR UPDATE;
    SELECT * INTO accepted FROM context_reviews WHERE id=NEW.review_id;
    SELECT * INTO reviewer FROM users WHERE id=accepted.reviewer_id FOR SHARE;
    SELECT * INTO author_row FROM users WHERE id=identity_row.author_id FOR SHARE;
    IF accepted.id IS NULL OR accepted.decision <> 'ACCEPT'
       OR accepted.context_version_id IS DISTINCT FROM target.id
       OR accepted.content_hash IS DISTINCT FROM target.content_hash
       OR NEW.content_hash IS DISTINCT FROM target.content_hash
       OR accepted.review_number IS DISTINCT FROM (SELECT max(review_number) FROM context_reviews WHERE context_version_id=target.id)
       OR target.version_number IS DISTINCT FROM (SELECT max(version_number) FROM context_versions WHERE context_id=target.context_id)
       OR reviewer.id IS NULL OR NOT reviewer.is_active OR reviewer.role <> 'ADMIN'
       OR reviewer.id=identity_row.author_id
       OR author_row.id IS NULL OR NOT author_row.is_active
       OR NEW.published_by IS DISTINCT FROM identity_row.author_id
       OR NEW.published_at < accepted.created_at
       OR NEW.published_at IS DISTINCT FROM NEW.created_at
       OR accepted.payload->'references_checked' IS DISTINCT FROM 'true'::jsonb
       OR accepted.payload->'scopes_checked' IS DISTINCT FROM 'true'::jsonb
       OR accepted.payload->'alternatives_checked' IS DISTINCT FROM 'true'::jsonb
       OR accepted.payload->'limitations_checked' IS DISTINCT FROM 'true'::jsonb
    THEN RAISE EXCEPTION 'Context publication requires current authorized acceptance' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER context_publication_insert BEFORE INSERT ON context_publications
FOR EACH ROW EXECUTE FUNCTION bpt_context_publication_insert();
    """)
    op.execute("""
CREATE TRIGGER frozen_contexts BEFORE UPDATE OR DELETE ON contexts FOR EACH ROW EXECUTE FUNCTION bpt_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_context_versions BEFORE UPDATE OR DELETE ON context_versions FOR EACH ROW EXECUTE FUNCTION bpt_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_context_reviews BEFORE UPDATE OR DELETE ON context_reviews FOR EACH ROW EXECUTE FUNCTION bpt_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_context_publications BEFORE UPDATE OR DELETE ON context_publications FOR EACH ROW EXECUTE FUNCTION bpt_append_only();
    """)


def downgrade():
    op.drop_table("context_publications")
    op.drop_table("context_reviews")
    op.drop_table("context_versions")
    op.drop_table("contexts")
    op.execute("DROP FUNCTION bpt_context_publication_insert()")
    op.execute("DROP FUNCTION bpt_context_review_insert()")
    op.execute("DROP FUNCTION bpt_context_version_insert()")
