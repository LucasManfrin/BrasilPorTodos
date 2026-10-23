"""Public graph snapshots and authenticated curation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from app.core.dependencies import DB, CurrentUser
from app.modules.graphs import service
from app.modules.graphs.schemas import (
    EdgeCreate,
    EdgePublishInput,
    EdgeReviewInput,
    EdgeUpdate,
    GraphCreate,
    GraphPublishInput,
    GraphUpdate,
    NodeCreate,
    NodeUpdate,
)

router = APIRouter(prefix="/api/v1/graphs", tags=["graphs"])
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
Search = Annotated[str | None, Query(max_length=120)]
Revision = Annotated[int, Path(ge=1)]


@router.get("/nodes")
def nodes(session: DB, page: Page = 1, page_size: PageSize = 20, q: Search = None):
    return service.list_nodes(session, page, page_size, q)


@router.get("/nodes/mine")
def node_mine(session: DB, user: CurrentUser, page: Page = 1, page_size: PageSize = 20):
    return service.list_nodes(session, page, page_size, user=user)


@router.post("/nodes", status_code=201)
def create_node(data: NodeCreate, session: DB, user: CurrentUser):
    return {"data": service.create_node(session, data, user)}


@router.put("/nodes/{node_id}")
@router.patch("/nodes/{node_id}")
def update_node(node_id: UUID, data: NodeUpdate, session: DB, user: CurrentUser):
    return {"data": service.update_node(session, node_id, data, user)}


@router.get("/nodes/{node_id}/draft")
def draft_node(node_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft_node(session, node_id, user)}


@router.get("/nodes/{node_id}/versions")
def node_versions(node_id: UUID, session: DB):
    return service.node_history(session, node_id)


@router.get("/nodes/{node_id}/versions/{revision}")
def node_version(node_id: UUID, revision: Revision, session: DB):
    return {"data": service.public_node(session, node_id, revision)}


@router.get("/nodes/{node_id}")
def node_detail(node_id: UUID, session: DB):
    return {"data": service.public_node(session, node_id)}


@router.get("/edges")
def edges(session: DB, page: Page = 1, page_size: PageSize = 20, q: Search = None):
    return service.list_edges(session, page, page_size, q)


@router.get("/edges/mine")
def edge_mine(session: DB, user: CurrentUser, page: Page = 1, page_size: PageSize = 20):
    return service.list_edges(session, page, page_size, user=user)


@router.get("/edges/review-queue")
def edge_review_queue(session: DB, user: CurrentUser, page: Page = 1, page_size: PageSize = 20):
    return service.list_edges(session, page, page_size, user=user, queue=True)


@router.post("/edges", status_code=201)
def create_edge(data: EdgeCreate, session: DB, user: CurrentUser):
    return {"data": service.create_edge(session, data, user)}


@router.put("/edges/{edge_id}")
@router.patch("/edges/{edge_id}")
def update_edge(edge_id: UUID, data: EdgeUpdate, session: DB, user: CurrentUser):
    return {"data": service.update_edge(session, edge_id, data, user)}


@router.get("/edges/{edge_id}/draft")
def draft_edge(edge_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft_edge(session, edge_id, user)}


@router.post("/edges/{edge_id}/review")
def review_edge(edge_id: UUID, data: EdgeReviewInput, session: DB, user: CurrentUser):
    return {"data": service.review_edge(session, edge_id, data, user)}


@router.post("/edges/{edge_id}/publish")
def publish_edge(edge_id: UUID, data: EdgePublishInput, session: DB, user: CurrentUser):
    return {"data": service.publish_edge(session, edge_id, data, user)}


@router.get("/edges/{edge_id}/versions")
def edge_versions(edge_id: UUID, session: DB):
    return service.edge_history(session, edge_id)


@router.get("/edges/{edge_id}/versions/{revision}")
def edge_version(edge_id: UUID, revision: Revision, session: DB):
    return {"data": service.public_edge(session, edge_id, revision)}


@router.get("/edges/{edge_id}")
def edge_detail(edge_id: UUID, session: DB):
    return {"data": service.public_edge(session, edge_id)}


@router.get("")
def graphs(session: DB, page: Page = 1, page_size: PageSize = 20, q: Search = None):
    return service.list_graphs(session, page, page_size, q)


@router.get("/mine")
def graph_mine(session: DB, user: CurrentUser, page: Page = 1, page_size: PageSize = 20):
    return service.list_graphs(session, page, page_size, user=user)


@router.post("", status_code=201)
def create_graph(data: GraphCreate, session: DB, user: CurrentUser):
    return {"data": service.create_graph(session, data, user)}


@router.put("/{graph_id}")
@router.patch("/{graph_id}")
def update_graph(graph_id: UUID, data: GraphUpdate, session: DB, user: CurrentUser):
    return {"data": service.update_graph(session, graph_id, data, user)}


@router.get("/{graph_id}/draft")
def draft_graph(graph_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft_graph(session, graph_id, user)}


@router.post("/{graph_id}/publish")
def publish_graph(graph_id: UUID, data: GraphPublishInput, session: DB, user: CurrentUser):
    return {"data": service.publish_graph(session, graph_id, data, user)}


@router.get("/{graph_id}/versions")
def graph_versions(graph_id: UUID, session: DB):
    return service.graph_history(session, graph_id)


@router.get("/{graph_id}/versions/{revision}")
def graph_version(graph_id: UUID, revision: Revision, session: DB):
    return {"data": service.public_graph(session, graph_id, revision)}


@router.get("/{graph_id}")
def graph_detail(graph_id: UUID, session: DB):
    return {"data": service.public_graph(session, graph_id)}
