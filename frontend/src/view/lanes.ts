import type { Scene, SceneEdge, SceneGroup, SceneNode, SceneZone } from "../data/types";

export interface LaneArea {
  group: SceneGroup;
  nodes: SceneNode[];
  /** Work items drawn in another area that also change this one. */
  alsoActive: SceneNode[];
}

export interface Lane {
  zone: SceneZone;
  number: number;
  areas: LaneArea[];
}

export interface Lanes {
  active: Lane[];
  quiet: Lane[];
  edgesByNode: Map<string, SceneEdge[]>;
}

/** Lanes in configured order. A lane with nothing to show collapses into the quiet list instead
 *  of taking a full empty column; each work item is drawn once, in its primary area. */
export function lanes(scene: Scene): Lanes {
  const nodes = new Map(scene.nodes.map((n) => [n.id, n]));
  const groups = new Map(scene.groups.map((g) => [g.id, g]));
  const zones = [...scene.zones].sort((a, b) => a.order - b.order);
  const all = zones.map((zone, i) => ({
    zone,
    number: i + 1,
    areas: zone.groups
      .map((gid) => groups.get(gid))
      .filter((g): g is SceneGroup => !!g)
      .map((group) => ({
        group,
        nodes: group.nodes.map((id) => nodes.get(id)).filter((n): n is SceneNode => !!n),
        alsoActive: group.also_active.map((id) => nodes.get(id)).filter((n): n is SceneNode => !!n),
      })),
  }));
  const edgesByNode = new Map<string, SceneEdge[]>();
  for (const e of scene.edges) for (const id of [e.from, e.to]) edgesByNode.set(id, [...(edgesByNode.get(id) ?? []), e]);
  const shows = (l: Lane) => l.areas.some((a) => a.nodes.length > 0 || a.alsoActive.length > 0);
  return { active: all.filter(shows), quiet: all.filter((l) => !shows(l)), edgesByNode };
}
