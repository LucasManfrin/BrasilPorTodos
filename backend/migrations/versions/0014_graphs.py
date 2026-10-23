"""Immutable graph versions, authorized reviews and explicit publications."""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE graph_collections (
	author_id UUID NOT NULL, 
	is_example BOOLEAN DEFAULT false NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_collections PRIMARY KEY (id), 
	CONSTRAINT fk_graph_collections_author_id_users FOREIGN KEY(author_id) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_graph_collections_author_id ON graph_collections (author_id)
    """)
    op.execute("""
CREATE TABLE graph_edges (
	author_id UUID NOT NULL, 
	is_example BOOLEAN DEFAULT false NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_edges PRIMARY KEY (id), 
	CONSTRAINT fk_graph_edges_author_id_users FOREIGN KEY(author_id) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_graph_edges_author_id ON graph_edges (author_id)
    """)
    op.execute("""
CREATE TABLE graph_nodes (
	author_id UUID NOT NULL, 
	is_example BOOLEAN DEFAULT false NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_nodes PRIMARY KEY (id), 
	CONSTRAINT fk_graph_nodes_author_id_users FOREIGN KEY(author_id) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_graph_nodes_author_id ON graph_nodes (author_id)
    """)
    op.execute("""
CREATE TABLE graph_collection_versions (
	graph_id UUID NOT NULL, 
	version_number INTEGER NOT NULL, 
	created_by UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	node_version_ids UUID[] NOT NULL, 
	edge_version_ids UUID[] NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_collection_versions PRIMARY KEY (id), 
	CONSTRAINT uq_graph_collection_version_number UNIQUE (graph_id, version_number), 
	CONSTRAINT uq_graph_collection_version_hash UNIQUE (id, content_hash), 
	CONSTRAINT ck_graph_collection_versions_version_number CHECK (version_number > 0), 
	CONSTRAINT ck_graph_collection_versions_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT ck_graph_collection_versions_payload_object CHECK (jsonb_typeof(payload) = 'object'), 
	CONSTRAINT ck_graph_collection_versions_node_limit CHECK (cardinality(node_version_ids) <= 200), 
	CONSTRAINT ck_graph_collection_versions_edge_limit CHECK (cardinality(edge_version_ids) <= 400), 
	CONSTRAINT fk_graph_collection_versions_graph_id_graph_collections FOREIGN KEY(graph_id) REFERENCES graph_collections (id), 
	CONSTRAINT fk_graph_collection_versions_created_by_users FOREIGN KEY(created_by) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_graph_collection_versions_graph_id ON graph_collection_versions (graph_id)
    """)
    op.execute("""
CREATE TABLE graph_node_versions (
	node_id UUID NOT NULL, 
	version_number INTEGER NOT NULL, 
	created_by UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_node_versions PRIMARY KEY (id), 
	CONSTRAINT uq_graph_node_version_number UNIQUE (node_id, version_number), 
	CONSTRAINT uq_graph_node_version_hash UNIQUE (id, content_hash), 
	CONSTRAINT ck_graph_node_versions_version_number CHECK (version_number > 0), 
	CONSTRAINT ck_graph_node_versions_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT ck_graph_node_versions_payload_object CHECK (jsonb_typeof(payload) = 'object'), 
	CONSTRAINT fk_graph_node_versions_node_id_graph_nodes FOREIGN KEY(node_id) REFERENCES graph_nodes (id), 
	CONSTRAINT fk_graph_node_versions_created_by_users FOREIGN KEY(created_by) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_graph_node_versions_node_id ON graph_node_versions (node_id)
    """)
    op.execute("""
CREATE TABLE graph_collection_publications (
	graph_version_id UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	published_by UUID NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_collection_publications PRIMARY KEY (id), 
	CONSTRAINT uq_graph_collection_publication_version UNIQUE (graph_version_id), 
	CONSTRAINT fk_graph_collection_publication_version_hash FOREIGN KEY(graph_version_id, content_hash) REFERENCES graph_collection_versions (id, content_hash), 
	CONSTRAINT ck_graph_collection_publications_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT fk_graph_collection_publications_published_by_users FOREIGN KEY(published_by) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE TABLE graph_edge_versions (
	edge_id UUID NOT NULL, 
	version_number INTEGER NOT NULL, 
	created_by UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	from_node_version_id UUID NOT NULL, 
	to_node_version_id UUID NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_edge_versions PRIMARY KEY (id), 
	CONSTRAINT uq_graph_edge_version_number UNIQUE (edge_id, version_number), 
	CONSTRAINT uq_graph_edge_version_hash UNIQUE (id, content_hash), 
	CONSTRAINT ck_graph_edge_versions_version_number CHECK (version_number > 0), 
	CONSTRAINT ck_graph_edge_versions_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT ck_graph_edge_versions_payload_object CHECK (jsonb_typeof(payload) = 'object'), 
	CONSTRAINT ck_graph_edge_versions_distinct_nodes CHECK (from_node_version_id <> to_node_version_id), 
	CONSTRAINT fk_graph_edge_versions_edge_id_graph_edges FOREIGN KEY(edge_id) REFERENCES graph_edges (id), 
	CONSTRAINT fk_graph_edge_versions_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), 
	CONSTRAINT fk_graph_edge_versions_from_node_version_id_graph_node_versions FOREIGN KEY(from_node_version_id) REFERENCES graph_node_versions (id), 
	CONSTRAINT fk_graph_edge_versions_to_node_version_id_graph_node_versions FOREIGN KEY(to_node_version_id) REFERENCES graph_node_versions (id)
)
    """)
    op.execute("""
CREATE INDEX ix_graph_edge_versions_edge_id ON graph_edge_versions (edge_id)
    """)
    op.execute("""
CREATE TABLE graph_edge_reviews (
	edge_version_id UUID NOT NULL, 
	review_number INTEGER NOT NULL, 
	reviewer_id UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	decision VARCHAR(20) NOT NULL, 
	payload JSONB NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_edge_reviews PRIMARY KEY (id), 
	CONSTRAINT uq_graph_edge_review_number UNIQUE (edge_version_id, review_number), 
	CONSTRAINT uq_graph_edge_review_target UNIQUE (id, edge_version_id, content_hash), 
	CONSTRAINT fk_graph_edge_review_version_hash FOREIGN KEY(edge_version_id, content_hash) REFERENCES graph_edge_versions (id, content_hash), 
	CONSTRAINT ck_graph_edge_reviews_review_number CHECK (review_number > 0), 
	CONSTRAINT ck_graph_edge_reviews_decision CHECK (decision IN ('ACCEPT','REQUEST_CHANGES','DISPUTE','REJECT')), 
	CONSTRAINT ck_graph_edge_reviews_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT ck_graph_edge_reviews_payload_object CHECK (jsonb_typeof(payload) = 'object'), 
	CONSTRAINT fk_graph_edge_reviews_reviewer_id_users FOREIGN KEY(reviewer_id) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE INDEX ix_graph_edge_reviews_edge_version_id ON graph_edge_reviews (edge_version_id)
    """)
    op.execute("""
CREATE TABLE graph_edge_publications (
	edge_version_id UUID NOT NULL, 
	review_id UUID NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	published_by UUID NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	published_state VARCHAR(12) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_graph_edge_publications PRIMARY KEY (id), 
	CONSTRAINT uq_graph_edge_publication_version UNIQUE (edge_version_id), 
	CONSTRAINT fk_graph_edge_publication_version_hash FOREIGN KEY(edge_version_id, content_hash) REFERENCES graph_edge_versions (id, content_hash), 
	CONSTRAINT fk_graph_edge_publication_review_target FOREIGN KEY(review_id, edge_version_id, content_hash) REFERENCES graph_edge_reviews (id, edge_version_id, content_hash), 
	CONSTRAINT ck_graph_edge_publications_content_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'), 
	CONSTRAINT ck_graph_edge_publications_published_state CHECK (published_state IN ('REVIEWED','DISPUTED')), 
	CONSTRAINT fk_graph_edge_publications_published_by_users FOREIGN KEY(published_by) REFERENCES users (id)
)
    """)
    op.execute("""
CREATE FUNCTION bpt_graph_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Graph records are append-only' USING ERRCODE='23514';
END; $$;

CREATE FUNCTION bpt_graph_node_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE identity_row graph_nodes%ROWTYPE;
BEGIN
    SELECT * INTO identity_row FROM graph_nodes WHERE id=NEW.node_id FOR UPDATE;
    IF identity_row.id IS NULL
       OR NEW.created_by IS DISTINCT FROM identity_row.author_id
       OR NEW.payload->>'id' IS DISTINCT FROM 'node-' || replace(identity_row.id::text,'-','')
       OR (NEW.payload->>'revision')::integer IS DISTINCT FROM NEW.version_number
       OR NEW.version_number IS DISTINCT FROM (SELECT COALESCE(max(version_number),0)+1 FROM graph_node_versions WHERE node_id=NEW.node_id)
       OR NEW.created_at < identity_row.created_at
    THEN RAISE EXCEPTION 'Invalid graph node version identity' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER graph_node_version_insert BEFORE INSERT ON graph_node_versions
FOR EACH ROW EXECUTE FUNCTION bpt_graph_node_version_insert();

CREATE FUNCTION bpt_graph_edge_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE identity_row graph_edges%ROWTYPE; origin graph_node_versions%ROWTYPE; destination graph_node_versions%ROWTYPE;
BEGIN
    SELECT * INTO identity_row FROM graph_edges WHERE id=NEW.edge_id FOR UPDATE;
    SELECT * INTO origin FROM graph_node_versions WHERE id=NEW.from_node_version_id FOR SHARE;
    SELECT * INTO destination FROM graph_node_versions WHERE id=NEW.to_node_version_id FOR SHARE;
    IF identity_row.id IS NULL OR origin.id IS NULL OR destination.id IS NULL
       OR origin.node_id=destination.node_id
       OR NEW.created_by IS DISTINCT FROM identity_row.author_id
       OR NEW.payload->>'id' IS DISTINCT FROM 'edge-' || replace(identity_row.id::text,'-','')
       OR NEW.payload->>'author_id' IS DISTINCT FROM identity_row.author_id::text
       OR (NEW.payload->>'revision')::integer IS DISTINCT FROM NEW.version_number
       OR NEW.payload->>'contract_version' IS DISTINCT FROM '1.0.0'
       OR (NEW.payload->>'updated_at')::timestamptz IS DISTINCT FROM NEW.created_at
       OR NEW.payload->'from_node' IS DISTINCT FROM origin.payload
       OR NEW.payload->'to_node' IS DISTINCT FROM destination.payload
       OR NEW.version_number IS DISTINCT FROM (SELECT COALESCE(max(version_number),0)+1 FROM graph_edge_versions WHERE edge_id=NEW.edge_id)
       OR NEW.created_at < greatest(identity_row.created_at,origin.created_at,destination.created_at)
       OR (NOT identity_row.is_example AND EXISTS(SELECT 1 FROM graph_nodes WHERE id IN(origin.node_id,destination.node_id) AND is_example))
    THEN RAISE EXCEPTION 'Invalid graph edge version identity or nodes' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER graph_edge_version_insert BEFORE INSERT ON graph_edge_versions
FOR EACH ROW EXECUTE FUNCTION bpt_graph_edge_version_insert();

CREATE FUNCTION bpt_graph_edge_ready(p jsonb, at_time timestamptz) RETURNS boolean LANGUAGE plpgsql AS $$
BEGIN
    RETURN COALESCE(
       p->>'contract_version'='1.0.0'
       AND (p->>'updated_at')::timestamptz <= at_time
       AND jsonb_typeof(p->'sources')='array' AND jsonb_array_length(p->'sources') BETWEEN 1 AND 32
       AND jsonb_typeof(p->'evidence')='array' AND jsonb_array_length(p->'evidence') BETWEEN 1 AND 64
       AND jsonb_typeof(p->'links')='array' AND jsonb_array_length(p->'links') BETWEEN 1 AND 64
       AND EXISTS(SELECT 1 FROM jsonb_array_elements(p->'links') item WHERE item->>'relation'='SUPPORTS')
       AND jsonb_array_length(p->'premises') > 0
       AND jsonb_array_length(p->'limitations') > 0
       AND jsonb_array_length(p->'unknowns') > 0
       AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(p->'sources') item
           WHERE item->>'consulted_at' IS NULL
              OR (item->>'consulted_at')::timestamptz > (p->>'updated_at')::timestamptz
              OR (item->>'published_date')::date > ((item->>'consulted_at')::timestamptz AT TIME ZONE 'UTC')::date)
       AND p->>'counterpoint_status' IN ('NOT_RESEARCHED','NOT_FOUND','DOCUMENTED')
       AND NOT(p->>'consensus' IN ('ESTABLISHED','DEBATED') AND p->>'counterpoint_status'='NOT_RESEARCHED')
       AND ((p->>'counterpoint_status'='DOCUMENTED') = EXISTS(SELECT 1 FROM jsonb_array_elements(p->'links') item WHERE item->>'relation'='CHALLENGES'))
       AND (p->>'counterpoint_status'<>'NOT_FOUND' OR (
           length(btrim(p->>'counterargument_note')) > 0
           AND jsonb_array_length(p->'counterpoint_search_notes') > 0
           AND p->>'counterpoint_searched_at' IS NOT NULL))
       AND (p->>'counterpoint_searched_at' IS NULL OR (p->>'counterpoint_searched_at')::timestamptz <= (p->>'updated_at')::timestamptz), false);
END; $$;

CREATE FUNCTION bpt_graph_edge_review_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target graph_edge_versions%ROWTYPE; identity_row graph_edges%ROWTYPE; reviewer users%ROWTYPE;
BEGIN
    SELECT * INTO target FROM graph_edge_versions WHERE id=NEW.edge_version_id;
    SELECT * INTO identity_row FROM graph_edges WHERE id=target.edge_id FOR UPDATE;
    SELECT * INTO reviewer FROM users WHERE id=NEW.reviewer_id FOR SHARE;
    IF target.id IS NULL OR identity_row.id IS NULL
       OR reviewer.id IS NULL OR NOT reviewer.is_active OR reviewer.role <> 'ADMIN'
       OR reviewer.id=identity_row.author_id
       OR target.version_number IS DISTINCT FROM (SELECT max(version_number) FROM graph_edge_versions WHERE edge_id=target.edge_id)
       OR EXISTS(SELECT 1 FROM graph_edge_publications WHERE edge_version_id=target.id)
       OR NEW.review_number IS DISTINCT FROM (SELECT COALESCE(max(review_number),0)+1 FROM graph_edge_reviews WHERE edge_version_id=target.id)
       OR NEW.payload->>'edge_id' IS DISTINCT FROM target.payload->>'id'
       OR (NEW.payload->>'edge_revision')::integer IS DISTINCT FROM target.version_number
       OR NEW.payload->>'content_hash' IS DISTINCT FROM target.content_hash
       OR NEW.content_hash IS DISTINCT FROM target.content_hash
       OR NEW.payload->>'reviewer_id' IS DISTINCT FROM reviewer.id::text
       OR NEW.payload->>'decision' IS DISTINCT FROM NEW.decision
       OR NEW.payload->>'contract_version' IS DISTINCT FROM '1.0.0'
       OR (NEW.payload->>'reviewed_at')::timestamptz IS DISTINCT FROM NEW.created_at
       OR NEW.created_at < target.created_at
       OR jsonb_typeof(NEW.payload->'references_checked') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(NEW.payload->'scopes_checked') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(NEW.payload->'counterpoints_checked') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(NEW.payload->'limitations_checked') IS DISTINCT FROM 'boolean'
       OR COALESCE(length(btrim(NEW.payload->>'rationale')),0)=0
    THEN RAISE EXCEPTION 'Invalid graph edge review' USING ERRCODE='23514'; END IF;
    IF NEW.decision IN('ACCEPT','DISPUTE') AND (
        NEW.payload->'references_checked' IS DISTINCT FROM 'true'::jsonb OR
        NEW.payload->'scopes_checked' IS DISTINCT FROM 'true'::jsonb OR
        NEW.payload->'counterpoints_checked' IS DISTINCT FROM 'true'::jsonb OR
        NEW.payload->'limitations_checked' IS DISTINCT FROM 'true'::jsonb OR
        NOT bpt_graph_edge_ready(target.payload,NEW.created_at)
    ) THEN RAISE EXCEPTION 'Incomplete graph edge review checklist or content' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER graph_edge_review_insert BEFORE INSERT ON graph_edge_reviews
FOR EACH ROW EXECUTE FUNCTION bpt_graph_edge_review_insert();

CREATE FUNCTION bpt_graph_edge_publication_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target graph_edge_versions%ROWTYPE; identity_row graph_edges%ROWTYPE; reviewed graph_edge_reviews%ROWTYPE; reviewer users%ROWTYPE; author_row users%ROWTYPE;
BEGIN
    SELECT * INTO target FROM graph_edge_versions WHERE id=NEW.edge_version_id;
    SELECT * INTO identity_row FROM graph_edges WHERE id=target.edge_id FOR UPDATE;
    SELECT * INTO reviewed FROM graph_edge_reviews WHERE id=NEW.review_id;
    SELECT * INTO reviewer FROM users WHERE id=reviewed.reviewer_id FOR SHARE;
    SELECT * INTO author_row FROM users WHERE id=identity_row.author_id FOR SHARE;
    IF target.id IS NULL OR identity_row.id IS NULL OR reviewed.id IS NULL
       OR reviewed.decision NOT IN('ACCEPT','DISPUTE')
       OR NEW.published_state IS DISTINCT FROM (CASE WHEN reviewed.decision='ACCEPT' THEN 'REVIEWED' ELSE 'DISPUTED' END)
       OR reviewed.edge_version_id IS DISTINCT FROM target.id
       OR reviewed.content_hash IS DISTINCT FROM target.content_hash
       OR NEW.content_hash IS DISTINCT FROM target.content_hash
       OR reviewed.review_number IS DISTINCT FROM (SELECT max(review_number) FROM graph_edge_reviews WHERE edge_version_id=target.id)
       OR target.version_number IS DISTINCT FROM (SELECT max(version_number) FROM graph_edge_versions WHERE edge_id=target.edge_id)
       OR reviewer.id IS NULL OR NOT reviewer.is_active OR reviewer.role <> 'ADMIN'
       OR reviewer.id=identity_row.author_id
       OR author_row.id IS NULL OR NOT author_row.is_active
       OR NEW.published_by IS DISTINCT FROM identity_row.author_id
       OR NEW.published_at < greatest(reviewed.created_at,target.created_at)
       OR NEW.published_at IS DISTINCT FROM NEW.created_at
       OR reviewed.payload->'references_checked' IS DISTINCT FROM 'true'::jsonb
       OR reviewed.payload->'scopes_checked' IS DISTINCT FROM 'true'::jsonb
       OR reviewed.payload->'counterpoints_checked' IS DISTINCT FROM 'true'::jsonb
       OR reviewed.payload->'limitations_checked' IS DISTINCT FROM 'true'::jsonb
       OR NOT bpt_graph_edge_ready(target.payload,NEW.published_at)
       OR (NOT identity_row.is_example AND EXISTS(SELECT 1 FROM jsonb_array_elements(target.payload->'sources') item JOIN sources s ON s.id=(item->>'id')::uuid WHERE s.is_example))
    THEN RAISE EXCEPTION 'Graph edge publication requires current authorized review' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER graph_edge_publication_insert BEFORE INSERT ON graph_edge_publications
FOR EACH ROW EXECUTE FUNCTION bpt_graph_edge_publication_insert();

CREATE FUNCTION bpt_graph_collection_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE identity_row graph_collections%ROWTYPE; node_row graph_node_versions%ROWTYPE; edge_row graph_edge_versions%ROWTYPE; selected_id uuid; position integer; seen_nodes uuid[] := '{}'; seen_edges uuid[] := '{}';
BEGIN
    SELECT * INTO identity_row FROM graph_collections WHERE id=NEW.graph_id FOR UPDATE;
    IF identity_row.id IS NULL
       OR NEW.created_by IS DISTINCT FROM identity_row.author_id
       OR NEW.payload->>'id' IS DISTINCT FROM identity_row.id::text
       OR NEW.payload->>'author_id' IS DISTINCT FROM identity_row.author_id::text
       OR (NEW.payload->>'revision')::integer IS DISTINCT FROM NEW.version_number
       OR NEW.payload->>'contract_version' IS DISTINCT FROM '1.0.0'
       OR (NEW.payload->>'updated_at')::timestamptz IS DISTINCT FROM NEW.created_at
       OR NEW.version_number IS DISTINCT FROM (SELECT COALESCE(max(version_number),0)+1 FROM graph_collection_versions WHERE graph_id=NEW.graph_id)
       OR NEW.created_at < identity_row.created_at
       OR jsonb_typeof(NEW.payload->'nodes') IS DISTINCT FROM 'array'
       OR jsonb_typeof(NEW.payload->'edges') IS DISTINCT FROM 'array'
       OR jsonb_array_length(NEW.payload->'nodes') IS DISTINCT FROM cardinality(NEW.node_version_ids)
       OR jsonb_array_length(NEW.payload->'edges') IS DISTINCT FROM cardinality(NEW.edge_version_ids)
    THEN RAISE EXCEPTION 'Invalid graph collection version identity' USING ERRCODE='23514'; END IF;
    position := 0;
    FOREACH selected_id IN ARRAY NEW.node_version_ids LOOP
        SELECT * INTO node_row FROM graph_node_versions WHERE id=selected_id FOR SHARE;
        IF node_row.id IS NULL OR node_row.node_id=ANY(seen_nodes)
           OR NEW.payload->'nodes'->position IS DISTINCT FROM node_row.payload
           OR NEW.created_at < node_row.created_at
           OR (NOT identity_row.is_example AND EXISTS(SELECT 1 FROM graph_nodes WHERE id=node_row.node_id AND is_example))
        THEN RAISE EXCEPTION 'Invalid graph collection node snapshot' USING ERRCODE='23514'; END IF;
        seen_nodes := array_append(seen_nodes,node_row.node_id);
        position := position+1;
    END LOOP;
    position := 0;
    FOREACH selected_id IN ARRAY NEW.edge_version_ids LOOP
        SELECT * INTO edge_row FROM graph_edge_versions WHERE id=selected_id FOR SHARE;
        IF edge_row.id IS NULL OR edge_row.edge_id=ANY(seen_edges)
           OR NEW.payload->'edges'->position IS DISTINCT FROM edge_row.payload
           OR NEW.created_at < edge_row.created_at
           OR NOT(edge_row.from_node_version_id=ANY(NEW.node_version_ids))
           OR NOT(edge_row.to_node_version_id=ANY(NEW.node_version_ids))
           OR (NOT identity_row.is_example AND EXISTS(SELECT 1 FROM graph_edges WHERE id=edge_row.edge_id AND is_example))
        THEN RAISE EXCEPTION 'Invalid graph collection edge snapshot' USING ERRCODE='23514'; END IF;
        seen_edges := array_append(seen_edges,edge_row.edge_id);
        position := position+1;
    END LOOP;
    RETURN NEW;
END; $$;
CREATE TRIGGER graph_collection_version_insert BEFORE INSERT ON graph_collection_versions
FOR EACH ROW EXECUTE FUNCTION bpt_graph_collection_version_insert();

CREATE FUNCTION bpt_graph_collection_publication_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target graph_collection_versions%ROWTYPE; identity_row graph_collections%ROWTYPE; author_row users%ROWTYPE;
BEGIN
    SELECT * INTO target FROM graph_collection_versions WHERE id=NEW.graph_version_id;
    SELECT * INTO identity_row FROM graph_collections WHERE id=target.graph_id FOR UPDATE;
    SELECT * INTO author_row FROM users WHERE id=identity_row.author_id FOR SHARE;
    IF target.id IS NULL OR identity_row.id IS NULL
       OR NEW.content_hash IS DISTINCT FROM target.content_hash
       OR target.version_number IS DISTINCT FROM (SELECT max(version_number) FROM graph_collection_versions WHERE graph_id=target.graph_id)
       OR author_row.id IS NULL OR NOT author_row.is_active
       OR NEW.published_by IS DISTINCT FROM identity_row.author_id
       OR NEW.published_at < target.created_at
       OR NEW.published_at IS DISTINCT FROM NEW.created_at
       OR cardinality(target.edge_version_ids)=0
       OR EXISTS(SELECT 1 FROM unnest(target.edge_version_ids) selected_id
           WHERE NOT EXISTS(SELECT 1 FROM graph_edge_publications p WHERE p.edge_version_id=selected_id AND p.published_at <= NEW.published_at))
       OR EXISTS(SELECT 1 FROM unnest(target.node_version_ids) selected_id
           WHERE NOT EXISTS(SELECT 1 FROM graph_edge_versions e JOIN graph_edge_publications p ON p.edge_version_id=e.id
               JOIN graph_edges witness ON witness.id=e.edge_id
               WHERE selected_id IN(e.from_node_version_id,e.to_node_version_id) AND p.published_at <= NEW.published_at
                 AND (identity_row.is_example OR NOT witness.is_example)))
       OR (NOT identity_row.is_example AND EXISTS(SELECT 1 FROM graph_edge_versions e
           CROSS JOIN LATERAL jsonb_array_elements(e.payload->'sources') item JOIN sources s ON s.id=(item->>'id')::uuid
           WHERE e.id=ANY(target.edge_version_ids) AND s.is_example))
    THEN RAISE EXCEPTION 'Graph publication requires public reviewed dependencies' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER graph_collection_publication_insert BEFORE INSERT ON graph_collection_publications
FOR EACH ROW EXECUTE FUNCTION bpt_graph_collection_publication_insert();

    """)
    op.execute("""
CREATE TRIGGER frozen_graph_collections BEFORE UPDATE OR DELETE ON graph_collections FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_edges BEFORE UPDATE OR DELETE ON graph_edges FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_nodes BEFORE UPDATE OR DELETE ON graph_nodes FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_collection_versions BEFORE UPDATE OR DELETE ON graph_collection_versions FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_node_versions BEFORE UPDATE OR DELETE ON graph_node_versions FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_collection_publications BEFORE UPDATE OR DELETE ON graph_collection_publications FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_edge_versions BEFORE UPDATE OR DELETE ON graph_edge_versions FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_edge_reviews BEFORE UPDATE OR DELETE ON graph_edge_reviews FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)
    op.execute("""
CREATE TRIGGER frozen_graph_edge_publications BEFORE UPDATE OR DELETE ON graph_edge_publications FOR EACH ROW EXECUTE FUNCTION bpt_graph_append_only();
    """)


def downgrade():
    op.drop_table("graph_edge_publications")
    op.drop_table("graph_edge_reviews")
    op.drop_table("graph_edge_versions")
    op.drop_table("graph_collection_publications")
    op.drop_table("graph_node_versions")
    op.drop_table("graph_collection_versions")
    op.drop_table("graph_nodes")
    op.drop_table("graph_edges")
    op.drop_table("graph_collections")
    op.execute("DROP FUNCTION bpt_graph_collection_publication_insert()")
    op.execute("DROP FUNCTION bpt_graph_collection_version_insert()")
    op.execute("DROP FUNCTION bpt_graph_edge_publication_insert()")
    op.execute("DROP FUNCTION bpt_graph_edge_review_insert()")
    op.execute("DROP FUNCTION bpt_graph_edge_ready(jsonb, timestamptz)")
    op.execute("DROP FUNCTION bpt_graph_edge_version_insert()")
    op.execute("DROP FUNCTION bpt_graph_node_version_insert()")
    op.execute("DROP FUNCTION bpt_graph_append_only()")
