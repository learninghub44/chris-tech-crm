# Deploying to Railway

This repo can't reach railway.app from the sandbox this was written in,
so this doc is the handoff: everything below has to be run from your
own machine, the Railway CLI, or the Railway dashboard.

## What's already in the repo

- `Dockerfile` — now bakes in `docker/backend/entrypoint.prod.sh`
  (migrate → collectstatic → gunicorn). This is separate from
  `docker/backend/entrypoint.sh`, which is dev-only (runserver,
  volume-mounted via docker-compose) and NOT used in this flow.
- `railway.json` — tells Railway to build via `Dockerfile` and start
  with the prod entrypoint. This is the config for the **web** service
  specifically.

## Services to create in Railway (4 total, one project)

1. **Postgres** — Railway's built-in Postgres plugin (Add → Database →
   PostgreSQL). No config needed, Railway provisions it and exposes
   `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`,
   `DATABASE_URL`.
2. **Redis** — Railway's built-in Redis plugin (Add → Database →
   Redis). Exposes `REDIS_URL`.
3. **web** (Django/gunicorn) — deploy from this GitHub repo, root
   directory `/`. Railway will pick up `railway.json` and `Dockerfile`
   automatically. This is the only service that needs a public domain
   (Settings → Networking → Generate Domain, or a custom domain once
   DNS is pointed).
4. **worker** and **beat** (Celery) — deploy from the **same repo**,
   but as two more separate Railway services. Same Dockerfile/build,
   but each needs its **start command overridden** in Railway's
   service settings (Settings → Deploy → Start Command), since
   `railway.json`'s `startCommand` only applies to the service using
   it as-is:
   - worker: `celery -A crm worker --loglevel=info`
   - beat: `celery -A crm beat --loglevel=info`

   (Simplest path: create the `web` service first from `railway.json`,
   then duplicate it twice in the dashboard and just change the start
   command on the two copies — avoids re-wiring env vars by hand.)

## Env vars — web, worker, and beat all need the same set

Railway lets you reference another service's vars with
`${{ServiceName.VAR_NAME}}` — use that instead of copy-pasting values,
so rotating a DB password later doesn't mean updating it in 3 places.

**Database** (map to Railway's Postgres plugin vars):
```
DBHOST=${{Postgres.PGHOST}}
DBPORT=${{Postgres.PGPORT}}
DBNAME=${{Postgres.PGDATABASE}}
DBUSER=${{Postgres.PGUSER}}
DBPASSWORD=${{Postgres.PGPASSWORD}}
```
(Note: `settings.py` reads these discrete `DB*` vars, not
`DATABASE_URL` — Railway's Postgres plugin provides both, but only
the discrete ones are wired up in this codebase.)

**Celery / Redis:**
```
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
```

**Core Django:**
```
ENV_TYPE=prod
SECRET_KEY=<generate a real one, e.g. `python -c "import secrets; print(secrets.token_urlsafe(64))"`>
DEBUG=False
ALLOWED_HOSTS=christech.co.ke,www.christech.co.ke,<web-service>.up.railway.app
CORS_ALLOW_ALL=False
CORS_ALLOWED_ORIGINS=https://christech.co.ke,https://www.christech.co.ke
TIME_ZONE=Africa/Nairobi
```

**S3 (media storage — required, `server_settings.py` will crash boot
without these once `ENV_TYPE=prod`):**
```
AWS_BUCKET_NAME=<your S3 bucket name>
AWS_ACCESS_KEY_ID=<IAM key with S3 read/write on that bucket>
AWS_SECRET_ACCESS_KEY=<...>
```

**SES (email — also required at boot once `EMAIL_BACKEND` is set to
SES):**
```
EMAIL_BACKEND=django_ses.SESBackend
AWS_SES_REGION_NAME=eu-west-1
AWS_SES_REGION_ENDPOINT=email.eu-west-1.amazonaws.com
DEFAULT_FROM_EMAIL=noreply@christech.co.ke
ADMIN_EMAIL=<your real admin email>
```
(`eu-west-1` suggested since AWS SES has no Africa region — confirm
this is where you want to verify a sender identity, or pick another
supported SES region.)

**Sentry (also required at boot — `server_settings.py` calls
`os.environ["SENTRY_DSN"]` with no default):**
```
SENTRY_DSN=<from a Sentry project you create>
```

**Cookies / proxy:**
```
SESSION_COOKIE_DOMAIN=.christech.co.ke
SECURE_SSL_REDIRECT=True
```

## Order of operations

1. Create the Railway project, add Postgres + Redis plugins first.
2. Create the `web` service from this GitHub repo (root dir `/`).
   Railway auto-detects `railway.json`.
3. Set all env vars above on `web`.
4. Confirm first deploy succeeds — check logs for migration success
   and gunicorn startup. **It will fail to boot without `SENTRY_DSN`,
   `AWS_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
   `AWS_SES_REGION_NAME`, and `AWS_SES_REGION_ENDPOINT` all set** —
   `server_settings.py` requires these with no fallback once
   `ENV_TYPE=prod`.
5. Duplicate `web` into `worker` and `beat`, override each start
   command as above, same env vars (they share the Postgres/Redis
   references automatically since references are per-project, not
   per-service).
6. Generate a Railway domain on `web`, confirm the app responds.
7. Point `christech.co.ke` DNS at Railway (CNAME to the generated
   domain, or Railway's custom domain flow) — separate step, see
   HANDOFF.md item 5.

## What's NOT covered here

- Actually creating the S3 bucket / IAM user, verifying an SES sender
  identity, or creating the Sentry project — those are AWS/Sentry
  console tasks, not Railway ones.
- DNS for christech.co.ke (HANDOFF.md item 5).
- Frontend deploy (Cloudflare Pages, HANDOFF.md item 4) — separate
  from this backend deploy.
