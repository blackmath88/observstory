import { CheckboxIcon, IssueOpenedIcon } from "@primer/octicons-react";
import type { Coordination, Issue } from "../../data/types";
import { zoned } from "../../view/time";

const STATE: Record<string, string> = {
  in_progress: "in progress",
  not_started: "not started",
  landed: "landed",
  closed: "closed",
  unlinked: "not linked to work",
  tracked_elsewhere: "tracked elsewhere",
};

/** Declared commitments and open issues. Nothing here is inferred from activity: a task with
 *  recent commits in its area is still only what was declared. */
export function RemainingWork({
  coordination,
  issues,
  timezone,
}: {
  coordination: Coordination | null | undefined;
  issues: Issue[];
  timezone?: string;
}) {
  const commitments = coordination?.commitments ?? [];
  const open = issues.filter((i) => i.state === "open");
  return (
    <section className="box" aria-labelledby="work-h">
      <div className="box-header">
        <CheckboxIcon size={16} />
        <h2 id="work-h">Remaining work</h2>
      </div>
      {commitments.length === 0 ? (
        <div className="box-row compact">
          <div className="main meta">No declared commitments yet.</div>
        </div>
      ) : (
        commitments.map((c) => (
          <div className="box-row compact" key={c.id}>
            <div className="main">
              <div>{c.text}</div>
              <div className="meta">
                {c.owner ?? "unassigned"}
                {c.due && ` · due ${timezone ? zoned(c.due, timezone) : c.due}`}
                {c.state && (
                  <>
                    {" "}
                    · <span className={c.cue ? "attention-text" : undefined}>{STATE[c.state] ?? c.state}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))
      )}
      {open.map((i) => (
        <div className="box-row compact" key={i.number}>
          <span className="item-icon">
            <IssueOpenedIcon size={16} />
          </span>
          <div className="main">
            {i.url ? <a href={i.url}>{i.title}</a> : i.title} <span className="muted">#{i.number}</span>
          </div>
        </div>
      ))}
      <div className="box-footer">
        Commitments come from people's check-ins; issues from GitHub. Nothing is marked done from activity alone.
      </div>
    </section>
  );
}
