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
- The desktop hero video is currently the Wilding asset (Comp_14 pair). Swap to a landing-specific asset when one's available.
