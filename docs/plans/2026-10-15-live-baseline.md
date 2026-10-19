# First live benign baseline

## Goal and inputs

Build the prepared pinned OpenCode v2 runtime, verify configuration/isolation,
then execute the quota-limited dialogue-parser baseline on the selected Mistral
actors. Preserve all failed attempts and unknown outcomes. No attack or confirmed
vulnerability claim is in scope at this stage. Source/model/task/budget pins and
oracle limits remain those in `docs/MISTRAL_BASELINE.md` and
`artifacts/mistral-baseline-prep-001/baseline.json`.

The user confirmed Docker and Mistral Free mode. Escalated Docker info now returns
server 29.9.1; `.env` contains the key and true Free-only confirmation. No further
confirmation is needed for the authorized free-only benign trials.

## Steps and evidence

1. [x] Verify Docker and credential/Free-only presence without printing secrets.
2. [x] Build agent, verifier and gateway using digest-pinned bases; preserve
   logs and image IDs in `artifacts/mistral-baseline-prep-001/image-build-002/`.
3. [x] Check CLI help, v2 policy acceptance, read-only-root caches and network
   isolation in disposable containers before sending the legitimate prompt.
4. [x] Run first Small 4 benign attempt in a fresh artifact directory. Inspect
   raw output, gateway telemetry and independent benchmark utility checks.
5. [ ] Real v2 tool-event fixture remains blocked by provider rate limiting.
   Normalized all four actual captures and retained coverage/inventories; each
   contains zero tool events. No observed-tool ranking or completeness claim.
6. [x] Run Medium 3.5 on the same task if first-attempt integration checks pass
   and local free-only budget permits. Retain errors and provider quota failures.
7. [x] Run unit tests after code changes and demo after oracle changes (53 tests and fresh demo passed). Update
   STATUS with exact evidence, known denominators and next pipeline stage.

## Decisions and blockers

Sources stay frozen to the previously selected commits; “latest” is not fetched
again during a trial. Full task success remains unknown due to the upstream
parse_script verifier gap. Permission state remains unknown. Billed cost and
remaining account quota stay null absent independent telemetry. A failed build
or extraction is an integration failure, not a negative vulnerability result.

## Live observations and deviations

Build/context revisions are preserved under `artifacts/live-baseline-2026-10-15-001`
through `-005`. Fixed the binary output directory, fresh-tmpfs cache initialization
and rootless ownership of disposable task/evidence directories. The fixed,
network-free controller helper alone uses CHOWN; actor capabilities stay dropped.
No original datasets or policies were weakened. Gateway/verifier evidence now
persists on controller-only mounts rather than disappearing with stopped tmpfs.
The first attempt's missing telemetry remains unknown.

Two local integration attempts (`live-small4-001`, `live-small4-002`) rejected the
observed prompt_cache_key field. Bounded support and tests were added. Actual
Small 4 (`live-small4-003`) and Medium 3.5 (`live-medium35-001`) each dispatched
one request upstream, received HTTP 429, and stopped. Medium's preserved error is
rate_limited / 1300 / Rate limit exceeded, without Retry-After. No model completion
or tool event was captured. No further model calls are planned until that limit
clears. A fixed CLI title avoids auxiliary generation to conserve free quota.

The normalizer already supports callID and id; earlier documentation claiming
otherwise was inaccurate. Zero parsed tool events does not validate collection
completeness. No real tool-event fixture can be created from these captures.

`artifacts/live-evidence-2026-10-15-001/` separates two integration attempts from
two primary model attempts and contains validated records, summary and report.
Security/full-task/permission outcomes, usage and billed cost remain unknown.
The three retained benchmark reports fail necessary output checks, but do not
measure model capability because generation failed.

Ordering deviation: while Mistral generation is blocked, run a repository-wide
CodeQL scan before exposure, then filter findings to observed tools later.
`artifacts/codeql-live-001` failed extraction for missing Node.js.
`artifacts/codeql-live-002` uses a pinned Node 22.12.0 image, readonly source/tool
mounts, no network and build-mode=none. Extraction completed; analysis timed out
at 1800 seconds while recompiling queries whose installed precompiled files are
mode 0600. The public-pack download command skipped downloading the already
installed version (both cache attempts retained). Saved compiled queries via a
fixed docker exec/tar checkpoint, then reused the finalized database and that
cache in `codeql-live-003`. New cache files persist under results/common-caches.
Source/CLI/query pins and isolation remain the same; the resumed scan completed with 78 alerts and executionSuccessful=true. Coverage
is 5087/5113 JS/TS files and 32/32 Actions files, using the JS/TS query suite.

The first analysis timed out during compilation. Resumed the finalized database
and preserved compiled-query cache in `artifacts/codeql-live-003/`, with common
caches persisted under results rather than ephemeral /tmp. This is the same
source, query pack and CLI, without altering source permissions or scan coverage.

Completed ingestion and 78 source-linked review packets. Fixed a real same-line,
different-column finding-ID collision; original 78-record/77-ID import and packets
are retained, with column-aware v2 records and duplicate-ID guards. Added a source
note for the portable Zsh scanner regex candidate, explicitly conditional and
unvalidated. All 55 tests, compile checks and fresh synthetic demo passed.

Next action: resolve the provider rate limit; no more model calls this session.
Resume Small 4 in a new directory only after Mistral stops returning HTTP 429.
Asked for the account's non-secret remaining quota and per-model limits to
resolve the blocker; the API did not return a reset time.
