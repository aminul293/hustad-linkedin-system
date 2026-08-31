# Privacy

## What data this system holds

| Data | Where | What it identifies |
|---|---|---|
| LinkedIn connection export | `data/raw/` | ~4,839 people: full name, current employer, job title, profile URL, connection date |
| LinkedIn messages, invitations, endorsements | `data/raw/` | who Eric has spoken to and when |
| CRM opportunity export | `data/raw/` | client company names, deal values, account managers, stages |
| Generated plan and copy | `data/work/` | the above, joined, plus a drafted message naming each person |
| The desk page | `data/out/`, `site/` | the same data, embedded in HTML |
| Send log | the browser, and `send_log.csv` | who was contacted, when, and any note Eric typed |
| `data/work/account_map.json` | `data/work/` | Hustad's own client roster, plus residential customer names from the CRM export |
| `data/work/plan_change_log*.csv` | `data/work/` | people removed from the plan, by name, with the reason |
| `data/work/storm_openers.py` | `data/work/` | today's drafted openers and verification notes, which name people and describe their employers |

The people in the connection export did not opt into this program. They accepted a LinkedIn
connection request. That is the standard the handling should be held to.

## Rules

**None of it goes in git.** `.gitignore` excludes `data/raw`, `data/work`, `data/out` and the built
`site/index.html`. Only `data/sample/` is tracked, and it is synthetic.

This is why the client map, the change logs and the daily storm file are data files rather than
python literals inside `pipeline/`. They used to be literals. A literal in a tracked file is one
`git add` away from being published, and no `.gitignore` can help you. If you find yourself about
to paste a real name into a file under `pipeline/`, that is the signal it belongs in `data/work/`
with a loader and a synthetic sample beside it.

Two judgement calls worth knowing about, because they are the ones a reviewer will question.

The **company research corpus** is public, sourced and company-level, and it was tracked at first
for exactly that reason. It is not tracked now. It quotes named executives out of promotion and
acquisition announcements, and the set of companies in it is the target list, so publishing it
publishes who Hustad is working. It lives in `data/research/` with a three-company synthetic sample
beside it in `data/sample/research/`, and `paths.research()` picks whichever is present.

The **internal routing roster** is tracked: `reply_engine.py` and `docs/REPLY_ENGINE.md` name
Hustad's own account managers and BD team next to the reply categories they own, because a reply
router that does not say who to route to is not a router. Those are colleagues doing their public
jobs, not third parties on a cold list, which is a different thing from the connection export and
is why the line is drawn here. It is still a reason to keep the repository private. The five client
names in the same files, and the executives quoted alongside them in `build_playbook.js`, are the
testimonial references that are already printed in Hustad's intro deck. They are cleared for use by
the people who gave them. Nothing else about a client contact belongs in a tracked file.

**None of it goes on the open internet.** The desk page embeds names, employers and profile URLs in
plain HTML. Anywhere it is served needs an identity check in front of it. See `DEPLOY.md`.

**None of it goes into a third-party tool** for enrichment, scoring or "finding emails". The export
is the only ingestion path, and adding a data broker to this pipeline would change what the program
is.

**Keep it out of the working tree if you can.** Set `HUSTAD_DATA=/secure/path` and the pipeline
reads and writes there instead. On a shared or backed-up machine, do this.

## If it leaks

Tell Eric immediately, then work out the blast radius: a public repo commit, a public deploy, or a
shared file. For a git commit, rewriting history is not enough on its own if the repo was ever
public or forked. Rotate what can be rotated and assume the rest is out. Note that the CRM export
also identifies Hustad's own clients and deal values, which is a commercial disclosure as well as a
privacy one.

## Retention

The program instructions call for keeping the master workbook plus the two most recent raw exports,
and noting superseded exports for deletion. Nothing here enforces that yet; it is worth a scheduled
job when the data moves to a real store.
