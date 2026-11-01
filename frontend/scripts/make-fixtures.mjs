// Builds the frontend's dev/test fixtures from the repository's synthetic demo states.
//   node scripts/make-fixtures.mjs
// Everything here is synthetic (northstar/* repositories, invented handles). Real consumer
// data is never committed; see fixtures/README.md.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..");
const out = join(here, "..", "fixtures");
const state = (name, kind) => readFileSync(join(repo, "demo", "states", `${name}.${kind}.json`), "utf8");
const put = (fixture, file, text) => {
  mkdirSync(join(out, fixture, "data"), { recursive: true });
  writeFileSync(join(out, fixture, "data", file), text);
};

// hackathon: active work, a declared mission rail, and a synthetic event schedule
put("hackathon", "snapshot.json", state("saturday-morning", "snapshot"));
put("hackathon", "scene.json", state("saturday-morning", "scene"));
put(
  "hackathon",
  "event.json",
  `${JSON.stringify(
    {
      schema: "observstory.event-schedule/v0",
      title: "Synthetic hackathon · event timetable",
      timezone: "Europe/Zurich",
      starts_on: "2026-10-09",
      ends_on: "2026-10-11",
      source: { kind: "synthetic_fixture", independently_verified: false, note: "Invented for frontend tests." },
      coding_deadline: { event_id: "sun-hands-off", at: "2026-10-11T12:00:00+02:00", label: "Hands off!", basis: "synthetic_fixture" },
      events: [
        { id: "sat-breakfast", label: "Breakfast", start_at: "2026-10-10T08:00:00+02:00", precision: "exact" },
        { id: "sun-hands-off", label: "Hands off!", start_at: "2026-10-11T12:00:00+02:00", precision: "exact" },
        { id: "sun-presentations", label: "Presentations", start_at: "2026-10-11T13:00:00+02:00", precision: "exact" },
      ],
      diagnostics: [],
    },
    null,
    2,
  )}\n`,
);

// quiet: nothing in flight, no optional inputs published
put("quiet", "snapshot.json", state("quiet", "snapshot"));
put("quiet", "scene.json", state("quiet", "scene"));

// broken: one unsupported version, one unreadable file
const snap = JSON.parse(state("calm", "snapshot"));
snap.schema = "observstory.snapshot/v9";
put("broken", "snapshot.json", `${JSON.stringify(snap, null, 2)}\n`);
put("broken", "scene.json", '{ "schema": "observstory.scene/v1", "zones": [ \n');
console.log("fixtures written to", out);
