# Deploying the desk

The built page contains personal data (see `PRIVACY.md`). Every option below is ranked by whether it
keeps that private, which matters more than convenience.

## What gets deployed

`make site` writes a single self-contained `site/index.html`: one file, no build step, no runtime
dependencies except Google Fonts. It works from `file://`, from any static host, from anything.

It is gitignored. Whatever you deploy with must build it, not commit it.

## Options, best first

### 1. Static host with access control (recommended)

Cloudflare Pages with Cloudflare Access, or Netlify with password protection, or Vercel with
Deployment Protection. Build command `make site`, publish directory `site`. Put Eric's Google or
Microsoft identity on the allow list. Fifteen minutes, and the data is behind a login.

### 2. GitHub Pages from a private repo

Private Pages needs GitHub Enterprise Cloud. On Team or Free, a private repo's Pages site is
**public**, which is the trap worth knowing about. There is a workflow at
`.github/workflows/deploy.yml` and it is disabled by default for that reason.

### 3. Behind the corporate network

If Hustad has internal hosting, this is one static file. It is the simplest thing to put on an
intranet share or an internal web server.

### 4. Local only

`make site && make serve`, open `http://localhost:8000`. Zero exposure. The obvious downside is one
machine, but that is also true of the send log today.

## What NOT to do

**Do not deploy to a public URL and rely on it being unguessable.** The page names real people and
their employers. An unlisted URL is not access control.

**Do not commit `site/index.html` to make a deploy simpler.** That puts the data in git history,
where it is much harder to remove than to prevent.

## The GitHub Actions workflow

`.github/workflows/deploy.yml` builds and deploys to Pages. It is disabled (`if: false` on the job)
until someone confirms the Pages site is not public. Turning it on also requires the real data to
reach the runner, which means committing it or passing it as a secret, both worse than option 1.

For a private host, the same workflow shape works: swap the deploy step and provide the data via a
secret or a mounted volume.
