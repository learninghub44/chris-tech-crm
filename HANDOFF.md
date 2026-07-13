# Chris Tech CRM — Handoff Notes

Written 2026-07-13, updated 2026-07-13 (later same day — commits moved
faster than the doc). Read this fully before touching the repo — it has
real GitHub history behind it, not a blank slate.

## What this project is

Repo: https://github.com/learninghub44/chris-tech-crm (public)
A rebrand of the open-source Django-CRM project into "Chris Tech CRM,"
owned by Chris (GitHub: learninghub44), running under his software dev
business. Intended target: christech.co.ke, sold as a commercial SaaS CRM
for small businesses (likely Kenyan market, KES pricing implied by past
projects, though this repo itself has no M-Pesa/billing code yet).

Stack:
- **Backend**: Django 6 + DRF, PostgreSQL with Row-Level Security
  (multi-tenant), Celery + Redis for async, JWT auth, AWS SES for email,
  S3-compatible storage via django-storages. Package managed with `uv`
  (see `backend/pyproject.toml`).
- **Frontend**: SvelteKit 2 / Svelte 5, Tailwind, pnpm.
- **Mobile**: Flutter app in `mobile/` (android + ios folders present,
  Firebase configured — see `mobile/FIREBASE_SETUP.md`).
- **MCP server**: `mcp_server/` — lets AI agents (Claude, Cursor, etc.)
  read/write CRM records via a personal access token. Optional install
  (`uv sync --extra mcp`).
- **Local dev**: `docker-compose.yml` spins up db, redis, backend,
  celery-worker, celery-beat, frontend. Uses `.env.docker` (dev-only
  placeholder secrets, fine to keep committed).

## What's been done so far (in order)

1. User uploaded a zip (`chris-tech-crm-rebranded.zip`) containing the
   already-rebranded source (branding/naming changes only — no
   functional changes).
2. It was flattened (zip had a redundant nested `chris-tech-crm/
   chris-tech-crm/` folder — repo root now matches project root) and
   pushed to `main` on top of the *existing* remote history (there was
   already an `Initial commit: Chris Tech CRM (based on Django-CRM)` —
   we did NOT force-push or rewrite history, we `reset --soft
   origin/main` and committed the rebrand as a new commit on top:
   commit `fc39ab6`, message "Rebrand to Chris Tech CRM").
3. GitHub Actions was fully **disabled** for the repo
   (`PUT /repos/.../actions/permissions {"enabled": false}`) at the
   user's request to stop a Dependabot-triggered workflow run from
   consuming/costing anything. One in-progress run
   ("Graph Update: uv in /backend, /mcp_server") was cancelled first.
   **Actions is currently OFF. Re-enable deliberately before expecting
   any CI/CD or Dependabot workflows to run again.**
4. GitHub's Dependabot scan reports **29 vulnerabilities: 9 high, 13
   moderate, 7 low** on the default branch. Not yet triaged or patched.
   Check https://github.com/learninghub44/chris-tech-crm/security/dependabot
   for the current list (may shift over time).
5. User's goal stated: make it deployable, then commercialize it
   (pricing/billing, the mobile app, "more"). Nothing beyond planning
   has been done for deployment or commercialization yet — no
   production env, no host set up, no billing code written.

## Roadmap agreed with user (in priority order)

**Status update (2026-07-13, same day): items 1–2 below have moved.
Commits since this doc was first written:**
```
5fcbd7b Fix CORS wide-open bug in prod settings, add SSL redirect/proxy header handling
28b27ee Patch Dependabot-flagged vulnerabilities (28 of 29)
e6fc764 Fix hardcoded TIME_ZONE (Asia/Kolkata -> Africa/Nairobi)
fcfec75 Patch last Dependabot vuln: weasyprint 68.1 -> 69.0 (CVE-2026-49452)
```

1. **Harden config for production** — **mostly done.** `SECRET_KEY`,
   `DEBUG`, `ALLOWED_HOSTS`, and CORS (`CORS_ORIGIN_ALLOW_ALL`) are all
   env-driven with safe defaults now (`backend/crm/settings.py`); the
   wide-open CORS bug is fixed and SSL redirect/proxy header handling
   was added. Still outstanding:
   - **S3 media storage is not actually wired up.** `django-storages`
     is a listed dependency but `settings.py` still only has local
     `MEDIA_ROOT`/`MEDIA_URL` — no `DEFAULT_FILE_STORAGE`, no bucket
     config. Uploaded files would hit local disk, which won't persist
     across Railway deploys. Needs real work, not just an env var.
   - SES email backend is wired and env-driven, but the default
     `AWS_SES_REGION_NAME` is still `ap-south-1` (inherited from the
     upstream template) — fine as long as the real env var is set at
     deploy time, but worth changing the default given the Kenyan
     market (SES has no Africa region; `eu-west-1` is the common
     choice).
   - Real `SECRET_KEY`/`ALLOWED_HOSTS` values still need to be set as
     actual env vars at deploy time — the code just no longer forces
     insecure defaults.
2. **Patch the 29 flagged vulnerabilities** — **done.** All 29 patched
   across two commits (`28b27ee` — 28 of 29, `fcfec75` — the last one,
   a weasyprint bump to 69.0 for CVE-2026-49452). Worth a fresh check
   of the Security tab to confirm zero open alerts remain, since new
   ones can appear independently of this work.
3. **Deploy backend + Postgres + Redis** — user's default host across
   his other projects is **Railway** (per his general stack pattern).
   Needs Procfile/railway config + provisioning Postgres/Redis services
   on Railway. Not started. **Note: this sandbox's network allowlist
   does NOT include railway.app**, so any Railway CLI/API calls must be
   run from the user's own machine or the Railway dashboard — an agent
   in a similarly locked-down sandbox will hit the same wall.
4. **Deploy the SvelteKit frontend** — likely Cloudflare Pages (his
   usual choice per other projects) or alongside backend on Railway.
   Not started.
5. **Point christech.co.ke at it** — DNS + HTTPS + update
   `ALLOWED_HOSTS`/CORS for the real domain. Not started.
6. **Build & ship the mobile Flutter app** — point API base URL at
   prod backend, build signed Android AAB and iOS build. Needs the
   user's Apple Developer and Google Play Console accounts. Not
   started.
7. **Commercialization** — pricing/plans, subscription billing (Stripe
   or M-Pesa given KES market), signup flow, per-plan usage limits,
   marketing landing page. No billing code exists in the repo today.
   Not started, not scoped in detail yet.

## Open questions / things to confirm with the user before proceeding

- Payment rail for billing: Stripe, M-Pesa (Daraja API), or both?
- Where is DNS for christech.co.ke managed (Cloudflare presumably,
  given his other projects use Cloudflare Pages)?
- Does he want Railway for backend specifically, or is that just an
  assumption carried over from his other repos (worth confirming, not
  yet confirmed for THIS project)?
- Multi-tenant pricing model — per-seat, per-org flat fee, usage-based?
- Any existing customers/leads waiting on this, or still pre-launch?

## Credentials/access an agent will need to keep going

- A **GitHub PAT** with `repo` scope to push further commits (the one
  used in this session was pasted directly in chat by the user — it
  should be rotated/replaced, don't reuse an old one from a
  transcript).
- Railway account access (CLI token or dashboard access) — user-side,
  not available in a sandboxed agent environment.
- AWS credentials for SES + S3 if wiring up production email/media.
- Apple Developer + Google Play accounts for mobile app store
  submission, when that stage is reached.
- Stripe or Daraja (M-Pesa) API keys once a billing rail is chosen.

## Working style notes for whoever picks this up

- Chris communicates tersely ("NEXT," "FIX IT," "PUSH") and prefers
  autonomous execution over back-and-forth — orient in the repo
  yourself before asking questions, and only ask when a decision
  genuinely can't be inferred (e.g. which payment rail).
- Don't force-push or rewrite `main` history on this repo — it already
  has real commits behind it (see point 2 above for how the rebrand
  was layered on safely).
