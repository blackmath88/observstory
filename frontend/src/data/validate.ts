import Ajv2020 from "ajv/dist/2020";
import knowledgeSchema from "../../../schema/knowledge-v1.json";
import sceneSchema from "../../../schema/scene-v1.json";
import snapshotSchema from "../../../schema/snapshot-v1.json";
import workspaceSchema from "../../../schema/workspace-v1.json";
import type { SourceName } from "./types";

/** One validator per contract, compiled from the repository's own JSON Schemas so the frontend
 *  and the Python producer cannot drift apart silently. */
const ajv = new Ajv2020({ allErrors: true, strict: false });
const compiled = {
  workspace: ajv.compile(workspaceSchema),
  snapshot: ajv.compile(snapshotSchema),
  scene: ajv.compile(sceneSchema),
  knowledge: ajv.compile(knowledgeSchema),
} as const;

export type Validation = { ok: true; contract: "full" | "identity-only" } | { ok: false; issues: string[] };

const MAX_ISSUES = 8;

export function validate(name: SourceName, data: unknown): Validation {
  if (name === "event") return validateEventIdentity(data);
  const check = compiled[name];
  if (check(data)) {
    if (name === "workspace") {
      const issues = workspaceIssues(data as unknown as import("./types").Workspace);
      if (issues.length) return { ok: false, issues };
    }
    return { ok: true, contract: "full" };
  }
  const issues = (check.errors ?? []).slice(0, MAX_ISSUES).map((e) => `${e.instancePath || "/"} ${e.message ?? "is invalid"}`);
  return { ok: false, issues };
}

/** `observstory.event-schedule/v0` has no schema file in this repository yet: check only the
 *  fields that identify a usable schedule, and report the contract as identity-only. */
function validateEventIdentity(data: unknown): Validation {
  const issues: string[] = [];
  if (!isRecord(data)) return { ok: false, issues: ["/ must be an object"] };
  if (typeof data.title !== "string") issues.push("/title must be a string");
  if (typeof data.timezone !== "string") issues.push("/timezone must be a string");
  if (!Array.isArray(data.events)) issues.push("/events must be an array");
  else
    data.events.forEach((e, i) => {
      if (!isRecord(e) || typeof e.id !== "string" || typeof e.label !== "string" || typeof e.start_at !== "string") {
        issues.push(`/events/${i} needs id, label and start_at strings`);
      }
    });
  const deadline = data.coding_deadline;
  if (deadline != null && (!isRecord(deadline) || typeof deadline.at !== "string")) issues.push("/coding_deadline/at must be a string");
  return issues.length ? { ok: false, issues: issues.slice(0, MAX_ISSUES) } : { ok: true, contract: "identity-only" };
}

export function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function workspaceIssues(data: import("./types").Workspace): string[] {
  const issues: string[] = [];
  const byId = new Map(data.records.map((r) => [r.id, r]));
  if (byId.size !== data.records.length) issues.push("Duplicate workspace record IDs");
  for (const r of data.records) {
    const p = r.planned;
    if (p) {
      const pattern = { year: /^\d{4}$/, month: /^\d{4}-(0[1-9]|1[0-2])$/, day: /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/ }[
        p.precision
      ];
      if ([p.start, p.end].some((v) => v !== undefined && (!pattern.test(v) || !Number.isFinite(Date.parse(v)))))
        issues.push(`${r.id}: invalid date or precision`);
      if (p.end && p.end < p.start) issues.push(`${r.id}: reversed planned interval`);
    }
  }
  const visited = new Set<string>();
  const stack = new Set<string>();
  function visit(id: string): boolean {
    if (stack.has(id)) return false;
    if (visited.has(id)) return true;
    stack.add(id);
    for (const child of byId.get(id)?.members ?? []) if (byId.has(child) && !visit(child)) return false;
    stack.delete(id);
    visited.add(id);
    return true;
  }
  for (const id of byId.keys())
    if (!visit(id)) {
      issues.push("Cyclic workspace membership");
      break;
    }
  for (const e of data.relations)
    if (!byId.has(e.from) || !byId.has(e.to) || e.from === e.to) issues.push("Invalid relationship endpoints");
  return issues;
}
