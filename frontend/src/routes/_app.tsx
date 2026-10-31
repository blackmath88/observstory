import { AlertIcon, ClockIcon, DatabaseIcon, LinkExternalIcon, RepoIcon, TelescopeIcon } from "@primer/octicons-react";
import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { absolute, freshness } from "../data/freshness";
import { loadBundle, resolveDataBase } from "../data/load";
import type { Bundle } from "../data/types";
import { useNow } from "../lib/useNow";

/** Everything below this layout reads data in the browser: the shell is prerendered once and
 *  the Action drops fresh `data/*.json` beside it on every run. */
export const Route = createFileRoute("/_app")({
  ssr: false,
  loader: () => loadBundle(resolveDataBase(window.location.search, import.meta.env.DEV ? "hackathon/data/" : "./data/")),
  staleTime: Number.POSITIVE_INFINITY,
  component: AppLayout,
  pendingComponent: Pending,
  pendingMs: 150,
  errorComponent: ({ error }) => (
    <main className="container page">
      <div className="flash danger" role="alert">
        <AlertIcon size={16} />
        <div>
          <strong>The Observatory could not start.</strong>
          <p>{error instanceof Error ? error.message : String(error)}</p>
        </div>
      </div>
    </main>
  ),
});

export function problemCount(b: Bundle): number {
  return (["snapshot", "scene", "knowledge", "event"] as const).filter((k) => {
    const s = b[k].status;
    return s !== "ok" && !(s === "missing" && (k === "knowledge" || k === "event"));
  }).length;
}

function AppLayout() {
  const bundle = Route.useLoaderData();
  const now = useNow();
  const snapshot = bundle.snapshot.status === "ok" ? bundle.snapshot.data : null;
  const scene = bundle.scene.status === "ok" ? bundle.scene.data : null;
  const fullName = snapshot?.repository.full_name ?? scene?.source.repository ?? null;
  const [owner, repo] = fullName ? fullName.split("/") : [null, null];
  const repoUrl = snapshot?.repository.url ?? scene?.source.repository_url ?? null;
  const generatedAt = snapshot?.generated_at ?? scene?.source.generated_at ?? null;
  const fresh = generatedAt ? freshness(generatedAt, now) : null;
  const problems = problemCount(bundle);
  if (typeof document !== "undefined") document.title = fullName ? `${fullName} · Observatory` : "Observatory";

  return (
    <>
      <header className="repo-header">
        <div className="container">
          <div className="repo-title">
            {fullName ? (
              <span className="crumbs">
                <RepoIcon size={16} />{" "}
                {repoUrl ? (
                  <a className="owner" href={repoUrl.replace(/\/[^/]+$/, "")}>
                    {owner}
                  </a>
                ) : (
                  <span className="owner">{owner}</span>
                )}
                <span className="sep">/</span>
                {repoUrl ? (
                  <a className="name" href={repoUrl}>
                    {repo}
                  </a>
                ) : (
                  <strong className="name">{repo}</strong>
                )}
              </span>
            ) : (
              <span className="crumbs">
                <RepoIcon size={16} /> <strong className="name">Observatory</strong>
              </span>
            )}
            {snapshot?.repository.visibility && <span className="label">{capitalise(snapshot.repository.visibility)}</span>}
            <div className="repo-meta">
              {snapshot && (
                <span className="counts">
                  <span className="sr-only">Project summary: </span>
                  <b>{snapshot.summary.in_flight}</b> in flight ·{" "}
                  <b className={snapshot.summary.signals.overlap ? "attention-text" : undefined}>{snapshot.summary.signals.overlap}</b>{" "}
                  {snapshot.summary.signals.overlap === 1 ? "overlap" : "overlaps"} ·{" "}
                  <b className={snapshot.summary.signals.waiting ? "attention-text" : undefined}>{snapshot.summary.signals.waiting}</b>{" "}
                  waiting · <b>{snapshot.summary.signals.stale}</b> stale
                </span>
              )}
              {fresh && generatedAt ? (
                <span
                  title={`Snapshot generated ${absolute(generatedAt)}`}
                  style={{ display: "inline-flex", gap: 6, alignItems: "center" }}
                >
                  <ClockIcon size={16} />
                  snapshot {fresh.label}
                  {fresh.stale && <span className="label caution">stale</span>}
                </span>
              ) : (
                <span className="label danger">no snapshot</span>
              )}
              <span>static · not live</span>
            </div>
          </div>
          {scene?.source.title && <p className="repo-sub">{scene.source.title}</p>}
          <nav className="underline-nav" aria-label="Observatory">
            <Link to="/" activeOptions={{ exact: true }} activeProps={{ "aria-current": "page" }}>
              <TelescopeIcon size={16} />
              Overview
            </Link>
            <Link to="/sources" activeProps={{ "aria-current": "page" }}>
              <DatabaseIcon size={16} />
              Data sources
              {problems > 0 && (
                <span className="counter" title={`${problems} input${problems > 1 ? "s" : ""} need attention`}>
                  {problems}
                </span>
              )}
            </Link>
            {bundle.views.length > 0 && (
              <span className="nav-extra">
                {bundle.views.map((v) => (
                  <a key={v.href} href={v.href}>
                    {v.label} <LinkExternalIcon size={12} />
                  </a>
                ))}
              </span>
            )}
          </nav>
        </div>
      </header>
      <main className="container page">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="container">
          <span>Observstory describes work, not people.</span>
          <span>
            Data from <code className="mono">{bundle.base}</code> · loaded {absolute(bundle.receivedAt)}
          </span>
        </div>
      </footer>
    </>
  );
}

function Pending() {
  return (
    <main className="container page" aria-busy="true" aria-label="Loading the snapshot">
      <div className="skeleton" style={{ height: 32, width: "40%" }} />
      <div className="skeleton" style={{ height: 88 }} />
      <div className="skeleton" style={{ height: 240 }} />
    </main>
  );
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
