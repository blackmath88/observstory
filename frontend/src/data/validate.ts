import Ajv2020 from "ajv/dist/2020";
import knowledgeSchema from "../../../schema/knowledge-v1.json";
import sceneSchema from "../../../schema/scene-v1.json";
import snapshotSchema from "../../../schema/snapshot-v1.json";
import type { SourceName } from "./types";

/** One validator per contract, compiled from the repository's own JSON Schemas so the frontend
 *  and the Python producer cannot drift apart silently. */
const ajv = new Ajv2020({ allErrors: true, strict: false });
const compiled = {
  snapshot: ajv.compile(snapshotSchema),
  scene: ajv.compile(sceneSchema),
  knowledge: ajv.compile(knowledgeSchema),
} as const;

export type Validation = { ok: true; contract: "full" | "identity-only" } | { ok: false; issues: string[] };

const MAX_ISSUES = 8;

export function validate(name: SourceName, data: unknown): Validation {
  if (name === "event") return validateEventIdentity(data);
  const check = compiled[name];
  if (check(data)) return { ok: true, contract: "full" };
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
