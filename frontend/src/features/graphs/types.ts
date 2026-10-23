import type { ContextEvidence, ContextSource, EvidenceLink } from "../contexts/types";

export type NodeKind = "INDICATOR" | "MEASURE" | "MECHANISM" | "AFFECTED_GROUP";
export type GraphNode = {
  id: string; revision: number; kind: NodeKind; label: string; definition: string;
  dimension: string; unit: string | null; indicator_code: string | null;
  policy_version_id: string | null; policy_version_number: number | null;
};
export type EdgeDirection = "INCREASES" | "DECREASES" | "UNCERTAIN";
export type GraphEdge = {
  contract_version: "1.0.0"; id: string; revision: number; author_id: string;
  updated_at: string; from_node: GraphNode; to_node: GraphNode; statement: string;
  trigger: "INCREASE" | "ADOPTION"; direction: EdgeDirection;
  horizon: "SHORT" | "MEDIUM" | "LONG";
  effect: "ACCOUNTING_DIRECT" | "INDIRECT_ESTIMATE" | "QUALITATIVE";
  consensus: "ESTABLISHED" | "DEBATED" | "SPECULATIVE";
  authorship: "HUMAN" | "AI_ASSISTED";
  sources: ContextSource[]; evidence: ContextEvidence[]; links: EvidenceLink[];
  premises: string[]; scope: string; period: string; limitations: string[]; unknowns: string[];
  counterpoint_status: "NOT_RESEARCHED" | "NOT_FOUND" | "DOCUMENTED";
  counterpoint_search_notes: string[]; counterpoint_searched_at: string | null;
  counterargument_note: string;
};
export type GraphReview = {
  contract_version: "1.0.0"; edge_id: string; edge_revision: number;
  content_hash: string; reviewer_id: string; reviewed_at: string;
  decision: "ACCEPT" | "REQUEST_CHANGES" | "DISPUTE" | "REJECT"; rationale: string;
  references_checked: boolean; scopes_checked: boolean;
  counterpoints_checked: boolean; limitations_checked: boolean;
};
export type GraphPublication = {
  edge_version_id: string; content_hash: string; published_at: string;
  publication_state: "REVIEWED" | "DISPUTED"; review: GraphReview;
};
export type GraphTopology = {
  duplicate_edges: string[][]; conflicting_edges: string[][];
  cycle_components: string[][]; isolated_nodes: string[]; limitations: string[];
};
export type GraphSummary = {
  id: string; revision: number; version_id: string; content_hash: string;
  published_at: string | null; is_example: boolean; content: { title: string };
};
export type GraphRecord = Omit<GraphSummary, "content"> & {
  content: {
    contract_version: "1.0.0"; id: string; revision: number; author_id: string;
    updated_at: string; title: string; nodes: GraphNode[]; edges: GraphEdge[];
  };
  topology: GraphTopology; publications: GraphPublication[];
};
export type GraphVersion = { revision: number; content_hash: string; published_at: string; title: string };
export type Selection = { kind: "node" | "edge"; id: string } | null;
export type Point3D = { id: string; x: number; y: number; z: number };
export type GraphCamera = { yaw: number; pitch: number; zoom: number; panX: number; panY: number };
