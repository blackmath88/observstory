# Owned-host Observatory pilot

Status: **implemented and synthetic-tested; not installed on linuc**.
Tracks [Observstory #28](https://github.com/blackmath88/observstory/issues/28).

This first slice replaces GitHub-hosted refreshes with an explicit, repository-allowlisted batch runner. It does not dispatch agents, run source-repository scripts, modify GitHub, install a server, migrate Pages or change required PR checks.

## Before installing on linuc

1. Inspect current services, timers, listening ports, installed Observstory revision, disk space, git/SSH configuration and Knowledge Lab state. Do **not** blindly install duplicate services or overwrite an existing data root.
2. Use a dedicated low-privilege user and a read-only deploy key or narrowly scoped GitHub token for the synthetic pilot. Provide `OBSERVSTORY_TOKEN` via a user-owned `0600` environment file. Git source access and the API token are separate permissions.
3. Check out Observstory at an **exact reviewed commit** in `producer_root`. Update `producer_sha` to that commit. The runner rejects a dirty or mismatched producer checkout.
4. Start with an allowlisted synthetic repository. The example JSON is intentionally not usable without editing paths, name, and commit.

The runner requires Python 3.10+, git, access to the GitHub API, a committed Observstory checkout and a writable `state_root`. It uses only the Python standard library itself.

## One-off smoke test

```bash
python3 ops/linuc/refresh.py --config "$HOME/.config/observstory/host.json" \
  --repo example/synthetic-observatory-pilot
```

Observe:

- `$STATE_ROOT/status/<slug>.json`: latest attempt, `ok` or `failed`, plus degradation
- `$STATE_ROOT/public/<slug>/data/snapshot.json`: typed evidence, source commit in `trigger.sha`
- `$STATE_ROOT/public/<slug>/build.json`: pinned exact commit and refresh timestamp

The public directory name is a local filesystem convention, **not** an internet-public publication. The runner creates no HTTP listener or network route.

## Scheduling

After the synthetic smoke and failure-injection tests pass, install the supplied **user-level systemd** templates. They assume a checked-out repository in `%h/src/observstory`, a config at `%h/.config/observstory/host.json` and a secrets file at `%h/.config/observstory/secrets.env`. Adjust those paths before installation. The timer fires 30 minutes after the last service stopped; the script also uses a non-blocking flock so overlapping invocations refuse to run.

```bash
systemd-analyze verify ops/linuc/systemd/observstory-refresh.service
systemctl --user daemon-reload
systemctl --user enable --now observstory-refresh.timer
systemctl --user list-timers --all
journalctl --user -u observstory-refresh.service -n 100 --no-pager
```

These are **operator commands**, not actions performed by this PR. Review the service file and copy it into the user unit directory before running them. Never use `enable --now` on an unfamiliar host without inspecting existing units and config.

## Publication and recovery

Each attempt fetches an exact branch commit into a local cache, builds in temporary isolation, validates repository identity, snapshot provenance, and optional knowledge completeness, then swaps one symlink to a versioned release. A failure leaves the last successful symlink intact and writes a small failure-status JSON. Releases are retained for review; no automatic deletion is implemented.

Serve `$STATE_ROOT/public` **only** through a tailnet-restricted HTTP service after checking access rules. Do not mount the directory under public Pages or a Cloudflare public route. The runner does not decide audience or configure Tailscale on your behalf.

For Mac mini recovery, install the same pinned producer and runner, use its own data root, and start manually only after the linuc scheduler is stopped or fenced. A snapshot copy is read-only recovery material; do not let two writers independently publish as if they shared one authority.

## Acceptance and limits

```bash
python3 -m unittest discover -s ops/linuc/tests -v
```

Synthetic tests cover pinned source, exact Git commit, atomic replacement, failure preservation, source allowlist and clean producer. Still required on the real host:

- verify a private synthetic GitHub repository and a restricted read-only token;
- test a failed GitHub API fetch and a malformed artifact;
- verify only approved tailnet clients can access the output and a revoked identity cannot;
- repeat a manual Mac mini rebuild of the same commit;
- measure elapsed refresh time, API rate-limit usage and staleness for one week before enrolling more repositories;
- verify compatibility with the installed Knowledge Lab and avoid duplicate writers.

Until these pass, the hosted GitHub Actions workflows should not be removed as the last documented fallback (they can be manual-only). No live deployment or access-control claim is made.
