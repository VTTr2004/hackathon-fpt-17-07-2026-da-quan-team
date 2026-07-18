# Automatic deployment with GitHub Actions

The workflow in `.github/workflows/deploy.yml` runs checks on pull requests. A push to `main` additionally builds the backend and frontend images, pushes them to GHCR, then deploys the exact commit to a Linux VPS.

## 1. Prepare the VPS once

Install Docker Engine and the Docker Compose plugin. The deployment user must be allowed to run Docker and write to `/opt/startup-lens`.

Create `/opt/startup-lens/.env.production` on the VPS:

```dotenv
POSTGRES_DB=startup_due_diligence
POSTGRES_USER=app
POSTGRES_PASSWORD=replace-with-a-long-random-password
DATABASE_URL=postgresql+asyncpg://app:replace-with-a-url-encoded-password@postgres:5432/startup_due_diligence
CORS_ORIGINS=https://your-domain.example
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GOONG_API_KEY=
GOOGLE_PLACES_API_KEY=
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

If the database password contains reserved URL characters, percent-encode it in `DATABASE_URL`. `POSTGRES_PASSWORD` itself remains the original, unencoded password.

Keep this file only on the server; never commit it. If surrounding-area data is required, place `poi.db` in `/opt/startup-lens/data/`.

## 2. Configure the repository

In GitHub, open **Settings → Secrets and variables → Actions** and create these repository or `production` environment secrets:

| Name | Value |
| --- | --- |
| `DEPLOY_HOST` | VPS hostname or IP address |
| `DEPLOY_PORT` | SSH port, usually `22` |
| `DEPLOY_USER` | Dedicated deployment user |
| `DEPLOY_SSH_KEY` | Private SSH deploy key |
| `DEPLOY_KNOWN_HOSTS` | Output of `ssh-keyscan -H your-host` verified against the VPS fingerprint |
| `GHCR_USERNAME` | GitHub username that can read the package |
| `GHCR_TOKEN` | Fine-grained/classic token with permission to read packages |

Create the Actions variable `NEXT_PUBLIC_API_URL`, for example `https://api.your-domain.example/api/v1`. Next.js embeds this public value while building, so changing it requires a new workflow run.

For a public GHCR package the VPS may pull anonymously; the supplied workflow still logs in so it works for private repositories too.

## 3. Deploy

Push or merge a commit into `main`, then follow the **CI/CD - Docker deploy** run under the repository's **Actions** tab. You can also run it manually with **Run workflow**.

The deployed containers use the immutable commit SHA tag. The `latest` tag is published for convenience but is not used during deployment.

## Roll back

On the VPS, replace `COMMIT_SHA` with a previously successful commit:

```bash
cd /opt/startup-lens
GHCR_REPOSITORY=ghcr.io/owner/repository IMAGE_TAG=COMMIT_SHA \
  docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```
