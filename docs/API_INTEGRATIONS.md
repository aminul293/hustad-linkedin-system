# LinkedIn API integrations

The honest map of what LinkedIn's official API lets this system automate, verified against the
Microsoft Learn documentation in August 2026. LinkedIn versions its API monthly and retires
versions on a rolling window, so before wiring anything, re-check the current docs; the shapes
below are stable, the version header is not.

## The one table that matters

| Surface | API? | This system's approach |
|---|---|---|
| Personal profile posts (text, image, PDF document) | Yes, self serve | `worker/post_scheduler.py`, live once secrets are set |
| Company page posts | Yes, after Community Management API approval | Worker supports it; manual from the Posts tab until approval |
| Carousel posts | Yes, as PDF document posts | `worker/render_assets.py` makes the PDF, worker uploads it |
| Newsletters | **No API exists** | Ten minute manual publish from the Newsletter tab |
| Long form articles | **No API exists** | Manual, from the Articles tab drafts |
| Direct messages | **No API exists, and prohibited here regardless** | Human sends every DM from the Outreach and Reply tabs. Do not build around this; it is a program rule, not a gap |
| Post analytics (impressions, engagement) | Organization posts only, with Community Management API; member post analytics are not available | Log manually in the tabs; revisit after org approval |

## Personal posting: the self serve path (do this first)

1. Create an app at developer.linkedin.com against the Hustad company page.
2. Add the products **"Sign In with LinkedIn using OpenID Connect"** and **"Share on LinkedIn"**.
   Both are self serve; no review queue.
3. OAuth authorization code flow with scopes `openid profile w_member_social`. Eric signs in once;
   you receive a member access token.
4. `GET https://api.linkedin.com/v2/userinfo` returns `sub`; the author URN is `urn:li:person:{sub}`.
5. Store token and URN as the two GitHub secrets. Flip `POSTING_ENABLED`.

Requests use the versioned surface:

```
POST https://api.linkedin.com/rest/posts
Authorization: Bearer {token}
Linkedin-Version: 202605          <- YYYYMM; keep within LinkedIn's supported window
X-Restli-Protocol-Version: 2.0.0
```

Payload shape is in `worker/post_scheduler.py::payload`. The response's `x-restli-id` header is
the created post URN; the worker stores it in `worker/state/posted.json`.

## Media: images and the carousel PDF

Two step, same pattern for both:

```
POST /rest/images?action=initializeUpload     {"initializeUploadRequest": {"owner": "<author urn>"}}
POST /rest/documents?action=initializeUpload  (PDF carousels; max 100MB, 300 pages, PDF/PPTX/DOCX)
```

The response carries `uploadUrl` (PUT the binary there, no version header) and the media URN
(`urn:li:image:...` / `urn:li:document:...`), which goes in the post's `content.media.id`.
A PDF document post renders as the swipeable carousel; LinkedIn's old native carousel format is
retired, the document post is the format.

## Company page posting: the application

Company page posts need the **Community Management API**, which is an application with review
(typically one to two weeks): use case description, privacy policy, app verification against the
company page. The posting account must be a page admin. Scope `w_organization_social`, author
`urn:li:organization:{id}`.

Until approval lands, Wednesday company posts are a two minute manual step: the Posts tab has the
copy button and the rendered asset. The worker detects the missing `LINKEDIN_ORG_URN` and says
exactly that in its log rather than failing.

Apply early; it gates analytics too, which is where the Friday review eventually wants real
impression numbers instead of hand-logged results.

## Tokens, the operational reality

Member access tokens live 60 days; refresh tokens 365 where the product grants them. Programmatic
refresh is not universally available, so build for the honest case: a calendar reminder (or a
worker preflight check) that fails loudly seven days before expiry, and a one click re-auth flow
to mint a new token. The worker treats a 401 as fatal and prints the re-auth instruction; it never
retries into a rate limit.

Rate limits are per application per day and generous relative to four posts a week (on the order
of low hundreds of posting calls per member per day). The worker makes at most three calls per
post. If you ever see 429s at this volume, something is looping; stop and read the state file.

## Rules the integration must keep

The four program rules in README.md apply to the API exactly as they apply to humans. In
particular: nothing reads or writes DMs, nothing scrapes, nothing acts on a profile, and every
piece of outbound content passed content QA before it entered the calendar. The worker posts what
the calendar holds and nothing else; if you want different content, change `content_engine.py`
and let the QA gate run.

Sources for the API facts above, for re-verification:
- learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api
- learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin
