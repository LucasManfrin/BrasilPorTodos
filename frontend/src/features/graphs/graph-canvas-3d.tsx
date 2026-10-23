"use client";

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { NODE_LABELS, neighbors } from "./helpers";
import { spatialLayout, cameraFrame, neighborhoodIds } from "./spatial";
import { createTapTracker } from "./interaction";
import type { GraphNode, GraphEdge, Selection, Point3D, NodeKind } from "./types";
import styles from "./graph-canvas-3d.module.css";

type Props = { nodes: GraphNode[]; edges: GraphEdge[]; selection: Selection; onSelect: (selection: Selection) => void; reducedMotion: boolean; onFailure: (reason: string) => void };
type Engine = { select: (selection: Selection) => void; reset: () => void; zoom: (factor: number) => void; rotate: (value: boolean) => void; illuminate: (kind: NodeKind | null) => void; dive: (id: string, depth: number) => void; dispose: () => void };
const kinds: NodeKind[] = ["MEASURE", "INDICATOR", "MECHANISM", "AFFECTED_GROUP"];
const tokens: Record<NodeKind, string> = { MEASURE: "--yellow", INDICATOR: "--green", MECHANISM: "--blue-muted", AFFECTED_GROUP: "--white" };
const vec = (point: { x: number; y: number; z: number }) => new THREE.Vector3(point.x, point.y, point.z);

/** The renderer accepts already-positioned visual objects. Production guards live in spatialLayout;
 * isolated stress fixtures can exercise 500 edges without changing the 400-edge public contract. */
export function createGraphRenderer(host: HTMLDivElement, nodes: GraphNode[], edges: GraphEdge[], positions: Point3D[], callbacks: { select: Props["onSelect"]; dive: (id: string) => void; pause: () => void; hover: (text: string) => void; failure: Props["onFailure"]; rendered?: (time: number) => void }): Engine {
  const css = getComputedStyle(host);
  const color = (token: string) => css.getPropertyValue(token).trim();
  const background = color("--night"), neutral = color("--blue-muted"), white = color("--white"), yellow = color("--yellow");
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "default" });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5));
  renderer.setClearColor(background);
  renderer.domElement.setAttribute("role", "img");
  renderer.domElement.setAttribute("aria-label", `Rede tridimensional com ${nodes.length} nós e ${edges.length} relações. Use a lista de nós por teclado ou o modo Lista para consultar todas as conexões.`);
  host.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(background, 650, 1800);
  const camera = new THREE.PerspectiveCamera(42, 1, 1, 5000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = .08; controls.autoRotate = true; controls.autoRotateSpeed = .22;
  controls.minDistance = 65; controls.maxDistance = 4800;
  controls.touches.ONE = THREE.TOUCH.ROTATE; controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
  scene.add(new THREE.AmbientLight(white, 2));
  const light = new THREE.DirectionalLight(white, 3); light.position.set(80, 160, 300); scene.add(light);
  const points = new Map(positions.map(point => [point.id, vec(point)]));
  const resources: { dispose: () => void }[] = [];
  const own = <T extends { dispose: () => void }>(value: T): T => { resources.push(value); return value; };
  const sphere = own(new THREE.SphereGeometry(5.5, 18, 14));
  const particleGeometry = own(new THREE.SphereGeometry(1.9, 8, 6));
  const coneGeometry = own(new THREE.ConeGeometry(2.7, 7, 8));
  const haloCanvas = document.createElement("canvas"); haloCanvas.width = haloCanvas.height = 64;
  const glowContext = haloCanvas.getContext("2d")!;
  const gradient = glowContext.createRadialGradient(32, 32, 1, 32, 32, 32);
  gradient.addColorStop(0, white); gradient.addColorStop(.2, white); gradient.addColorStop(1, "transparent");
  glowContext.fillStyle = gradient; glowContext.fillRect(0, 0, 64, 64);
  const haloTexture = own(new THREE.CanvasTexture(haloCanvas));
  function sprite(text: string, tint = white) {
    const canvas = document.createElement("canvas"); const context = canvas.getContext("2d")!;
    context.font = "600 28px sans-serif";
    const words = text.split(" "); const lines: string[] = []; let line = "";
    for (const word of words) { const next = line ? `${line} ${word}` : word; if (context.measureText(next).width > 350 && line) { lines.push(line); line = word; } else line = next; } if (line) lines.push(line);
    canvas.width = Math.max(52, Math.min(384, Math.ceil(Math.max(0, ...lines.map(value => context.measureText(value).width))) + 24)); canvas.height = Math.max(52, lines.length * 36 + 16);
    context.font = "600 28px sans-serif"; context.fillStyle = background; context.globalAlpha = .88; if (text !== "?") context.fillRect(0, 0, canvas.width, canvas.height); context.globalAlpha = 1;
    context.fillStyle = tint; context.textAlign = "center"; context.textBaseline = "middle";
    lines.forEach((value, index) => context.fillText(value, canvas.width / 2, 26 + index * 36, canvas.width - 20));
    const texture = own(new THREE.CanvasTexture(canvas)); texture.colorSpace = THREE.SRGBColorSpace;
    const material = own(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false, depthWrite: false }));
    const object = new THREE.Sprite(material); object.renderOrder = 3;
    object.userData.ratio = canvas.width / canvas.height; object.userData.lines = lines.length;
    return object;
  }
  // One draw call for every sphere, one for every directional arrow, and three
  // for the consensus styles. Per-instance/vertex colors only express type or
  // interaction state; they never encode a numerical effect or truth ranking.
  const backgroundColor = new THREE.Color(background), neutralColor = new THREE.Color(neutral);
  const nodeBodies = own(new THREE.InstancedMesh(sphere, own(new THREE.MeshStandardMaterial({ color: white, roughness: .35, metalness: .15 })), nodes.length));
  const arrows = own(new THREE.InstancedMesh(coneGeometry, own(new THREE.MeshBasicMaterial({ color: white })), edges.length));
  nodeBodies.instanceMatrix.setUsage(THREE.DynamicDrawUsage); arrows.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  nodeBodies.frustumCulled = arrows.frustumCulled = false;
  scene.add(nodeBodies, arrows);
  const hiddenMatrix = new THREE.Matrix4().makeScale(0, 0, 0), matrix = new THREE.Matrix4();
  const mixed = new THREE.Color(), unitScale = new THREE.Vector3(1, 1, 1), axis = new THREE.Vector3(0, 1, 0);
  const batches = (["ESTABLISHED", "DEBATED", "SPECULATIVE"] as const).map(consensus => {
    const members = edges.map((edge, index) => ({ edge, index })).filter(item => item.edge.consensus === consensus);
    const coordinates = new Float32Array(members.length * 6), colors = new Float32Array(members.length * 6), distances = new Float32Array(members.length * 2);
    members.forEach(({ edge }, index) => {
      const start = points.get(edge.from_node.id)!, end = points.get(edge.to_node.id)!;
      coordinates.set([start.x, start.y, start.z, end.x, end.y, end.z], index * 6);
      distances[index * 2 + 1] = start.distanceTo(end);
      mixed.copy(backgroundColor).lerp(neutralColor, .52);
      colors.set([mixed.r, mixed.g, mixed.b, mixed.r, mixed.g, mixed.b], index * 6);
    });
    const geometry = own(new THREE.BufferGeometry());
    const position = new THREE.BufferAttribute(coordinates, 3).setUsage(THREE.DynamicDrawUsage);
    const tint = new THREE.BufferAttribute(colors, 3).setUsage(THREE.DynamicDrawUsage);
    geometry.setAttribute("position", position); geometry.setAttribute("color", tint); geometry.setAttribute("lineDistance", new THREE.BufferAttribute(distances, 1));
    const material = own(consensus === "ESTABLISHED" ? new THREE.LineBasicMaterial({ vertexColors: true }) : new THREE.LineDashedMaterial({ vertexColors: true, dashSize: consensus === "DEBATED" ? 9 : 1.5, gapSize: 6 }));
    const lines = new THREE.LineSegments(geometry, material); lines.frustumCulled = false; scene.add(lines);
    return { consensus, members, position, tint };
  });
  const edgeSlots = new Map(batches.flatMap(batch => batch.members.map(({ edge }, slot) => [edge.id, { batch, slot }] as const)));
  const nodeObjects = nodes.map((node, index) => {
    // Object3D is metadata for projection/picking, not an extra rendered mesh.
    const mesh = new THREE.Object3D(); mesh.position.copy(points.get(node.id)!); mesh.updateMatrix();
    const tint = new THREE.Color(color(tokens[node.kind])); nodeBodies.setMatrixAt(index, mesh.matrix); nodeBodies.setColorAt(index, tint);
    const halo = new THREE.Sprite(own(new THREE.SpriteMaterial({ map: haloTexture, color: color(tokens[node.kind]), transparent: true, opacity: .22, depthWrite: false })));
    halo.scale.setScalar(24); halo.position.copy(mesh.position); scene.add(halo);
    const label = sprite(node.label); label.position.copy(mesh.position); scene.add(label);
    return { node, index, tint, mesh, halo, label, strength: 1, visible: true };
  });
  const focus = own(new THREE.InstancedMesh(own(new THREE.CylinderGeometry(1, 1, 1, 6)), own(new THREE.MeshBasicMaterial({ color: yellow, transparent: true, opacity: .9 })), 512));
  focus.frustumCulled = false; focus.count = 0;
  focus.visible = false; scene.add(focus);
  const particles = Array.from({ length: 3 }, () => { const object = new THREE.Mesh(particleGeometry, own(new THREE.MeshBasicMaterial({ color: white }))); object.visible = false; scene.add(object); return object; });
  const edgeObjects = edges.map((edge, index) => {
    const start = points.get(edge.from_node.id)!, end = points.get(edge.to_node.id)!;
    const direction = end.clone().sub(start).normalize();
    const quaternion = new THREE.Quaternion().setFromUnitVectors(axis, direction);
    const arrowMatrix = new THREE.Matrix4().compose(start.clone().lerp(end, .77), quaternion, unitScale);
    arrows.setMatrixAt(index, edge.direction === "UNCERTAIN" ? hiddenMatrix : arrowMatrix);
    arrows.setColorAt(index, mixed.copy(backgroundColor).lerp(neutralColor, .8));
    const question = edge.direction === "UNCERTAIN" ? sprite("?", neutral) : null;
    if (question) { question.position.copy(start).lerp(end, .5); question.scale.set(22, 22, 1); scene.add(question); }
    return { edge, index, start, end, quaternion, arrowMatrix, slot: edgeSlots.get(edge.id)!, question, visible: true };
  });
  let selected: Selection = null, litKind: NodeKind | null = null, diveSet: Set<string> | null = null;
  let frame = 0, disposed = false, onScreen = true, width = 1, height = 1, dirty = true, lastTime = 0;
  let tween: { from: THREE.Vector3; to: THREE.Vector3; fromTarget: THREE.Vector3; toTarget: THREE.Vector3; start: number | null } | null = null;
  function framePoints(targetPoints: Point3D[] | THREE.Vector3[], animate = true) {
    const overlay = host.closest("[data-graph-map]")?.querySelector<HTMLElement>("[data-graph-overlay]");
    const panel = overlay?.getBoundingClientRect();
    const bottomSheet = !!panel && width < 1050;
    const usableWidth = panel && !bottomSheet ? Math.max(220, width - panel.width - 50) : width;
    const usableHeight = panel && bottomSheet ? Math.max(220, height - panel.height - 70) : height;
    const box = cameraFrame(targetPoints, usableWidth / usableHeight); const target = vec(box.target);
    const direction = camera.position.clone().sub(controls.target).normalize(); if (direction.lengthSq() === 0) direction.set(.15, .12, 1).normalize();
    const right = new THREE.Vector3().crossVectors(camera.up, direction).normalize();
    const up = new THREE.Vector3().crossVectors(direction, right).normalize();
    const tan = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    const vertical = tan * Math.max(160, usableHeight - (bottomSheet ? 55 : 170)) / height;
    const horizontal = tan * Math.max(170, usableWidth - 64) / height;
    box.distance = Math.max(180, ...targetPoints.map(point => {
      const relative = vec(point).sub(target);
      return relative.dot(direction) + Math.max((Math.abs(relative.dot(right)) + 18) / horizontal, (Math.abs(relative.dot(up)) + 18) / vertical) * 1.14;
    }));
    if (panel) {
      const amount = box.distance * tan;
      target.addScaledVector(bottomSheet ? up : right, bottomSheet ? -amount * panel.height / height : amount * panel.width / height);
    }
    const to = target.clone().addScaledVector(direction, box.distance);
    if (animate) tween = { from: camera.position.clone(), to, fromTarget: controls.target.clone(), toTarget: target, start: null };
    else { camera.position.copy(to); controls.target.copy(target); controls.update(); }
    dirty = true; schedule();
  }
  function highlight() {
    const adjacent = selected?.kind === "node" ? new Set(neighborhoodIds(selected.id, edges, 1)) : selected?.kind === "edge" ? new Set(edges.filter(edge => edge.id === selected!.id).flatMap(edge => [edge.from_node.id, edge.to_node.id])) : null;
    for (const item of nodeObjects) {
      item.visible = !diveSet || diveSet.has(item.node.id); item.halo.visible = item.visible;
      const direct = !adjacent || adjacent.has(item.node.id); const type = !litKind || item.node.kind === litKind;
      item.strength = direct && type ? 1 : .15;
      matrix.compose(item.mesh.position, item.mesh.quaternion, unitScale);
      nodeBodies.setMatrixAt(item.index, item.visible ? matrix : hiddenMatrix);
      nodeBodies.setColorAt(item.index, mixed.copy(backgroundColor).lerp(item.tint, item.strength));
      item.halo.material.opacity = selected?.kind === "node" && selected.id === item.node.id ? .68 : .18 * item.strength;
      item.halo.scale.setScalar(selected?.kind === "node" && selected.id === item.node.id ? 38 : 24);
    }
    for (const item of edgeObjects) {
      item.visible = !diveSet || diveSet.has(item.edge.from_node.id) && diveSet.has(item.edge.to_node.id);
      const focused = selected?.kind === "edge" && selected.id === item.edge.id;
      const adjacentEdge = !selected || focused || selected.kind === "node" && (item.edge.from_node.id === selected.id || item.edge.to_node.id === selected.id);
      const { batch, slot } = item.slot, offset = slot * 2;
      batch.position.setXYZ(offset, item.visible ? item.start.x : 0, item.visible ? item.start.y : 0, item.visible ? item.start.z : 0);
      batch.position.setXYZ(offset + 1, item.visible ? item.end.x : 0, item.visible ? item.end.y : 0, item.visible ? item.end.z : 0);
      mixed.copy(backgroundColor).lerp(neutralColor, adjacentEdge ? .52 : .09);
      batch.tint.setXYZ(offset, mixed.r, mixed.g, mixed.b); batch.tint.setXYZ(offset + 1, mixed.r, mixed.g, mixed.b);
      arrows.setMatrixAt(item.index, item.visible && item.edge.direction !== "UNCERTAIN" ? item.arrowMatrix : hiddenMatrix);
      arrows.setColorAt(item.index, mixed.copy(backgroundColor).lerp(neutralColor, adjacentEdge ? .8 : .12));
      if (item.question) { item.question.visible = item.visible; item.question.material.opacity = adjacentEdge ? .95 : .2; }
    }
    nodeBodies.instanceMatrix.needsUpdate = arrows.instanceMatrix.needsUpdate = true;
    if (nodeBodies.instanceColor) nodeBodies.instanceColor.needsUpdate = true;
    if (arrows.instanceColor) arrows.instanceColor.needsUpdate = true;
    batches.forEach(batch => { batch.position.needsUpdate = batch.tint.needsUpdate = true; });
    const focused = selected?.kind === "edge" ? edgeObjects.find(item => item.edge.id === selected!.id && item.visible) : null;
    focus.visible = !!focused;
    if (focused) {
      const length = focused.start.distanceTo(focused.end);
      const dash = focused.edge.consensus === "ESTABLISHED" ? length : focused.edge.consensus === "DEBATED" ? 9 : 1.5;
      const gap = focused.edge.consensus === "ESTABLISHED" ? 0 : 6;
      let count = 0;
      for (let start = 0; start < length && count < 512; start += dash + gap) {
        const size = Math.min(dash, length - start);
        const center = focused.start.clone().lerp(focused.end, (start + size / 2) / length);
        matrix.compose(center, focused.quaternion, new THREE.Vector3(1, size, 1));
        focus.setMatrixAt(count++, matrix);
      }
      focus.count = count; focus.instanceMatrix.needsUpdate = true;
    } else focus.count = 0;
    particles.forEach(particle => { particle.visible = !!focused && focused.edge.direction !== "UNCERTAIN"; });
    dirty = true; schedule();
  }
  function select(value: Selection) {
    callbacks.hover(""); selected = value;
    if (!value) diveSet = null;
    else if (diveSet) {
      const ids = value.kind === "node" ? [value.id] : edges.filter(edge => edge.id === value.id).flatMap(edge => [edge.from_node.id, edge.to_node.id]);
      if (ids.some(id => !diveSet!.has(id))) diveSet = null;
    } controls.autoRotate = false; callbacks.pause(); highlight();
    const ids = value?.kind === "node" ? new Set(neighborhoodIds(value.id, edges, 1)) : value?.kind === "edge" ? new Set(edges.filter(edge => edge.id === value.id).flatMap(edge => [edge.from_node.id, edge.to_node.id])) : null;
    framePoints(positions.filter(point => !ids || ids.has(point.id)));
  }
  // Text sprites face the camera. Screen-space packing moves labels only, never nodes or links.
  function labels() {
    const occupied: { x: number; y: number; w: number; h: number }[] = [];
    for (const item of nodeObjects) if (item.visible) {
      const screen = item.mesh.position.clone().project(camera);
      const depth = Math.abs(item.mesh.position.clone().applyMatrix4(camera.matrixWorldInverse).z);
      const radius = 5.5 * height / (2 * Math.max(1, depth) * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) + 3;
      occupied.push({ x: (screen.x + 1) * width / 2 - radius, y: (1 - screen.y) * height / 2 - radius, w: radius * 2, h: radius * 2 });
    }
    for (const item of edgeObjects) if (item.question?.visible) {
      const screen = item.question.position.clone().project(camera);
      const depth = Math.abs(item.question.position.clone().applyMatrix4(camera.matrixWorldInverse).z);
      const size = 22 * height / (2 * Math.max(1, depth) * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
      occupied.push({ x: (screen.x + 1) * width / 2 - size / 2, y: (1 - screen.y) * height / 2 - size / 2, w: size, h: size });
    }
    const ordered = [...nodeObjects].sort((a, b) => Number(b.node.id === selected?.id) - Number(a.node.id === selected?.id) || b.strength - a.strength || a.node.id.localeCompare(b.node.id));
    const projected = new THREE.Vector3();
    for (const item of ordered) {
      item.label.visible = false; if (!item.visible) continue;
      projected.copy(item.mesh.position).project(camera);
      if (projected.z > 1 || projected.z < -1) continue;
      const x = (projected.x + 1) * width / 2, y = (1 - projected.y) * height / 2;
      const close = camera.position.distanceTo(item.mesh.position) < 520;
      const important = !!selected && item.strength === 1;
      const maxWidth = important ? Math.min(184, width * .48) : close ? 164 : 148;
      const w = Math.min(maxWidth, item.label.userData.ratio * (item.label.userData.lines * (important ? 19 : 17) + 12));
      const h = w / item.label.userData.ratio;
      const options = [[0, -23 - h / 2], [0, 23 + h / 2], [w / 2 + 14, 0], [-w / 2 - 14, 0], [w / 2, -36 - h], [-w / 2, 36 + h], [0, -60 - h], [0, 60 + h]];
      let rect: { x: number; y: number; w: number; h: number } | null = null;
      for (const [dx, dy] of options) {
        const candidate = { x: x + dx - w / 2, y: y + dy - h / 2, w, h };
        if (candidate.x < 8 || candidate.y < 65 || candidate.x + w > width - 8 || candidate.y + h > height - 185) continue;
        if (occupied.some(other => candidate.x < other.x + other.w + 4 && candidate.x + w + 4 > other.x && candidate.y < other.y + other.h + 4 && candidate.y + h + 4 > other.y)) continue;
        rect = candidate; break;
      }
      if (!rect) continue;
      occupied.push(rect);
      const labelPosition = new THREE.Vector3((rect.x + w / 2) / width * 2 - 1, 1 - (rect.y + h / 2) / height * 2, projected.z).unproject(camera);
      item.label.position.copy(labelPosition);
      const cameraDepth = Math.abs(labelPosition.clone().applyMatrix4(camera.matrixWorldInverse).z);
      const worldPerPixel = 2 * cameraDepth * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / height;
      item.label.scale.set(w * worldPerPixel, h * worldPerPixel, 1);
      item.label.material.opacity = important ? 1 : item.strength < 1 ? .18 : close ? .88 : .55;
      item.label.visible = true;
    }
  }
  function render(time: number) {
    frame = 0; if (disposed || document.hidden || !onScreen) return;
    const delta = Math.min(.05, (time - lastTime) / 1000 || .016); lastTime = time;
    if (tween) {
      tween.start ??= time; const p = Math.min(1, (time - tween.start) / 1050); const ease = p < .5 ? 4 * p ** 3 : 1 - (-2 * p + 2) ** 3 / 2;
      camera.position.lerpVectors(tween.from, tween.to, ease); controls.target.lerpVectors(tween.fromTarget, tween.toTarget, ease); dirty = true; if (p === 1) tween = null;
    }
    const changed = controls.update(delta);
    const depth = camera.position.distanceTo(controls.target);
    (scene.fog as THREE.Fog).near = Math.max(300, depth * .85);
    (scene.fog as THREE.Fog).far = depth + 1300;
    const animatedEdge = selected?.kind === "edge" ? edgeObjects.find(item => item.edge.id === selected!.id && item.visible && item.edge.direction !== "UNCERTAIN") : null;
    if (animatedEdge) particles.forEach((particle, index) => particle.position.copy(animatedEdge.start).lerp(animatedEdge.end, (time / 2400 + index / 3) % 1));
    if (dirty || changed || tween || animatedEdge) { labels(); renderer.render(scene, camera); callbacks.rendered?.(time); dirty = false; }
    // A paused, settled view sleeps; interaction/change resumes it.
    if (controls.autoRotate || tween || animatedEdge || changed) schedule();
  }
  function schedule() { if (!frame && !disposed && onScreen && !document.hidden) frame = requestAnimationFrame(render); }
  function resize() { const rect = host.getBoundingClientRect(); width = Math.max(1, rect.width); height = Math.max(1, rect.height); renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix(); dirty = true; schedule(); }
  resize(); framePoints(positions, false);
  const observer = new ResizeObserver(resize); observer.observe(host);
  const intersection = new IntersectionObserver(entries => { onScreen = entries[0]?.isIntersecting ?? true; if (onScreen) { dirty = true; schedule(); } else { cancelAnimationFrame(frame); frame = 0; } }); intersection.observe(host);
  const visibility = () => { if (document.hidden) { cancelAnimationFrame(frame); frame = 0; } else { dirty = true; schedule(); } }; document.addEventListener("visibilitychange", visibility);
  const stop = () => { callbacks.hover(""); tween = null; controls.autoRotate = false; callbacks.pause(); schedule(); };
  const change = () => { dirty = true; schedule(); };
  controls.addEventListener("start", stop); controls.addEventListener("change", change);
  const lost = (event: Event) => { event.preventDefault(); callbacks.failure("A conexão 3D foi interrompida. As mesmas relações continuam na Lista."); }; renderer.domElement.addEventListener("webglcontextlost", lost);
  function pick(clientX: number, clientY: number): Selection {
    const rect = host.getBoundingClientRect(), x = clientX - rect.left, y = clientY - rect.top;
    const project = (point: THREE.Vector3) => { const p = point.clone().project(camera); return { x: (p.x + 1) * width / 2, y: (1 - p.y) * height / 2, z: p.z }; };
    let best: { id: string; distance: number; z: number } | null = null;
    for (const item of nodeObjects) { if (!item.visible) continue; const p = project(item.mesh.position), distance = Math.hypot(x - p.x, y - p.y); const depth = Math.abs(item.mesh.position.clone().applyMatrix4(camera.matrixWorldInverse).z); const radius = Math.max(23, 5.5 * height / (2 * Math.max(1, depth) * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) + 8); if (p.z < 1 && p.z > -1 && distance < radius && (!best || distance < best.distance)) best = { id: item.node.id, distance, z: p.z }; }
    if (best) return { kind: "node", id: best.id };
    let edgeHit: { id: string; distance: number } | null = null;
    for (const item of edgeObjects) { if (!item.visible) continue; const a = project(item.start), b = project(item.end); if (a.z > 1 || b.z > 1) continue; const dx = b.x - a.x, dy = b.y - a.y; const t = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / Math.max(1, dx * dx + dy * dy))); const distance = Math.hypot(x - a.x - dx * t, y - a.y - dy * t); if (distance < 9 && (!edgeHit || distance < edgeHit.distance)) edgeHit = { id: item.edge.id, distance }; }
    return edgeHit ? { kind: "edge", id: edgeHit.id } : null;
  }
  const taps = createTapTracker();
  const activePointers = new Set<number>();
  let lastClick: { id: string; time: number } | null = null;
  const down = (event: PointerEvent) => { activePointers.add(event.pointerId); taps.down(event); callbacks.hover(""); };
  const up = (event: PointerEvent) => {
    activePointers.delete(event.pointerId);
    if (!taps.up(event)) { lastClick = null; return; }
    const hit = pick(event.clientX, event.clientY);
    if (hit?.kind === "node" && lastClick?.id === hit.id && event.timeStamp - lastClick.time < 360) { callbacks.dive(hit.id); lastClick = null; }
    else { callbacks.select(hit); lastClick = hit?.kind === "node" ? { id: hit.id, time: event.timeStamp } : null; }
  };
  const cancel = (event: PointerEvent) => { activePointers.delete(event.pointerId); taps.cancel(event.pointerId); lastClick = null; };
  let hoverFrame = 0;
  const move = (event: PointerEvent) => { taps.move(event); if (activePointers.size || event.pointerType === "touch" || hoverFrame) return; const x = event.clientX, y = event.clientY; hoverFrame = requestAnimationFrame(() => { hoverFrame = 0; const hit = pick(x, y); callbacks.hover(hit?.kind === "node" ? nodes.find(node => node.id === hit.id)?.label ?? "" : hit ? edges.find(edge => edge.id === hit.id)?.statement ?? "" : ""); }); };
  const leave = () => callbacks.hover("");
  const canvas = renderer.domElement;
  canvas.addEventListener("pointerdown", down); canvas.addEventListener("pointerup", up); canvas.addEventListener("pointercancel", cancel); canvas.addEventListener("pointermove", move); canvas.addEventListener("pointerleave", leave);
  schedule();
  return {
    select,
    reset() { diveSet = null; selected = null; litKind = null; highlight(); framePoints(positions); },
    zoom(factor) { stop(); camera.position.sub(controls.target).multiplyScalar(factor).clampLength(65, 4800).add(controls.target); change(); },
    rotate(value) { controls.autoRotate = value; if (value) tween = null; schedule(); },
    illuminate(kind) { litKind = kind; highlight(); },
    dive(id, depth) { diveSet = new Set(neighborhoodIds(id, edges, depth)); highlight(); framePoints(positions.filter(point => diveSet!.has(point.id))); },
    dispose() { disposed = true; cancelAnimationFrame(frame); cancelAnimationFrame(hoverFrame); observer.disconnect(); intersection.disconnect(); document.removeEventListener("visibilitychange", visibility); controls.removeEventListener("start", stop); controls.removeEventListener("change", change); controls.dispose(); canvas.removeEventListener("webglcontextlost", lost); canvas.removeEventListener("pointerdown", down); canvas.removeEventListener("pointerup", up); canvas.removeEventListener("pointercancel", cancel); canvas.removeEventListener("pointermove", move); canvas.removeEventListener("pointerleave", leave); scene.clear(); resources.forEach(resource => resource.dispose()); renderer.dispose(); renderer.forceContextLoss(); canvas.remove(); },
  };
}

export default function GraphCanvas3D({ nodes, edges, selection, onSelect, onFailure }: Props) {
  const host = useRef<HTMLDivElement>(null), root = useRef<HTMLDivElement>(null), engine = useRef<Engine | null>(null);
  const callbacks = useRef({ onSelect, onFailure });
  const rotationPreference = useRef(true);
  const diveRef = useRef<{ id: string; depth: number } | null>(null);
  const [rotating, setRotating] = useState(true), [hover, setHover] = useState("");
  const [lit, setLit] = useState<NodeKind | null>(null), [immersive, setImmersive] = useState(false);
  const [dive, setDive] = useState<{ id: string; depth: number } | null>(null);
  const points = useMemo(() => spatialLayout(nodes, edges), [nodes, edges]);
  const ordered = useMemo(() => [...nodes].sort((a, b) => a.label.localeCompare(b.label, "pt-BR")), [nodes]);
  useEffect(() => { callbacks.current = { onSelect, onFailure }; }, [onSelect, onFailure]);
  useEffect(() => {
    if (!host.current) return;
    let scene: Engine | null = null;
    try { scene = createGraphRenderer(host.current, nodes, edges, points, { select: value => { if (!value) { diveRef.current = null; setDive(null); setLit(null); scene?.reset(); } callbacks.current.onSelect(value); }, dive: id => { callbacks.current.onSelect({ kind: "node", id }); diveRef.current = { id, depth: 1 }; setDive(diveRef.current); scene?.dive(id, 1); }, pause: () => { rotationPreference.current = false; setRotating(false); }, hover: setHover, failure: reason => callbacks.current.onFailure(reason) }); engine.current = scene; scene.rotate(rotationPreference.current); }
    catch { callbacks.current.onFailure("O 3D não abriu neste navegador. Você pode explorar as mesmas conexões na Lista."); }
    return () => { scene?.dispose(); engine.current = null; };
  }, [nodes, edges, points]);
  useEffect(() => {
    if (selection) engine.current?.select(selection); else engine.current?.reset();
    const current = diveRef.current;
    if (!current && selection) return;
    const visible = current ? new Set(neighborhoodIds(current.id, edges, current.depth)) : null;
    const ids = selection?.kind === "node" ? [selection.id] : selection?.kind === "edge" ? edges.filter(edge => edge.id === selection.id).flatMap(edge => [edge.from_node.id, edge.to_node.id]) : [];
    if (!selection || visible && ids.some(id => !visible.has(id))) {
      diveRef.current = null;
      const frame = requestAnimationFrame(() => { setDive(null); if (!selection) setLit(null); });
      return () => cancelAnimationFrame(frame);
    }
  }, [selection, nodes, edges]);
  function reset() { diveRef.current = null; setDive(null); setLit(null); engine.current?.reset(); onSelect(null); }
  function fullScreen() {
    const map = root.current?.closest<HTMLElement>("[data-graph-map]"); if (!map) return;
    if (document.fullscreenElement) void document.exitFullscreen();
    else if (immersive) { delete map.dataset.immersive; setImmersive(false); }
    else { map.dataset.immersive = "true"; setImmersive(true); if (map.requestFullscreen) void map.requestFullscreen().catch(() => { /* CSS viewport mode remains usable. */ }); }
  }
  useEffect(() => {
    const map = root.current?.closest<HTMLElement>("[data-graph-map]");
    const full = () => { if (!document.fullscreenElement && map) { delete map.dataset.immersive; setImmersive(false); } };
    const key = (event: KeyboardEvent) => { if (event.key !== "Escape" || event.defaultPrevented || !map?.contains(event.target as Node) && !map?.dataset.immersive && document.fullscreenElement !== map) return; if (document.fullscreenElement) void document.exitFullscreen().catch(() => {}); if (map?.dataset.immersive) { delete map.dataset.immersive; setImmersive(false); } diveRef.current = null; setDive(null); setLit(null); engine.current?.reset(); callbacks.current.onSelect(null); };
    document.addEventListener("fullscreenchange", full); document.addEventListener("keydown", key);
    return () => { document.removeEventListener("fullscreenchange", full); document.removeEventListener("keydown", key); if (map) delete map.dataset.immersive; };
  }, []);
  function keyboard(event: React.KeyboardEvent<HTMLButtonElement>, id: string) {
    if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault(); const ids = neighbors(id, edges).nodeIds; if (!ids.length) return;
    const next = ids[event.key === "ArrowUp" || event.key === "ArrowLeft" ? ids.length - 1 : 0];
    onSelect({ kind: "node", id: next });
    requestAnimationFrame(() => root.current?.querySelector<HTMLButtonElement>(`[data-key-node="${CSS.escape(next)}"]`)?.focus());
  }
  const node = selection?.kind === "node" ? nodes.find(item => item.id === selection.id) : null;
  const edge = selection?.kind === "edge" ? edges.find(item => item.id === selection.id) : null;
  return <div ref={root} className={styles.stage}>
    <div className={styles.host} ref={host} data-graph-canvas-host />
    <div className={styles.caption}><strong>Entre nas conexões.</strong><span>{nodes.length} nós · {edges.length} relações · Esferas de tamanho igual</span></div>
    <div className={styles.keyboard} data-graph-keyboard aria-label="Nós da rede por teclado">{ordered.map(item => <button type="button" key={item.id} data-key-node={item.id} data-graph-node-id={item.id} onClick={() => onSelect({ kind: "node", id: item.id })} onKeyDown={event => keyboard(event, item.id)}>{item.label} · {NODE_LABELS[item.kind]} · Enter para explorar, setas para os vizinhos</button>)}</div>
    {hover && <div className={styles.tooltip} role="tooltip">{hover}</div>}
    {dive && <div className={styles.dive}><span>Vizinhança de {dive.depth} {dive.depth === 1 ? "nível" : "níveis"}</span><button type="button" onClick={() => { const next = { ...dive, depth: dive.depth + 1 }; diveRef.current = next; setDive(next); engine.current?.dive(next.id, next.depth); }}>Expandir mais um nível</button><button type="button" onClick={reset}>Sair do mergulho</button></div>}
    <GraphLegend active={lit} onChange={value => { setLit(value); engine.current?.illuminate(value); }} />
    <div className={styles.key} data-graph-line-key aria-label="Estilos das relações"><span><i />Consolidado</span><span><i className={styles.dashed} />Debatido</span><span><i className={styles.dotted} />Especulativo</span><br />Consenso declarado pelo autor · ? sentido incerto · seta: origem → destino</div>
    <GraphControls rotating={rotating} immersive={immersive} onZoom={factor => engine.current?.zoom(factor)} onReset={reset} onRotate={() => { const next = !rotating; rotationPreference.current = next; setRotating(next); engine.current?.rotate(next); }} onFullscreen={fullScreen} />
    <p className={styles.srOnly} aria-live="polite" aria-atomic="true">{node ? `${node.label}. ${neighbors(node.id, edges).incoming.length} ligações chegam e ${neighbors(node.id, edges).outgoing.length} saem.` : edge ? `${edge.from_node.label} para ${edge.to_node.label}. ${edge.statement}` : "Visão geral da rede. Nenhum ponto selecionado."}</p>
  </div>;
}

function GraphLegend({ active, onChange }: { active: NodeKind | null; onChange: (kind: NodeKind | null) => void }) {
  return <div className={styles.legend} data-graph-legend role="group" aria-label="Iluminar por tipo de nó">{kinds.map(kind => <button type="button" key={kind} aria-pressed={active === kind} onClick={() => onChange(active === kind ? null : kind)} style={{ "--node-color": `var(${tokens[kind]})` } as CSSProperties}><i aria-hidden="true" />{NODE_LABELS[kind]}</button>)}</div>;
}

function GraphControls({ rotating, immersive, onZoom, onReset, onRotate, onFullscreen }: { rotating: boolean; immersive: boolean; onZoom: (factor: number) => void; onReset: () => void; onRotate: () => void; onFullscreen: () => void }) {
  return <div className={styles.controls} data-graph-controls role="group" aria-label="Controles da rede"><button type="button" onClick={() => onZoom(.8)} aria-label="Aproximar a rede">+</button><button type="button" onClick={() => onZoom(1.25)} aria-label="Afastar a rede">−</button><button type="button" onClick={onReset}>Ver tudo</button><button type="button" onClick={onRotate} aria-pressed={rotating}>{rotating ? "Pausar giro" : "Girar"}</button><button type="button" onClick={onFullscreen} aria-pressed={immersive}>{immersive ? "Sair da tela cheia" : "Tela cheia"}</button></div>;
}
