# Claude / Orca / NUC — Observatory pixel-design studies
Date: 31 October 2026
Scope: design studies and implementation-ready visual language. No production rewrite or deployment in this slice.

You previously developed Weavr and soul.me's visual worlds. Bring the same meaning and restraint to Observstory, with its own identity.

## Read first
- This repo: AGENTS.md, ARCHITECTURE.md, docs/ui/design-language.md, docs/ui/scene-grammar.md, docs/integrations/weavr.md.
- docs/plans/OBSERVATORY-REWRITE.md.
- blackmath88/development-practice: PRACTICE.md and profiles/product.md.
- Weavr: DESIGN.md, design/ori/, design/tanabata/brand-kit.html.
- soul.me: brand/README.md and brand/brand-kit.html.
Inspect current local state and preserve others' work. Do not assume the NUC checkout path, a running Orca session or a Weavr Mission exists.

## Product context
Observstory provides shared situational awareness for people and agents building software together. It collects GitHub metadata and produces typed, evidence-backed project state.
Typical journey: open the dashboard → see relevant work → notice overlap or a dependency → select it → inspect evidence → discuss or act in the appropriate tool.
Signals concern work, not people: overlap, stale activity, waiting dependencies and rapid change streams. It also shows explicitly declared plans and commitments.
Observed, derived, heuristic and declared are distinct. Observstory observes; it does not dispatch agents or decide who may act.

First real use case: a BaselHack weekend with two repositories:
- baselhack26-open-presence: Photo Frame Commons, preserving the circumstances, voices and provenance behind useful community knowledge.
- baselhack26-knowledge-lab: separate graph and retrieval exploration.
The dashboard currently observes Open Presence only. A file-history replay exists there. Cross-repo graph growth and live Observatory history are not already connected.

## Art direction
An actual observatory: a small pixel dome/telescope, a quiet landscape, a warm window, and the feeling of mapping a field of stars.
Owner references suggest: the calm composition of a small observatory under a vast night sky; a readable illustrated telescope silhouette; warm light in an otherwise cool environment.
The owner will supply visual templates shortly. Treat those as pending input, not missing permission to explore. Existing chat image references may not be available on the NUC; do not pretend you inspected them.
Premium means clear hierarchy, excellent spacing, typography, interaction and state handling. Use GitHub-familiar density and navigation with a distinctive visual identity.
Pixel art surrounds the working interface. Data and controls stay crisp and readable. Do not copy Weavr's loom/Wanderer, soul.me's fox or their semantic colour rules.

## Explore three coherent studies
A. Observatory courtyard: small dome and horizon beside a restrained working surface.
B. Telescope instrument: compact telescope/coordinate motifs, with focus tied to selection.
C. Star atlas: a precise chart with stable groupings and a small observatory identity.
Use the same labelled synthetic project data in all three. Show quiet, overlapping-work and historical-replay states. Include enough real UI to assess reading and interaction; avoid illustration-only moodboards.

## Candidate visual law
Every meaningful mark leads to evidence.
Distinguish decorative scenery from interactive data. Data stars need labels, selection and keyboard/list equivalents. Connections mean declared dependency or derived overlap, not arbitrary proximity.
Show explicit collection timestamp and coverage. No telescope scanning animation implies live collection unless that state is actually available.
Decorative animation is optional, stops for reduced motion, and carries no exclusive information.
Focus may turn the telescope; replay may change the plotted state. Text labels always express the state.
Do not turn activity volume into brightness, importance or a ranking of people.

## Deliver
- A self-contained study page in design/observatory/ with a README and clear synthetic-data notice.
- Three comparable directions plus quiet/overlap/replay examples; responsive demonstration and keyboard-accessible controls.
- Deterministic procedural pixel assets where practical, with editable source, consistent pixel scale and small palette.
- Proposed tokens, typography, icon rules, state-to-visual mapping and motion/reduced-motion rules.
- Screenshots at desktop and mobile, generated and actually inspected.
- A recommendation with trade-offs and an explicit list of decisions awaiting owner templates.
- A handoff explaining how assets fit the future typed frontend without altering producer schemas.

Work on a dedicated design branch; preserve other branches and changes. Commit the study, push the branch if repository access permits, and report the exact review location. Do not merge or deploy. Do not begin the TanStack rewrite in this design slice.
