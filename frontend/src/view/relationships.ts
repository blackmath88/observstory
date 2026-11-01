import type { Bundle } from "../data/types";
import { isRecord } from "../data/validate";
import { publicURL, type RecordView } from "./workspace";

export interface RelationshipEndpoint {
  id: string | null;
  title: string;
  available: boolean;
}
export interface RelationshipQuote {
  id: string;
  path: string;
  quote: string | null;
  found: boolean | null;
  line: number | null;
  url?: string;
}
export interface PublishedRelationship {
  id: string;
  source: "Project knowledge" | "Workspace declaration";
  from: RelationshipEndpoint;
  to: RelationshipEndpoint;
  verb: string;
  basis: string;
  resolved: boolean | null;
  declarations: RelationshipQuote[];
  manifestURL?: string;
  unreadable: boolean;
}
const string = (value: unknown) => (typeof value === "string" ? value : null);

/** Construct only a pinned public Git source link; no main/latest or path traversal fallback. */
export function manifestURL(repository: unknown, commit: unknown, path: unknown): string | undefined {
  if (
    typeof repository !== "string" ||
    !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository) ||
    repository.split("/").some((p) => p === "." || p === "..")
  )
    return;
  if (typeof commit !== "string" || !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/i.test(commit)) return;
  if (
    typeof path !== "string" ||
    [...path].some((character) => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127) ||
    path.split("/").some((part) => !part || part === "." || part === "..")
  )
    return;
  return `https://github.com/${repository}/blob/${commit}/${path.split("/").map(encodeURIComponent).join("/")}`;
}

/** Preserve published direction, source order, basis, quote matching and exporter resolution.
 * Missing endpoints never become records or membership; malformed fields stay qualified. */
export function publishedRelationships(bundle: Bundle, records: RecordView[]) {
  const byId = new Map(records.map((r) => [r.id, r]));
  function endpoint(value: unknown): RelationshipEndpoint {
    const id = string(value);
    const record = id === null ? undefined : byId.get(id);
    return { id, title: record?.title ?? id ?? "Endpoint ID unavailable", available: !!record };
  }
  const knowledge = bundle.knowledge.status === "ok" ? bundle.knowledge.data : null;
  const declaration = bundle.workspace.status === "ok" ? bundle.workspace.data : null;
  const knowledgeLinks = Array.isArray(knowledge?.relationships) ? knowledge.relationships : [];
  const knowledgeManifest = manifestURL(knowledge?.repository, knowledge?.resolved_commit, knowledge?.source?.manifest_path);
  const workspaceManifest = manifestURL(
    bundle.snapshot.status === "ok" ? bundle.snapshot.data.repository.full_name : null,
    declaration?.source_commit,
    ".observstory/workspace.json",
  );
  const links: PublishedRelationship[] = knowledgeLinks.map((value, index) => {
    const raw = isRecord(value) ? value : {};
    const basis = isRecord(raw.basis) ? raw.basis : {};
    const from = endpoint(raw.from);
    const to = endpoint(raw.to);
    const verb = string(raw.rel);
    const declarations: RelationshipQuote[] = (Array.isArray(basis.declarations) ? basis.declarations : []).map((value, quoteIndex) => {
      const quote = isRecord(value) ? value : {};
      return {
        id: `knowledge:${index}:quote:${quoteIndex}`,
        path: string(quote.path) ?? "Source path unavailable",
        quote: string(quote.quote),
        found: typeof quote.found === "boolean" ? quote.found : null,
        line: typeof quote.line === "number" && Number.isInteger(quote.line) && quote.line > 0 ? quote.line : null,
        url: publicURL(string(quote.url) ?? undefined),
      };
    });
    return {
      id: `knowledge:${index}`,
      source: "Project knowledge",
      from,
      to,
      verb: verb ?? "Relationship label unavailable",
      basis: string(basis.kind) ?? "Basis unavailable",
      resolved: typeof raw.resolved === "boolean" ? raw.resolved : null,
      declarations,
      manifestURL: knowledgeManifest,
      unreadable: !from.id || !to.id || !verb,
    };
  });
  for (const [index, edge] of (declaration?.relations ?? []).entries()) {
    links.push({
      id: `workspace:${index}`,
      source: "Workspace declaration",
      from: endpoint(edge.from),
      to: endpoint(edge.to),
      verb: edge.type,
      basis: "Declared workspace",
      resolved: null,
      declarations: [],
      manifestURL: workspaceManifest,
      unreadable: false,
    });
  }
  return {
    links,
    knowledgeState: knowledge
      ? Array.isArray(knowledge.relationships)
        ? knowledge.complete
          ? "loaded"
          : "partial"
        : "relationships unavailable"
      : bundle.knowledge.status,
    workspaceState: declaration ? "loaded" : bundle.workspace.status,
    unplaced: links.filter((edge) => !edge.from.available && !edge.to.available).length,
  };
}
export type RelationshipEvidence = ReturnType<typeof publishedRelationships>;
export function relationshipsFor(evidence: RelationshipEvidence, id: string) {
  return evidence.links.filter((edge) => edge.from.id === id || edge.to.id === id);
}
