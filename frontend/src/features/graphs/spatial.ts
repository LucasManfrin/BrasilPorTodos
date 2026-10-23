import { assertGraphLimits, layoutGraph } from "./helpers.ts";
import type { GraphEdge, GraphNode, Point3D } from "./types";

/** Geometry only. World coordinates never encode fiscal impact or certainty. */
export const WORLD_SCALE = 160;
const MAX_CACHED_LAYOUTS = 8;
const layouts = new Map<string, Point3D[]>();

/** Stable positions stop the renderer from restarting physics on selection. */
export function spatialLayout(nodes: GraphNode[], edges: GraphEdge[]): Point3D[] {
  // Validate even a cache hit: a new snapshot may reuse IDs with invalid endpoints.
  assertGraphLimits(nodes, edges);
  const signature = JSON.stringify([
    nodes.map((node) => node.id).sort(),
    edges.map((edge) => [edge.id, edge.from_node.id, edge.to_node.id]).sort((a, b) => a[0].localeCompare(b[0])),
  ]);
  const cached = layouts.get(signature);
  if (cached) {
    layouts.delete(signature);
    layouts.set(signature, cached);
    return cached.map((point) => ({ ...point }));
  }
  const points = layoutGraph(nodes, edges).map((point) => ({
    id: point.id, x: point.x * WORLD_SCALE, y: point.y * WORLD_SCALE, z: point.z * WORLD_SCALE,
  }));
  layouts.set(signature, points);
  if (layouts.size > MAX_CACHED_LAYOUTS) layouts.delete(layouts.keys().next().value!);
  // Three/force-graph may add mutable properties: never lend it the cache itself.
  return points.map((point) => ({ ...point }));
}

/** Undirected visual neighborhood; original edge directions remain untouched. */
export function neighborhoodIds(root: string, edges: GraphEdge[], depth = 1): string[] {
  const visited = new Set([root]);
  let frontier = [root];
  const passes = Number.isFinite(depth) ? Math.max(0, Math.floor(depth)) : 0;
  for (let pass = 0; pass < passes && frontier.length; pass++) {
    const current = new Set(frontier);
    const next = new Set<string>();
    for (const edge of edges) {
      if (current.has(edge.from_node.id) && !visited.has(edge.to_node.id)) next.add(edge.to_node.id);
      if (current.has(edge.to_node.id) && !visited.has(edge.from_node.id)) next.add(edge.from_node.id);
    }
    frontier = [...next];
    for (const id of frontier) visited.add(id);
  }
  return [...visited].sort();
}

export type CameraFrame = { target: { x: number; y: number; z: number }; distance: number };

/** Fits a bounding sphere at vertical FOV >=40°, including narrow portrait views. */
export function cameraFrame(points: Pick<Point3D, "x" | "y" | "z">[], aspect = 1): CameraFrame {
  const finite = points.filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y) && Number.isFinite(point.z));
  if (!finite.length) return { target: { x: 0, y: 0, z: 0 }, distance: 420 };
  const target = { x: 0, y: 0, z: 0 };
  for (const axis of ["x", "y", "z"] as const) {
    target[axis] = (Math.min(...finite.map((point) => point[axis])) + Math.max(...finite.map((point) => point[axis]))) / 2;
  }
  const radius = Math.max(40, ...finite.map((point) => Math.hypot(point.x - target.x, point.y - target.y, point.z - target.z)));
  const safeAspect = Number.isFinite(aspect) && aspect > 0 ? Math.max(0.001, aspect) : 1;
  const verticalHalfFov = Math.PI / 9;
  const horizontalHalfFov = Math.atan(Math.tan(verticalHalfFov) * safeAspect);
  const limitingHalfFov = Math.min(verticalHalfFov, horizontalHalfFov);
  return { target, distance: Math.max(180, (radius + 32) * 1.2 / Math.sin(limitingHalfFov)) };
}

export type RenderingCapabilities = {
  reducedMotion: boolean; webgl: boolean; deviceMemory?: number;
  hardwareConcurrency?: number; saveData?: boolean;
};

/** Missing capability hints are unknown, never a reason to reject a device. */
export function fallbackReason({ reducedMotion, webgl, deviceMemory, hardwareConcurrency, saveData }: RenderingCapabilities): string | null {
  if (reducedMotion) return "A lista está ativa para respeitar sua preferência por movimento reduzido.";
  if (!webgl) return "Este navegador não disponibilizou o 3D. Explore as mesmas conexões na lista.";
  if (saveData) return "A lista está ativa para economizar dados, conforme a preferência do seu dispositivo.";
  if ((deviceMemory !== undefined && deviceMemory > 0 && deviceMemory <= 2) || (hardwareConcurrency !== undefined && hardwareConcurrency > 0 && hardwareConcurrency <= 2)) {
    return "A lista está ativa para manter a navegação leve neste dispositivo.";
  }
  return null;
}
