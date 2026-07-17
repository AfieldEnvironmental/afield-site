# Afield site — handover notes

Snapshot of state on hand-off. The site is live and approved as-is.

## How content flows

The site is currently rendered **entirely from the HTML** in `index.html`. There is an Airtable hydration script in the page (around line 5500), but it has an early `return;` (line ~5618) that bypasses it.

```
HTML (index.html, hardcoded)    →   what visitors see
Airtable (apptFgYvzapkeUvov)    →   editorial source of truth, NOT currently rendering on the site
```

This intentional disconnect means the client can edit Airtable freely without the live site changing visually. To make Airtable edits go live, the in-house team needs to:

1. Remove the `return;` on the line numbered around 5618 (the surrounding comment explains).
2. Fix the three "DISABLED" sub-sections nearby (mission-text overwrite, video URL override, cycler-words DOM) — each has a comment in the code explaining what broke and what to be careful of.
3. Add a `Value` field to the Airtable **Site Config** table (see below).

Until those three steps land, Airtable is a read-only mirror of the HTML.

## Airtable schema state

Base: `apptFgYvzapkeUvov`

All tables now match the current HTML thanks to the sync script (`scripts/sync-airtable-from-html.py`). Specifics:

### Grants
Two records — Wilding + Arts. Fields used:
- `Card Intro` — the intro paragraph at the top of each grant card
- `Card Announcement` — the bold "launching in autumn / winter 2026" line
- `Card Body` — the main descriptive paragraph
- `Detail Intro` — large intro on the "Read more" detail panel
- `Detail Body` — the body of the detail panel, using `[P]` for paragraph breaks and `[LI]` for bullet items (per the `toHTML()` helper at line ~5036 of index.html)

### Values
Four records — Bold, Caring, Imaginative, Just. Fields:
- `Name` — value name (used as `<h3>` heading)
- `Description` — body text

### Team
Three records — Liz Orton, Mike Saunders, Joana Esgalhado.
- `Name` — used as bio heading
- `Bio` — bio body, with `[P]` for paragraph breaks (Liz has three paragraphs)

Joana was missing from Airtable and the sync script created her record. If "extra" team members are added in Airtable, they won't appear on the site until the hydration is re-enabled — and the HTML's `.bio-item` markup template would need to be made dynamic (currently it has a hand-written `<div>` per person).

### Cycler Words
Seven records — Purpose, Places, Wilding, Knowledge, Practices, Action, Art. These match the on-site cycler order.

### Site Config — **action required from in-house team**
The table holds 11 rows keyed by `Name`: `hero_heading`, `hero_cta_label`, `mission_intro`, `mission_body`, `values_intro`, `contact_email`, `footer_credit_label`, `footer_credit_url`, `hero_video_webm`, `hero_video_mp4`.

**There is no `Value` field on this table.** The Airtable REST API can't add fields — only the web UI can. Steps:

1. Open the Site Config table in Airtable.
2. Add a new field called `Value`. Type: **Long text** (single line works for shorter values, but `mission_body` is multi-paragraph and needs long text).
3. Re-run `scripts/sync-airtable-from-html.py` and it will populate every row.

The HTML hydration code reads `r.fields.Key` and `r.fields.Value`, but the actual field is named `Name` not `Key`. When re-enabling hydration, change line ~5622 from `cfg[r.fields.Key]` to `cfg[r.fields.Name]`.

## The sync script

`scripts/sync-airtable-from-html.py`

Run with:
```bash
AIRTABLE_TOKEN=pat... AIRTABLE_BASE=apptFgYvzapkeUvov python3 scripts/sync-airtable-from-html.py
```

Token needs `data.records:read` + `data.records:write` on the base. Safe to re-run — it diffs current Airtable against the HTML and only writes what's changed.

If the in-house team edits the HTML, they should update the hardcoded strings near the top of the script (clearly sectioned) before re-running.

## Form submissions

The Get in touch form posts to **Formspree** (`https://formspree.io/f/xgobbadz`). Recipient is configured in the Formspree dashboard to forward to `hello@afield.org.uk`. Login to Formspree is owned by Chris (Madalena Studio). To transfer ownership: change the recipient email + share login or create a new form under the client's own Formspree account.

## Domain & hosting

- Domain `afield.org.uk` registered at GoDaddy.
- DNS A records (185.199.108-111.153) + CNAME for www point at GitHub Pages.
- Repo: `AfieldEnvironmental/afield-site`.
- Deploy: GitHub Actions on push to `main` (`.github/workflows/deploy.yml`). Build takes ~90 seconds.
- HTTPS: Enforced via GitHub Pages (Let's Encrypt cert auto-rotates).

## Outstanding items (non-blocking)

- Privacy policy has one phrase ("Commonplace Digital Ltd" in the Disclosure section) that reads like a template leftover from another organisation — should probably be "Afield Environmental". Legal call.
- Hydration toggle + three DISABLED sub-sections (see top of this doc). Needed only when the team wants Airtable to be the live source.
- Site Config Value field (see above).

## Imagery (July 2026: static images, no more video)

All polygon imagery is now static transparent PNGs on Cloudinary, with the polygon composed at the centre of a 3840x2160 frame:

- WILDING `image/upload/v1784115426/AFIELD-WEB---WILDING_vi2w0s.png` — used by the desktop hero, desktop Wilding pin, mobile hero, and mobile Wilding section.
- ARTS `image/upload/v1784115429/AFIELD-WEB---ARTS_lrd3wx.png` — used by the desktop Arts pin and mobile Arts section.

The site requests them through `f_auto,q_auto,w_2560` so Cloudinary serves AVIF/WebP at a sensible size. To swap an image: re-export with the polygon centred in a 16:9 frame, upload to Cloudinary, and replace the URL in every slot that uses it (search the HTML for the old public ID). Keep the polygon centred in the frame — all slots use plain central alignment with no positional compensation.

The old `<video>` management JS (pause pipeline, iPad decode gate, codec probe) is still in the file but inert; it null-guards and no-ops with no videos present, and works again if video ever returns.

## Transfer of ownership checklist

Everything the site depends on, who holds it today, and the exact step that moves it. Order matters where noted.

### 1. GitHub (code + hosting) — currently: Chris admin on `AfieldEnvironmental/afield-site`
1. Client staff create GitHub accounts (with 2FA) and are added as **Owners** of the `AfieldEnvironmental` org (org Settings → People). If the org itself was created under Chris's account, transfer org ownership rather than the repo — the Pages URL, Actions history and settings all stay put.
2. Verify the client can see repo → Settings → Pages (custom domain shows `afield.org.uk`) and Settings → Secrets and variables → Actions (`AIRTABLE_TOKEN`, `AIRTABLE_BASE`).
3. In the org's Settings → Pages → **Verified domains**, verify `afield.org.uk` (adds a TXT record at GoDaddy). This stops anyone else claiming the domain on Pages if the site is ever unpublished.
4. After steps 5–6 below, Chris removes himself from the org.

### 2. Airtable (content) — currently: base `apptFgYvzapkeUvov` in Chris's workspace, token in GitHub Secrets is Chris's PAT
1. Share the base with a client admin, then **move the base into the client's own Airtable workspace** (base menu → Move base). URLs and IDs don't change.
2. A client admin creates their own Personal Access Token at airtable.com/create/tokens with scopes `data.records:read` (+ `data.records:write` if they'll run the sync scripts) restricted to this base.
3. Replace `AIRTABLE_TOKEN` in GitHub repo Secrets with the new token; run the workflow manually (Actions → Build and Deploy → Run workflow) to confirm a green build.
4. Chris revokes his old PAT. **Do this last** — revoking first breaks the hourly rebuild.

### 3. Domain — currently: `afield.org.uk` in Chris's GoDaddy account
1. Client creates a GoDaddy account; Chris initiates **Move domain to another GoDaddy account** (Domain Settings → Transfer → within GoDaddy; free, instant-ish).
2. DNS records that must survive the move (they copy across automatically, but verify): four A records `185.199.108.153` / `.109.153` / `.110.153` / `.111.153` on `@`, CNAME `www` → `afieldenvironmental.github.io`, plus the Pages verification TXT from step 1.3.
3. Nothing to change in the repo — `CNAME` file already says `afield.org.uk`.

### 4. Cloudinary (imagery) — currently: account `duaosajrr`, owned by Chris
The live site hot-links images from this account, so the account must stay alive under client control. Simplest: change the account's email + password to a client-owned inbox (Settings → Account). The URLs (and therefore the site) don't change. The free tier covers current usage comfortably.

### 5. Formspree (contact form) — currently: form `xgobbadz` under Chris's login
Two options:
- **Clean break (recommended):** client creates their own Formspree account, makes a new form pointing at `hello@afield.org.uk`, and the form ID is swapped in `index.html` (one string: search `formspree.io/f/`). Submissions history stays with the old form.
- Or hand over the existing login and change its email.

### 6. Leftovers to delete once transferred
- `netlify.toml` + `netlify/` — vestiges of the old Netlify deploy; the site is GitHub Pages now. Safe to remove.
- Any local clones/tokens on Madalena machines.

## Adding new pages via Airtable — BUILT, needs one Airtable step

**Scope:** the main page is a hand-choreographed scroll experience — new *sections* of it can't come from a spreadsheet. What this feature adds is standalone **content pages** (news, project write-ups, announcements) in the site's fonts and colours, generated at build time as plain static HTML (fast, indexable, no client-side rendering).

**The one thing the team must do first** — create a table called **`Pages`** in the Airtable base (the API can't create tables), with EXACTLY these field names:

| Field | Type | Notes |
|---|---|---|
| `Title` | Single line text | required |
| `Slug` | Single line text | required — becomes the URL: `afield.org.uk/<slug>/`. Lowercase letters, numbers, hyphens (anything else is stripped) |
| `Body` | Long text | required — same `[P]` paragraph / `[LI]` bullet markers as the Grants copy |
| `Image URL` | URL | optional — full-width image under the title (use a Cloudinary URL) |
| `Published` | Checkbox | the page only builds when ticked |
| `Order` | Number | optional — sort order on the `/pages/` listing |

**How publishing works after that:**
1. Add a row, tick Published.
2. The site rebuilds hourly (GitHub Actions cron), so the page is live at `afield.org.uk/<slug>/` within the hour — or immediately via GitHub → Actions → Build and Deploy → **Run workflow**.
3. Every published page is also linked from `afield.org.uk/pages/`. To surface one on the main site, paste its URL wherever it's wanted (or link it from another page's Body).

**Where the code lives:** `scripts/build-pages.js` (the generator + the page template, commented) runs as the "Build Airtable pages" step in `.github/workflows/deploy.yml`, reading the `data/airtable.json` that `fetch-airtable.js` writes. Until the `Pages` table exists, the fetch treats it as optional and the build stays green. Fonts for generated pages are the shared `assets/gt-cinetype.css`. Un-ticking Published removes the page at the next build (the deploy artifact is rebuilt from scratch every run).

Safety rails built in: slugs are sanitised, duplicates and reserved names (`assets`, `data`, `scripts`, `pages`, …) are skipped with a warning in the build log, and page content is HTML-escaped.
