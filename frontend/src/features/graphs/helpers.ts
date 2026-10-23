import type { GraphCamera, GraphEdge, GraphNode, GraphRecord, NodeKind, Point3D } from "./types";

export const MAX_NODES = 200;
export const MAX_EDGES = 400;
export const NODE_LABELS: Record<NodeKind, string> = { INDICATOR: "Indicador", MEASURE: "Medida", MECHANISM: "Mecanismo", AFFECTED_GROUP: "Grupo afetado" };
export const DIRECTION_LABELS = { INCREASES: "Pode aumentar", DECREASES: "Pode reduzir", UNCERTAIN: "Sentido incerto" };
export const EFFECT_LABELS = { ACCOUNTING_DIRECT: "Efeito contábil direto", INDIRECT_ESTIMATE: "Estimativa indireta", QUALITATIVE: "Relação qualitativa" };
export const CONSENSUS_LABELS = { ESTABLISHED: "Consolidado, segundo o autor", DEBATED: "Em debate, segundo o autor", SPECULATIVE: "Especulativo, segundo o autor" };
export const HORIZON_LABELS = { SHORT: "Curto prazo", MEDIUM: "Médio prazo", LONG: "Longo prazo" };

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Pure-payload IDs are not API UUIDs. Demo slugs deliberately do not resolve. */
export function uuidFromSlug(id: string, kind?: "node" | "edge"): string | null {
  const match = /^(node|edge)-([0-9a-f]{32})$/i.exec(id);
  if (!match || (kind && match[1].toLowerCase() !== kind)) return null;
  const hex = match[2].toLowerCase();
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function graphPath(id: string, revision?: number): string | null {
  if (!uuidPattern.test(id) || (revision !== undefined && (!Number.isSafeInteger(revision) || revision < 1 || revision > 2147483647))) return null;
  return `/grafos/${id.toLowerCase()}${revision === undefined ? "" : `/versoes/${revision}`}`;
}

/** Exact public node/edge API path, never a draft or implicit latest-version lookup. */
export function safePublicPath(kind: "node" | "edge", slug: string, revision: number): string | null {
  const id = uuidFromSlug(slug, kind);
  if (!id || !Number.isSafeInteger(revision) || revision < 1 || revision > 2147483647) return null;
  return `/api/v1/graphs/${kind === "node" ? "nodes" : "edges"}/${id}/versions/${revision}`;
}

const normalized = (text: string) => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").replace(/\s+/g, " ").trim();

/** Reject a truncated network: cutting rows would silently hide relations. */
export function assertGraphLimits(nodes: GraphNode[], edges: GraphEdge[]): void {
  if (nodes.length > MAX_NODES || edges.length > MAX_EDGES) throw new RangeError("Esta rede excede o limite de 200 nós ou 400 ligações.");
  const ids = new Set(nodes.map((node) => node.id));
  if (ids.size !== nodes.length || new Set(edges.map((edge) => edge.id)).size !== edges.length) throw new RangeError("A rede contém identidades duplicadas.");
  if (edges.some((edge) => !ids.has(edge.from_node.id) || !ids.has(edge.to_node.id))) throw new RangeError("A rede contém uma ligação sem suas duas pontas.");
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const fields: (keyof GraphNode)[] = ["id", "revision", "kind", "label", "definition", "dimension", "unit", "indicator_code", "policy_version_id", "policy_version_number"];
  if (edges.some((edge) => [edge.from_node, edge.to_node].some((endpoint) => fields.some((field) => endpoint[field] !== byId.get(endpoint.id)?.[field])))) throw new RangeError("Uma ligação usa conteúdo diferente da versão do nó selecionada.");
}

/** Rendering guard, not a substitute for backend validation or authorization. */
export function graphWithinLimits(record: GraphRecord): boolean {
  try { assertGraphLimits(record.content.nodes, record.content.edges); return true; } catch { return false; }
}

export function filterGraph(nodes: GraphNode[], edges: GraphEdge[], query: string, kind: "ALL" | NodeKind): { nodes: GraphNode[]; edges: GraphEdge[] } {
  assertGraphLimits(nodes, edges);
  const terms = normalized(query).split(" ").filter(Boolean);
  const matches = (text: string) => terms.every((term) => normalized(text).includes(term));
  const eligible = new Set(nodes.filter((node) => kind === "ALL" || node.kind === kind).map((node) => node.id));
  const selected = new Set(nodes.filter((node) => eligible.has(node.id) && matches(`${node.label} ${node.definition} ${node.dimension}`)).map((node) => node.id));
  const matchingEdges = edges.filter((edge) => terms.length > 0 && matches(`${edge.statement} ${edge.scope} ${edge.from_node.label} ${edge.to_node.label}`) && (eligible.has(edge.from_node.id) || eligible.has(edge.to_node.id)));
  for (const edge of matchingEdges) { selected.add(edge.from_node.id); selected.add(edge.to_node.id); }
  // Adjacent context remains attached when a type is chosen: no dangling arrows.
  if (!terms.length && kind !== "ALL") {
    for (const edge of edges) if (eligible.has(edge.from_node.id) || eligible.has(edge.to_node.id)) { selected.add(edge.from_node.id); selected.add(edge.to_node.id); }
  }
  return { nodes: nodes.filter((node) => selected.has(node.id)), edges: edges.filter((edge) => selected.has(edge.from_node.id) && selected.has(edge.to_node.id)) };
}

export function neighbors(nodeId: string, edges: GraphEdge[]): { incoming: GraphEdge[]; outgoing: GraphEdge[]; nodeIds: string[] } {
  const incoming = edges.filter((edge) => edge.to_node.id === nodeId);
  const outgoing = edges.filter((edge) => edge.from_node.id === nodeId);
  return { incoming, outgoing, nodeIds: [...new Set([...incoming.map((edge) => edge.from_node.id), ...outgoing.map((edge) => edge.to_node.id)])].sort() };
}

/** Number is used exclusively for visual geometry, never fiscal calculations. */
export function layoutGraph(nodes: GraphNode[], edges: GraphEdge[]): Point3D[] {
  assertGraphLimits(nodes, edges);
  const ordered = [...nodes].sort((a, b) => a.id.localeCompare(b.id));
  if (!ordered.length) return [];
  if (ordered.length === 1) return [{ id: ordered[0].id, x: 0, y: 0, z: 0 }];
  const points = ordered.map((node, i) => {
    const y = 1 - 2 * (i + 0.5) / ordered.length;
    const radius = Math.sqrt(1 - y * y);
    const angle = i * Math.PI * (3 - Math.sqrt(5));
    return { id: node.id, x: Math.cos(angle) * radius, y, z: Math.sin(angle) * radius };
  });
  const indexes = new Map(points.map((point, i) => [point.id, i]));
  const pairs = [...edges].sort((a, b) => a.id.localeCompare(b.id)).map((edge) => [indexes.get(edge.from_node.id)!, indexes.get(edge.to_node.id)!]);
  const anchors = points.map((point) => ({ ...point }));
  // Springs retain a nonzero rest length. A weak anchor keeps disconnected
  // concepts in the scene without letting an isolated node set its whole scale.
  const springPasses = points.length > 60 ? 38 : 110;
  for (let step = 0; step < springPasses; step++) {
    const forces = points.map(() => ({ x: 0, y: 0, z: 0 }));
    for (let i = 0; i < points.length; i++) for (let j = i + 1; j < points.length; j++) {
      const a = points[i], b = points[j];
      const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
      const squared = Math.max(0.025, dx * dx + dy * dy + dz * dz);
      const strength = 0.048 / squared;
      forces[i].x += dx * strength; forces[j].x -= dx * strength;
      forces[i].y += dy * strength; forces[j].y -= dy * strength;
      forces[i].z += dz * strength; forces[j].z -= dz * strength;
    }
    for (const [i, j] of pairs) {
      const distance = Math.max(0.01, Math.hypot(points[j].x - points[i].x, points[j].y - points[i].y, points[j].z - points[i].z));
      const spring = (distance - 0.95) * 0.065 / distance;
      for (const axis of ["x", "y", "z"] as const) { const delta = (points[j][axis] - points[i][axis]) * spring; forces[i][axis] += delta; forces[j][axis] -= delta; }
    }
    const cooling = 0.65 * (1 - step / (springPasses + 40));
    points.forEach((point, i) => { for (const axis of ["x", "y", "z"] as const) point[axis] += Math.max(-0.08, Math.min(0.08, forces[i][axis] + (anchors[i][axis] - point[axis]) * 0.018)) * cooling; });
  }
  const center = { x: 0, y: 0, z: 0 };
  const connected = new Set(edges.flatMap((edge) => [edge.from_node.id, edge.to_node.id]));
  const reference = connected.size > 1 ? points.filter((point) => connected.has(point.id)) : points;
  for (const point of reference) for (const axis of ["x", "y", "z"] as const) center[axis] += point[axis] / reference.length;
  const extent = { x: 0.01, y: 0.01, z: 0.01 };
  for (const point of reference) for (const axis of ["x", "y", "z"] as const) extent[axis] = Math.max(extent[axis], Math.abs(point[axis] - center[axis]));
  const scene = points.map((point) => ({ ...point, x: Math.max(-1.5, Math.min(1.5, (point.x - center.x) / extent.x * 1.5)), y: Math.max(-1.05, Math.min(1.05, (point.y - center.y) / extent.y * 1.05)), z: Math.max(-0.65, Math.min(0.65, (point.z - center.z) / extent.z * 0.65)) }));
  // Initial-view collision packing keeps front/back concepts independently
  // selectable. This is visual spacing, never a claimed strength of a relation.
  const initialCamera = { yaw: -0.32, pitch: 0.28, zoom: 1, panX: 0, panY: 0 };
  const gap = Math.min(38, 155 / Math.sqrt(scene.length));
  const collisionPasses = scene.length > 60 ? 6 : 32;
  for (let pass = 0; pass < collisionPasses; pass++) {
    const projections = scene.map((point) => projectPoint(point, initialCamera, 850, 550));
    for (let i = 0; i < scene.length; i++) for (let j = i + 1; j < scene.length; j++) {
      const a = projections[i], b = projections[j];
      const dx = a.x - b.x, dy = a.y - b.y;
      const distance = Math.hypot(dx, dy);
      if (distance >= gap) continue;
      const angle = (i + 1) * (j + 1) * 2.399963229728653;
      const push = (gap - distance) * 0.52;
      const screenX = (distance > 0.001 ? dx / distance : Math.cos(angle)) * push;
      const screenY = (distance > 0.001 ? dy / distance : Math.sin(angle)) * push;
      for (const [index, sign, scale] of [[i, 1, a.scale], [j, -1, b.scale]]) {
        const worldX = screenX / (140.25 * scale * Math.cos(initialCamera.yaw));
        const worldY = (screenY / (140.25 * scale) - Math.sin(initialCamera.yaw) * Math.sin(initialCamera.pitch) * worldX) / Math.cos(initialCamera.pitch);
        scene[index].x = Math.max(-1.5, Math.min(1.5, scene[index].x + worldX * sign));
        scene[index].y = Math.max(-1.05, Math.min(1.05, scene[index].y + worldY * sign));
        projections[index] = projectPoint(scene[index], initialCamera, 850, 550);
      }
    }
  }
  return scene;
}

const finite = (value: number, fallback: number) => Number.isFinite(value) ? value : fallback;
export function projectPoint(point: Point3D, camera: GraphCamera, width: number, height: number): { x: number; y: number; scale: number; depth: number } {
  const yaw = finite(camera.yaw, 0), pitch = finite(camera.pitch, 0);
  const x = finite(point.x, 0), y = finite(point.y, 0), z = finite(point.z, 0);
  const rotatedX = x * Math.cos(yaw) + z * Math.sin(yaw);
  const rotatedZ = -x * Math.sin(yaw) + z * Math.cos(yaw);
  const rotatedY = y * Math.cos(pitch) - rotatedZ * Math.sin(pitch);
  const depth = y * Math.sin(pitch) + rotatedZ * Math.cos(pitch);
  const w = Math.max(1, finite(width, 1000)), h = Math.max(1, finite(height, 640));
  const perspective = 4 / Math.max(1, 4 - depth);
  const zoom = Math.max(0.4, Math.min(3, finite(camera.zoom, 1)));
  const size = Math.min(w, h) * 0.255 * zoom * perspective;
  return { x: w / 2 + rotatedX * size + finite(camera.panX, 0), y: h / 2 + rotatedY * size + finite(camera.panY, 0), scale: perspective * zoom, depth };
}
