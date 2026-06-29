#!/usr/bin/env python3
"""
Sync Airtable content to match the current HTML on the live site.

Why this exists: client has approved the site as-is. They want Airtable
to hold the same text the site shows, so that future edits go through
Airtable (once the hydration switch in index.html line 5618 is re-enabled
by the in-house team).

This script writes the HTML's text into Airtable verbatim. Safe to re-run.

Run:
  AIRTABLE_TOKEN=pat... AIRTABLE_BASE=app... python3 scripts/sync-airtable-from-html.py
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
    sys.stderr.write("Missing AIRTABLE_TOKEN or AIRTABLE_BASE.\n")
    sys.exit(1)

H = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}


def api(method, path, body=None):
    url = "https://api.airtable.com/v0/" + BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=H, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code} {e.read().decode('utf-8','replace')}")


def list_all(table):
    encoded = urllib.parse.quote(table, safe="")
    records, offset = [], None
    while True:
        path = f"/{encoded}"
        if offset:
            path += "?offset=" + urllib.parse.quote(offset)
        page = api("GET", path)
        records.extend(page.get("records", []))
        offset = page.get("offset")
        if not offset:
            break
    return records


def patch_record(table, rec_id, fields):
    encoded = urllib.parse.quote(table, safe="")
    return api("PATCH", f"/{encoded}/{rec_id}", body={"fields": fields})


def create_record(table, fields):
    encoded = urllib.parse.quote(table, safe="")
    return api("POST", f"/{encoded}", body={"fields": fields})


def find_by(records, key, value):
    """Return the record whose fields[key] == value, case-insensitive."""
    for r in records:
        v = r.get("fields", {}).get(key, "")
        if str(v).lower() == str(value).lower():
            return r
    return None


# ──────────────────────────────────────────────────────────────────────
# Content extracted from index.html (June 2026 state of the live site).
# Edits to the HTML should be mirrored here when the in-house team runs
# this script next.
# ──────────────────────────────────────────────────────────────────────

WILDING_CARD_INTRO = (
    "Afield aims to address environmental injustices driven by structural "
    "inequalities in urban planning, land use and development. These failures "
    "result in biodiversity loss, degraded habitats, poor physical and mental "
    "health, and increased climate vulnerability, all of which disproportionately "
    "affect low-income communities."
)
WILDING_CARD_ANNOUNCEMENT = (
    "Afield will be launching the first round of its wilding grants in London "
    "in autumn 2026."
)
WILDING_CARD_BODY = (
    "Afield responds by funding and supporting individuals with ideas for "
    "transformative community-led urban wilding, providing up to three years "
    "funding alongside mentorship, skills-building and networks. Our philosophy "
    "is rooted in mutuality: encouraging partnerships between humans and nature, "
    "supporting shared ecological spaces, and promoting reciprocal investment "
    "in ecosystems."
)

WILDING_DETAIL_INTRO = (
    "Afield is tackling problems that are rooted in the structural inequalities "
    "underlying environmental injustice."
)
# Detail Body uses [P] paragraph markers + [LI] list markers (per toHTML in
# index.html ~line 5036). HTML <strong> tags inside list items are preserved.
WILDING_DETAIL_BODY = (
    "[P] These result from failures of government, private development, land "
    "ownership, and urban planning to provide healthy inner-city ecosystems. "
    "Consequently, local communities and the wider urban ecology experience:"
    " [P]"
    " [LI] A lack of biodiversity"
    " [LI] Habitat scarcity for all species"
    " [LI] Poor human (physical and mental) health and wellbeing arising from a "
    "lack of access to rich local ecosystems and poor air quality"
    " [LI] Climate change vulnerability such as higher risk of overheating and "
    "flooding"
    " [P] These problems disproportionately affect poor communities. "
    "Environmental degradation reinforces social inequality and ecological "
    "decline. Therefore the areas of the highest need in cities are often those "
    "with the lowest capacity to solve the problems. Residents have less free "
    "time, greater financial burden, and there are fewer voluntary organisations."
    " [P] Our framework for change is therefore one of:"
    " [P]"
    " [LI] <strong>Mutual partnerships:</strong> working together to benefit "
    "humans and other species"
    " [LI] <strong>Mutual spaces:</strong> living together as part of an "
    "ecosystem, supported by governance such as long-term agreements or land "
    "ownership"
    " [LI] <strong>Mutual investment:</strong> giving back as much as we take "
    "from ecosystems"
    " [P] Afield's approach is to support a small number of individuals with a "
    "visionary idea to create foundational, long-term, community-led wilding "
    "projects that benefit both humans and other species. We will support "
    "grantees to realise their ideas by funding up to three years of the London "
    "Living Wage, and providing a cohort programme of mentorship, peer support, "
    "technical skills, networking, and learning."
    " [P] Having mapped access and need for urban green space across London, "
    "we'll initially be inviting applications from individuals looking to "
    "develop projects in Waltham Forest, Newham, Barking, Croydon, Brent, "
    "Ealing, Lambeth, Lewisham, Hackney and Islington."
)

ARTS_CARD_INTRO = (
    "Afield provides grants to artists on low incomes, whose research "
    "contributes towards ecological knowledge and justice."
)
ARTS_CARD_ANNOUNCEMENT = (
    "Afield will be launching the first round of its arts grants in London in "
    "winter 2026."
)
ARTS_CARD_BODY = (
    "Afield's art programme supports artist research focusing on ecological "
    "care, interconnection, imagination, and repair. We seek to nurture "
    "excellence in the arts and demonstrate the value of artistic contributions "
    "to ecological justice, publishing and sharing artworks that challenge "
    "failed ecological models and help create futures everyone can live in. "
    "Artists make a vital contribution to ecological research — they can work "
    "outside of, across, with, and against traditional disciplines, developing "
    "ideas that go beyond established scientific, technical and cultural "
    "frameworks. Afield is committed to bringing under-represented voices to "
    "ecological research."
)

ARTS_DETAIL_INTRO = (
    "Afield aims to address a funding gap in the arts by providing grants to "
    "artists in financial hardship or on low incomes, whose research contributes "
    "towards ecological knowledge and justice."
)
ARTS_DETAIL_BODY = (
    "[P] Afield's art programme aims to:"
    " [P]"
    " [LI] Provide career and development support for artists who have been "
    "structurally disadvantaged in arts funding, and to promote equity and "
    "plurality in arts research"
    " [LI] Value and support the intrinsic value of artist contributions to "
    "ecological justice"
    " [LI] Promote ecological frameworks that foreground care, interdependency "
    "and connection, imagination and repair"
    " [P] We seek to fund artist research that might include:"
    " [P]"
    " [LI] New knowledge, frameworks and paradigms that disrupt and offer "
    "alternatives to current exploitative models"
    " [LI] Direct action or intervention"
    " [LI] Socially engaged learning, organising and solidarity-building"
    " [LI] Speculation, reimagining, and world-building"
    " [LI] More than human-perspectives"
    " [P] We recognise that the current funding system for artists is broken "
    "and we aim to be a fair and transparent funder, creating an application "
    "process that does not overburden applicants. Initially we will trial an "
    "open call approach, awarding grants of up to £30,000 for projects of up to "
    "three years."
    " [P] We do not make our grants conditional on achieving predetermined "
    "outputs and outcomes, and we seek a collaborative, learning-based "
    "relationship with the artists we support. We are particularly interested "
    "in proposals from global majority artists, LGBTQIA+ artists, disabled "
    "artists or artists experiencing chronic illness. Our fund is open to all "
    "ages, art disciplines and points in career."
)

VALUES = {
    "Bold": "We embrace risk and challenge orthodoxy. We take clear positions and back the individuals and ideas we believe in, even when it's uncomfortable. We support communities to be bold too — treating every outcome as learning.",
    "Caring": "We understand care as a practice — of attention, of relationships, and of responsibility. We aim to extend that care to our grantees and beyond — to non-human life, to land, and to the health of communities and ecosystems.",
    "Imaginative": "We take and support creative action. We stay curious, make space for the unexpected, and trust the process of not-knowing.",
    "Just": "Justice shapes how we work. We ask who benefits, who is missing, and what is fair, and we aim to hold ourselves accountable to those questions.",
}

TEAM = {
    "Liz Orton": (
        "Liz is a visual artist with a background in education and participatory "
        "arts. She worked as a Lecturer in Photography at London College of "
        "Communication, and as an Associate Artist with Performing Medicine, and "
        "has led participatory photography projects for PhotoVoice, the "
        "Photographers' Gallery, The Refugee Council and other community "
        "organisations."
        "[P] Her artistic practice centres on archives and found images, "
        "considering the tensions in the production of knowledge and its "
        "circulation. Her practice has been supported by several grants including "
        "from the Mead Fellowship, Wellcome Trust and UCL Grand Challenges."
        "[P] In 2019 she was diagnosed with M.E., became unemployed and spent "
        "five years often bedbound and housebound. Improvements in health "
        "enabled her to co-found Afield from a family legacy in 2025. She lives "
        "a sometimes life – sometimes active and sometimes in bed."
    ),
    "Mike Saunders": (
        "Mike is an entrepreneur, technologist and trustee, interested in the "
        "way that communities are impacted by, and respond to environmental "
        "crises. He founded community platform Commonplace, helping councils "
        "and developers to engage and co-design with over 12M local people. "
        "Commonplace data consistently shows nature and green space to be "
        "amongst the top two priorities for urban communities. Mike is also "
        "deputy chair of Trinity College London and a trustee of Open City, "
        "which amongst other things runs the Open House Festival. He previously "
        "led digital at Kew Gardens, was a member of the Speaker's Advisory "
        "Committee on Public Engagement at Parliament, ActionAid's digital board "
        "and worked in government and broadcasting. He has a design MA, and "
        "trained as a software engineer."
    ),
    "Joana Esgalhado": (
        "Joana is a programme manager with an environmental justice background. "
        "She has designed and delivered placemaking and education projects that "
        "create positive social and environmental impact, both in the UK and "
        "Portugal. She is also a community gardener and nature educator."
    ),
}

SITE_CONFIG = {
    "hero_heading":       "Creative responses to environmental injustice.",
    "hero_cta_label":     "CONTINUE ↓",
    "mission_intro":      "Our purpose is to support those most affected by environmental injustice to lead research, and shape their local ecosystems.",
    "mission_body":       (
        "Lower-income communities and people from global majority backgrounds "
        "are disproportionately affected by climate change and are often "
        "excluded from decisions that shape their environment — inequities "
        "rooted in a long history of colonialism and racism."
        "[P] We trust that those with lived experience of environmental "
        "injustice are the experts in imagining solutions that directly address "
        "their needs and create conditions for wider change."
        "[P] We value collaboration, dialogue and joy, and work in the spirit "
        "of mutuality with our grantees and with non-human species, listening "
        "to and learning from them."
    ),
    "values_intro":       "The way we work is as important as everything that we do.",
    "contact_email":      "hello@afield.org.uk",
    "footer_credit_label":"Design by Madalena Studio",
    "footer_credit_url":  "https://www.madalenastudio.com",
}

# ──────────────────────────────────────────────────────────────────────
# Sync runner
# ──────────────────────────────────────────────────────────────────────


def update_or_skip(table_name, records, match_key, match_value, new_fields):
    rec = find_by(records, match_key, match_value)
    if not rec:
        return ("missed", None, None)
    diffs = {}
    for k, v in new_fields.items():
        cur = rec.get("fields", {}).get(k)
        if cur != v:
            diffs[k] = v
    if not diffs:
        return ("already-correct", rec["id"], {})
    patch_record(table_name, rec["id"], diffs)
    return ("updated", rec["id"], diffs)


def main():
    applied, already, missed = 0, 0, 0

    # ─── GRANTS ───────────────────────────────────────────────────────
    grants = list_all("Grants")
    grants_edits = [
        ("wilding", {
            "Card Intro":        WILDING_CARD_INTRO,
            "Card Announcement": WILDING_CARD_ANNOUNCEMENT,
            "Card Body":         WILDING_CARD_BODY,
            "Detail Intro":      WILDING_DETAIL_INTRO,
            "Detail Body":       WILDING_DETAIL_BODY,
        }),
        ("arts", {
            "Card Intro":        ARTS_CARD_INTRO,
            "Card Announcement": ARTS_CARD_ANNOUNCEMENT,
            "Card Body":         ARTS_CARD_BODY,
            "Detail Intro":      ARTS_DETAIL_INTRO,
            "Detail Body":       ARTS_DETAIL_BODY,
        }),
    ]
    for type_val, fields in grants_edits:
        result, rec_id, diffs = update_or_skip("Grants", grants, "Type", type_val, fields)
        if result == "updated":
            print(f"✓ Grants / Type={type_val} — updated fields: {list(diffs.keys())}")
            applied += 1
        elif result == "already-correct":
            print(f"— Grants / Type={type_val} — already correct")
            already += 1
        else:
            print(f"✗ Grants / Type={type_val} — record not found")
            missed += 1

    # ─── VALUES ───────────────────────────────────────────────────────
    values_records = list_all("Values")
    for name, description in VALUES.items():
        result, rec_id, diffs = update_or_skip("Values", values_records, "Name", name, {"Description": description})
        if result == "updated":
            print(f"✓ Values / {name} — Description updated")
            applied += 1
        elif result == "already-correct":
            print(f"— Values / {name} — already correct")
            already += 1
        else:
            print(f"✗ Values / {name} — record not found")
            missed += 1

    # ─── TEAM ─────────────────────────────────────────────────────────
    team_records = list_all("Team")
    for name, bio in TEAM.items():
        rec = find_by(team_records, "Name", name)
        if rec:
            cur_bio = rec.get("fields", {}).get("Bio")
            if cur_bio == bio:
                print(f"— Team / {name} — already correct")
                already += 1
            else:
                patch_record("Team", rec["id"], {"Bio": bio})
                print(f"✓ Team / {name} — Bio updated")
                applied += 1
        else:
            # Joana is missing in current Airtable; create her.
            create_record("Team", {"Name": name, "Bio": bio})
            print(f"✓ Team / {name} — CREATED new record")
            applied += 1

    # ─── SITE CONFIG ──────────────────────────────────────────────────
    # The Site Config table currently has rows with a "Name" field
    # (hero_heading, mission_body, …) and a "Notes" field describing what
    # the row holds — but no "Value" column. The Airtable API can't add
    # new fields (only the web UI can), so this section reports what's
    # missing and what to add. Once the in-house team adds a "Value"
    # column in Airtable, re-running this script will populate it.
    config_records = list_all("Site Config")
    existing_names = {r.get("fields", {}).get("Name") for r in config_records}
    has_value_field = any("Value" in r.get("fields", {}) for r in config_records)
    if not has_value_field:
        print()
        print("⚠ Site Config: no 'Value' column exists in the Airtable table.")
        print("  Add a 'Value' single-line-text (or long-text) field to the")
        print("  Site Config table in Airtable. Then re-run this script — it")
        print("  will populate every row from the HTML.")
        print()
        print("  Rows that need values once the column exists:")
        for key in SITE_CONFIG:
            present = "✓" if key in existing_names else "+"
            print(f"    {present} {key}")
        print("  ('+' = the row also needs to be created)")
        missed += len(SITE_CONFIG)
    else:
        for key, value in SITE_CONFIG.items():
            rec = find_by(config_records, "Name", key)
            if not rec:
                print(f"✗ Site Config / Name={key} — row not found")
                missed += 1
                continue
            cur = rec.get("fields", {}).get("Value")
            if cur == value:
                print(f"— Site Config / {key} — already correct")
                already += 1
            else:
                patch_record("Site Config", rec["id"], {"Value": value})
                print(f"✓ Site Config / {key} — Value updated")
                applied += 1

    print(f"\nDone. Applied {applied}, already-correct {already}, missed {missed}.")
    if missed:
        sys.stderr.write("Some records were not found. Review the ✗ lines above.\n")
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"✗ {e}\n")
        sys.exit(1)
