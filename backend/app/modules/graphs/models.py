"""Immutable graph identities, versions, authorized reviews and publications."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import CreatedAt, UUIDPrimaryKey


class GraphNode(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_nodes"
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    is_example: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))


class GraphNodeVersion(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_node_versions"
    __table_args__ = (
        UniqueConstraint("node_id", "version_number", name="uq_graph_node_version_number"),
        UniqueConstraint("id", "content_hash", name="uq_graph_node_version_hash"),
        CheckConstraint("version_number > 0", name="version_number"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
    )
    node_id: Mapped[UUID] = mapped_column(ForeignKey("graph_nodes.id"), index=True)
    version_number: Mapped[int]
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB)


class GraphEdge(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_edges"
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    is_example: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))


class GraphEdgeVersion(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_edge_versions"
    __table_args__ = (
        UniqueConstraint("edge_id", "version_number", name="uq_graph_edge_version_number"),
        UniqueConstraint("id", "content_hash", name="uq_graph_edge_version_hash"),
        CheckConstraint("version_number > 0", name="version_number"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
        CheckConstraint("from_node_version_id <> to_node_version_id", name="distinct_nodes"),
    )
    edge_id: Mapped[UUID] = mapped_column(ForeignKey("graph_edges.id"), index=True)
    version_number: Mapped[int]
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB)
    from_node_version_id: Mapped[UUID] = mapped_column(ForeignKey("graph_node_versions.id"))
    to_node_version_id: Mapped[UUID] = mapped_column(ForeignKey("graph_node_versions.id"))


class GraphEdgeReview(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_edge_reviews"
    __table_args__ = (
        UniqueConstraint("edge_version_id", "review_number", name="uq_graph_edge_review_number"),
        UniqueConstraint(
            "id", "edge_version_id", "content_hash", name="uq_graph_edge_review_target"
        ),
        ForeignKeyConstraint(
            ["edge_version_id", "content_hash"],
            ["graph_edge_versions.id", "graph_edge_versions.content_hash"],
            name="fk_graph_edge_review_version_hash",
        ),
        CheckConstraint("review_number > 0", name="review_number"),
        CheckConstraint(
            "decision IN ('ACCEPT','REQUEST_CHANGES','DISPUTE','REJECT')", name="decision"
        ),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
    )
    edge_version_id: Mapped[UUID] = mapped_column(index=True)
    review_number: Mapped[int]
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSONB)


class GraphEdgePublication(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_edge_publications"
    __table_args__ = (
        UniqueConstraint("edge_version_id", name="uq_graph_edge_publication_version"),
        ForeignKeyConstraint(
            ["edge_version_id", "content_hash"],
            ["graph_edge_versions.id", "graph_edge_versions.content_hash"],
            name="fk_graph_edge_publication_version_hash",
        ),
        ForeignKeyConstraint(
            ["review_id", "edge_version_id", "content_hash"],
            [
                "graph_edge_reviews.id",
                "graph_edge_reviews.edge_version_id",
                "graph_edge_reviews.content_hash",
            ],
            name="fk_graph_edge_publication_review_target",
        ),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
        CheckConstraint("published_state IN ('REVIEWED','DISPUTED')", name="published_state"),
    )
    edge_version_id: Mapped[UUID]
    review_id: Mapped[UUID]
    content_hash: Mapped[str] = mapped_column(String(64))
    published_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_state: Mapped[str] = mapped_column(String(12))


class GraphCollection(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_collections"
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    is_example: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))


class GraphCollectionVersion(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_collection_versions"
    __table_args__ = (
        UniqueConstraint("graph_id", "version_number", name="uq_graph_collection_version_number"),
        UniqueConstraint("id", "content_hash", name="uq_graph_collection_version_hash"),
        CheckConstraint("version_number > 0", name="version_number"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
        CheckConstraint("cardinality(node_version_ids) <= 200", name="node_limit"),
        CheckConstraint("cardinality(edge_version_ids) <= 400", name="edge_limit"),
    )
    graph_id: Mapped[UUID] = mapped_column(ForeignKey("graph_collections.id"), index=True)
    version_number: Mapped[int]
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB)
    node_version_ids: Mapped[list[UUID]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    edge_version_ids: Mapped[list[UUID]] = mapped_column(ARRAY(PGUUID(as_uuid=True)))


class GraphCollectionPublication(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "graph_collection_publications"
    __table_args__ = (
        UniqueConstraint("graph_version_id", name="uq_graph_collection_publication_version"),
        ForeignKeyConstraint(
            ["graph_version_id", "content_hash"],
            ["graph_collection_versions.id", "graph_collection_versions.content_hash"],
            name="fk_graph_collection_publication_version_hash",
        ),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
    )
    graph_version_id: Mapped[UUID]
    content_hash: Mapped[str] = mapped_column(String(64))
    published_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
