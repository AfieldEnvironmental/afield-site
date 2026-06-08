#!/usr/bin/env python3
"""
One-off: applies the copy edits from commit fef885e to Airtable.

Safe to re-run: every edit checks for the "before" text and skips if
it isn't present, so a second run is a no-op.

Run with:
  AIRTABLE_TOKEN=pat... AIRTABLE_BASE=app... python3 scripts/update-airtable-copy.py

Token needs data.records:read + data.records:write on this base.
Pure stdlib (no pip install).
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request

TOKEN = os.environ.get("AIRTABLE_TOKEN")
BASE  = os.environ.get("AIRTABLE_BASE")
if not TOKEN or not BASE:
    sys.stderr.write("✗ Missing AIRTABLE_TOKEN or AIRTABLE_BASE env vars.\n")
    sys.exit(1)

HEADERS = {
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json",
}

# Each edit:
#   table     — Airtable table name
#   match     — dict identifying the record (e.g. {"Type": "wilding"})
#   fields    — list of candidate field names; the FIRST one containing
#               the "find" text gets the replacement
#   find      — literal substring (or `find_regex` instead)
#   find_regex— compiled regex; mutually exclusive with `find`
#   replace   — replacement string ("" for deletion)
EDITS = [
    # ─── WILDING ───────────────────────────────────────────────────────
    dict(table="Grants", match={"Type": "wilding"}, fields=["Card Intro"],
         find="affects low-income", replace="affect low-income"),

    dict(table="Grants", match={"Type": "wilding"}, fields=["Card Announcement"],
         find="Autumn 2026", replace="autumn 2026"),

    dict(table="Grants", match={"Type": "wilding"}, fields=["Detail Body"],
         find="They result from failures", replace="These result from failures"),

    dict(table="Grants", match={"Type": "wilding"}, fields=["Detail Body"],
         find="The result is that local communities and the wider urban ecology suffer from:",
         replace="Consequently, local communities and the wider urban ecology experience:"),

    dict(table="Grants", match={"Type": "wilding"}, fields=["Detail Body"],
         find="support them to realise", replace="support grantees to realise"),

    # Delete the "Our goal over the next five years..." paragraph + its
    # leading [P] separator.
    dict(table="Grants", match={"Type": "wilding"}, fields=["Detail Body"],
         find_regex=re.compile(
             r"\s*\[P\]\s*Our goal over the next five years is to support around 10 people on their way to creating new or caring for existing nature spaces in their community\.?\s*"
         ),
         replace=""),

    # ─── ARTS ──────────────────────────────────────────────────────────
    dict(table="Grants", match={"Type": "arts"}, fields=["Card Intro"],
         find="environmental knowledge", replace="ecological knowledge"),

    dict(table="Grants", match={"Type": "arts"}, fields=["Card Announcement"],
         find="Winter 2026", replace="winter 2026"),

    dict(table="Grants", match={"Type": "arts"}, fields=["Card Body", "Detail Body"],
         find="We nurture excellence", replace="We seek to nurture excellence"),

    dict(table="Grants", match={"Type": "arts"}, fields=["Card Body", "Detail Body"],
         find="Initially we will trial an open call approach, and in the first year we will award seven grants of up to £30,000 for projects of up to three years.",
         replace="Initially we will trial an open call approach, awarding grants of up to £30,000 for projects of up to three years."),

    dict(table="Grants", match={"Type": "arts"}, fields=["Detail Intro"],
         find="environmental knowledge", replace="ecological knowledge"),

    # Delete the "We believe that we can support excellence..." paragraph.
    dict(table="Grants", match={"Type": "arts"}, fields=["Detail Body"],
         find_regex=re.compile(
             r"\s*\[P\]\s*We believe that we can support excellence both in the arts and in ecological research by focusing our resources on low-income artists who have been traditionally excluded from research funding\. Artists can make a unique and vital contribution to ecological research [—\-] they can work outside of, across, with and against traditional disciplines, developing insights and ideas that go beyond established scientific, technical and cultural frameworks\.\s*"
         ),
         replace=""),

    dict(table="Grants", match={"Type": "arts"}, fields=["Detail Body"],
         find="specified outputs", replace="predetermined outputs"),

    # ─── VALUES ────────────────────────────────────────────────────────
    dict(table="Values", match={"Name": "Bold"}, fields=["Description"],
         find="We back communities to be bold too",
         replace="We support communities to be bold too"),

    # Justice has two changes in one sentence ("operate" → "work" AND
    # delete "in everything we do"). Single regex covers both.
    dict(table="Values", match={"Name": "Justice"}, fields=["Description"],
         find_regex=re.compile(
             r"Justice shapes how we operate\. We ask who benefits, who is missing, and what is fair, and we aim to hold ourselves accountable to those questions in everything we do\.?"
         ),
         replace="Justice shapes how we work. We ask who benefits, who is missing, and what is fair, and we aim to hold ourselves accountable to those questions."),
]


def api(method, path, body=None):
    url = "https://api.airtable.com/v0/" + BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} → {e.code} {e.read().decode('utf-8', 'replace')}")


def list_all(table):
    encoded = urllib.parse.quote(table, safe="")
    records = []
    offset = None
    while True:
        suffix = f"/{encoded}"
        if offset:
            suffix += "?offset=" + urllib.parse.quote(offset)
        page = api("GET", suffix)
        records.extend(page.get("records", []))
        offset = page.get("offset")
        if not offset:
            break
    return records


def patch_record(table, rec_id, fields):
    encoded = urllib.parse.quote(table, safe="")
    return api("PATCH", f"/{encoded}/{rec_id}", body={"fields": fields})


def record_matches(rec, match):
    for k, v in match.items():
        if str(rec.get("fields", {}).get(k, "")).lower() != str(v).lower():
            return False
    return True


def describe(e):
    if "find_regex" in e:
        return e["find_regex"].pattern[:80] + "…"
    return f'"{e["find"][:60]}"' + ("…" if len(e["find"]) > 60 else "")


def main():
    cache = {}
    applied = 0
    already = 0
    missed  = 0

    for e in EDITS:
        if e["table"] not in cache:
            print(f"  fetching {e['table']}… ", end="", flush=True)
            cache[e["table"]] = list_all(e["table"])
            print(f"{len(cache[e['table']])} records")

        rec = next((r for r in cache[e["table"]] if record_matches(r, e["match"])), None)
        if not rec:
            sys.stderr.write(f"✗ no {e['table']} record matching {e['match']}\n")
            missed += 1
            continue

        hit = False
        for field in e["fields"]:
            cur = rec["fields"].get(field)
            if not isinstance(cur, str):
                continue

            if "find_regex" in e:
                if not e["find_regex"].search(cur):
                    continue
                nxt = e["find_regex"].sub(e["replace"], cur)
            else:
                if e["find"] not in cur:
                    continue
                nxt = cur.replace(e["find"], e["replace"])

            if nxt == cur:
                already += 1
                hit = True
                break

            patch_record(e["table"], rec["id"], {field: nxt})
            rec["fields"][field] = nxt
            label = e["match"].get("Type") or e["match"].get("Name") or list(e["match"].values())[0]
            print(f"✓ {e['table']} / {label} / {field}")
            print(f"   - {describe(e)}")
            replace_show = e["replace"] if e["replace"] else "(deleted)"
            print(f"   + \"{replace_show[:60]}\"")
            applied += 1
            hit = True
            break

        if not hit:
            # Distinguish "already correct on re-run" from a real miss
            # by probing for the replacement text instead.
            probe = e.get("replace") or ""
            joined = "\n".join(str(rec["fields"].get(f) or "") for f in e["fields"])
            if probe and len(probe) > 6 and probe in joined:
                already += 1
            else:
                sys.stderr.write(
                    f"⚠ no match for {describe(e)} in "
                    f"{e['table']}/{e['match']}/{'|'.join(e['fields'])}\n"
                )
                missed += 1

    print(f"\nApplied {applied}, already-correct {already}, missed {missed}.")
    if missed:
        sys.stderr.write(
            "Some edits could not be applied. Review the ⚠ lines above and either "
            "fix the source text manually in Airtable or update this script.\n"
        )
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.stderr.write(f"✗ {exc}\n")
        sys.exit(1)
