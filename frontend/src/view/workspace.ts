import type { Bundle, WorkspaceRecord } from "../data/types";

export interface RecordView extends WorkspaceRecord {
  basis: string;
  material: { title: string; url?: string }[];
  observed?: string;
}

/** Stable source order, never activity order. Knowledge status is document status,
 * not a lifecycle state. Folder membership never creates conceptual relationships. */
export function workspace(bundle: Bundle) {
  const knowledge = bundle.knowledge.status === "ok" ? bundle.knowledge.data : null;
  const scene = bundle.scene.status === "ok" ? bundle.scene.data : null;
  const declaration = bundle.workspace?.status === "ok" ? bundle.workspace.data : null;
  const records: RecordView[] = (declaration?.records ?? []).map((r) => ({
    ...r,
    basis: "Declared workspace",
    material: (r.sources ?? []).map((url) => ({ title: "Source declaration", url })),
  }));
  const ids = new Set(records.map((r) => r.id));
  for (const k of knowledge?.records ?? []) {
    if (ids.has(k.id)) continue;
    records.push({
      id: k.id,
      title: k.title,
      kind: k.type,
      context: k.excerpt ?? undefined,
      basis: `Selected knowledge · document ${k.status}`,
      material: k.url ? [{ title: k.path ?? k.title, url: k.url }] : [],
    });
  }
  // Area groupings are the deterministic, explicitly derived implementation fallback.
  for (const g of [...(scene?.groups ?? [])].sort((a, b) => a.id.localeCompare(b.id))) {
    const id = `area:${g.id}`;
    if (ids.has(id)) continue;
    records.push({
      id,
      title: g.label,
      kind: "implementation",
      basis: "Derived area grouping · lifecycle undeclared",
      context: g.path,
      observed: g.last_activity_at ?? undefined,
      members: g.nodes.map((n) => `observed:${n}`),
      material: [],
    });
  }
  for (const n of [...(scene?.nodes ?? [])].sort((a, b) => a.id.localeCompare(b.id))) {
    records.push({
      id: `observed:${n.id}`,
      title: n.label,
      kind: "implementation",
      basis: `Observed ${n.kind} · ${n.status} (artifact state)`,
      observed: n.last_activity_at ?? undefined,
      material: n.url ? [{ title: n.ref, url: n.url }] : [],
    });
  }
  const areas = records.filter((r) => r.id.startsWith("area:"));
  if (areas.length)
    records.push({
      id: "derived:implementation",
      title: "Repository implementation",
      kind: "implementation",
      basis: "Derived from observed area groupings",
      context: "Repository artifacts grouped by area; activity is not lifecycle or deployment.",
      members: areas.map((r) => r.id),
      material: [],
    });
  const byId = new Map(records.map((r) => [r.id, r]));
  const memberships = new Set(records.flatMap((r) => r.members ?? []).filter((id) => byId.has(id)));
  const relations = declaration?.relations ?? [];
  const roots = records.filter((r) => !memberships.has(r.id));
  const warnings: string[] = [];
  if (!declaration)
    warnings.push(
      `Workspace ${bundle.workspace?.status ?? "missing"}. Showing derived groupings and selected knowledge; lifecycle and resume context remain undeclared.`,
    );
  if (knowledge && !knowledge.complete) warnings.push("Project knowledge is partial.");
  if (bundle.knowledge.status !== "ok") warnings.push(`Project knowledge ${bundle.knowledge.status}.`);
  if (bundle.snapshot.status !== "ok" || bundle.scene.status !== "ok")
    warnings.push("Activity is unavailable. Missing observations are not zero activity.");
  const snapshot = bundle.snapshot.status === "ok" ? bundle.snapshot.data : null;
  if (snapshot?.provenance.degraded.length) warnings.push(`Collection partial: ${snapshot.provenance.degraded.join("; ")}`);
  const revisions = [snapshot?.trigger?.sha, knowledge?.resolved_commit, declaration?.source_commit].filter((s): s is string => !!s);
  if (new Set(revisions).size > 1) warnings.push("Source commits differ. These inputs are not an atomic project state.");
  for (const r of records)
    for (const member of r.members ?? []) if (!byId.has(member)) warnings.push(`${r.title}: member ${member} is unavailable.`);
  for (const edge of relations)
    if (!byId.has(edge.from) || !byId.has(edge.to)) warnings.push("A declared relationship has an unavailable endpoint.");
  const direction = knowledge?.records.find((r) => r.id === knowledge.selection?.current_direction?.record);
  return { records, roots, byId, relations, warnings, direction, revisions };
}

export function publicURL(url?: string) {
  return url?.startsWith("https://") ? url : undefined;
}

/** Navigation categories use record kinds only. They imply no relationship or lifecycle. */
export const FOCUSES = [
  { id: "all", label: "All work" },
  { id: "research", label: "Research" },
  { id: "concept", label: "Concepts" },
  { id: "plan", label: "Planning" },
  { id: "implementation", label: "Implementation" },
  { id: "context", label: "Other context" },
] as const;
export type Focus = (typeof FOCUSES)[number]["id"];
export function readFocus(value: string | null): Focus {
  return FOCUSES.find((f) => f.id === value)?.id ?? "all";
}
export function recordFocus(record: RecordView): Focus {
  return ["research", "concept", "plan", "implementation"].includes(record.kind) ? (record.kind as Focus) : "context";
}

export function scopeWorkspace(model: ReturnType<typeof workspace>, focus: Focus, query: string) {
  const words = query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  const matches = model.records.filter((r) => {
    const text = [
      r.title,
      r.kind,
      r.context,
      r.basis,
      r.status,
      r.attention,
      r.resume?.stopping_point,
      r.resume?.next_action,
      ...r.material.map((s) => s.title),
    ]
      .join(" ")
      .toLocaleLowerCase();
    return (focus === "all" || recordFocus(r) === focus) && words.every((word) => text.includes(word));
  });
  const matching = new Set(matches.map((r) => r.id));
  // Retain declared/derived ancestors for orientation without changing membership.
  const visible = new Set(matching);
  let changed = true;
  while (changed) {
    changed = false;
    for (const r of model.records) {
      if (!visible.has(r.id) && r.members?.some((id) => visible.has(id))) {
        visible.add(r.id);
        changed = true;
      }
    }
  }
  return { matches, matching, visible, active: focus !== "all" || words.length > 0 };
}
