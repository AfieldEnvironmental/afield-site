#!/usr/bin/env node
/*
 * One-off: applies the copy edits from commit fef885e to Airtable.
 *
 * Safe to re-run: every edit checks for the "before" text and skips
 * if it isn't present, so a second run is a no-op.
 *
 * Run with:
 *   AIRTABLE_TOKEN=pat... AIRTABLE_BASE=app... node scripts/update-airtable-copy.js
 *
 * Token needs data.records:read + data.records:write on this base.
 */

const TOKEN = process.env.AIRTABLE_TOKEN;
const BASE  = process.env.AIRTABLE_BASE;
if (!TOKEN || !BASE) {
  console.error('✗ Missing AIRTABLE_TOKEN or AIRTABLE_BASE env vars.');
  console.error('  Run:  AIRTABLE_TOKEN=... AIRTABLE_BASE=... node scripts/update-airtable-copy.js');
  process.exit(1);
}

const HEADERS = { Authorization: 'Bearer ' + TOKEN, 'Content-Type': 'application/json' };

/*
 * Each edit:
 *   table       — Airtable table name
 *   match       — { fieldName: value } that uniquely identifies the record
 *   fields      — field names to try in order; the FIRST one that contains
 *                 the "before" text gets the replacement (lets us survive
 *                 minor schema drift, e.g. content moved between Card Body
 *                 and Detail Body)
 *   find        — literal string to replace (plain substring)
 *   findRegex   — alternative to `find` for paragraph deletions where we
 *                 need to consume a `[P]` separator too
 *   replace     — replacement string ('' for deletion)
 */
const EDITS = [
  // ─── WILDING ───────────────────────────────────────────────────────
  { table:'Grants', match:{Type:'wilding'}, fields:['Card Intro'],
    find:'affects low-income', replace:'affect low-income' },

  { table:'Grants', match:{Type:'wilding'}, fields:['Card Announcement'],
    find:'Autumn 2026', replace:'autumn 2026' },

  { table:'Grants', match:{Type:'wilding'}, fields:['Detail Body'],
    find:'They result from failures', replace:'These result from failures' },

  { table:'Grants', match:{Type:'wilding'}, fields:['Detail Body'],
    find:'The result is that local communities and the wider urban ecology suffer from:',
    replace:'Consequently, local communities and the wider urban ecology experience:' },

  { table:'Grants', match:{Type:'wilding'}, fields:['Detail Body'],
    find:'support them to realise', replace:'support grantees to realise' },

  // Delete the "Our goal over the next five years..." paragraph + the
  // [P] separator that introduces it. Also matches if it's the last
  // paragraph (trailing [P] is optional).
  { table:'Grants', match:{Type:'wilding'}, fields:['Detail Body'],
    findRegex:/\s*\[P\]\s*Our goal over the next five years is to support around 10 people on their way to creating new or caring for existing nature spaces in their community\.?\s*/,
    replace:'' },

  // ─── ARTS ──────────────────────────────────────────────────────────
  { table:'Grants', match:{Type:'arts'}, fields:['Card Intro'],
    find:'environmental knowledge', replace:'ecological knowledge' },

  { table:'Grants', match:{Type:'arts'}, fields:['Card Announcement'],
    find:'Winter 2026', replace:'winter 2026' },

  // The user's spec puts "We seek to nurture excellence" and the
  // "Initially we will trial..." rewrite on the Arts card, but in the
  // HTML fallback "Initially we will trial..." lives in the Detail
  // Body. Try Card Body first, fall through to Detail Body if it's
  // there instead.
  { table:'Grants', match:{Type:'arts'}, fields:['Card Body','Detail Body'],
    find:'We nurture excellence', replace:'We seek to nurture excellence' },

  { table:'Grants', match:{Type:'arts'}, fields:['Card Body','Detail Body'],
    find:'Initially we will trial an open call approach, and in the first year we will award seven grants of up to £30,000 for projects of up to three years.',
    replace:'Initially we will trial an open call approach, awarding grants of up to £30,000 for projects of up to three years.' },

  { table:'Grants', match:{Type:'arts'}, fields:['Detail Intro'],
    find:'environmental knowledge', replace:'ecological knowledge' },

  // Delete the "We believe that we can support excellence..." paragraph.
  // Greedy-stops at the next [P] OR end-of-string so we don't gobble
  // following paragraphs. Both em-dash (—) and ASCII hyphen handled.
  { table:'Grants', match:{Type:'arts'}, fields:['Detail Body'],
    findRegex:/\s*\[P\]\s*We believe that we can support excellence both in the arts and in ecological research by focusing our resources on low-income artists who have been traditionally excluded from research funding\. Artists can make a unique and vital contribution to ecological research [—\-] they can work outside of, across, with and against traditional disciplines, developing insights and ideas that go beyond established scientific, technical and cultural frameworks\.\s*/,
    replace:'' },

  { table:'Grants', match:{Type:'arts'}, fields:['Detail Body'],
    find:'specified outputs', replace:'predetermined outputs' },

  // ─── VALUES ────────────────────────────────────────────────────────
  { table:'Values', match:{Name:'Bold'}, fields:['Description'],
    find:'We back communities to be bold too', replace:'We support communities to be bold too' },

  // Justice has two changes in one sentence ("operate" → "work" AND
  // delete "in everything we do"). Single regex covers both.
  { table:'Values', match:{Name:'Justice'}, fields:['Description'],
    findRegex:/Justice shapes how we operate\. We ask who benefits, who is missing, and what is fair, and we aim to hold ourselves accountable to those questions in everything we do\.?/,
    replace:'Justice shapes how we work. We ask who benefits, who is missing, and what is fair, and we aim to hold ourselves accountable to those questions.' },
];

async function listAll(table) {
  const records = [];
  let offset = null;
  do {
    const url = new URL('https://api.airtable.com/v0/' + BASE + '/' + encodeURIComponent(table));
    if (offset) url.searchParams.set('offset', offset);
    const r = await fetch(url, { headers: HEADERS });
    if (!r.ok) throw new Error('list ' + table + ': ' + r.status + ' ' + (await r.text()));
    const j = await r.json();
    records.push.apply(records, j.records);
    offset = j.offset;
  } while (offset);
  return records;
}

async function patchRecord(table, id, fields) {
  const url = 'https://api.airtable.com/v0/' + BASE + '/' + encodeURIComponent(table) + '/' + id;
  const r = await fetch(url, { method:'PATCH', headers: HEADERS, body: JSON.stringify({ fields }) });
  if (!r.ok) throw new Error('patch ' + table + '/' + id + ': ' + r.status + ' ' + (await r.text()));
  return r.json();
}

function recordMatches(rec, m) {
  for (const k of Object.keys(m)) {
    if (String(rec.fields[k] || '').toLowerCase() !== String(m[k]).toLowerCase()) return false;
  }
  return true;
}

function describe(e) {
  if (e.findRegex) return e.findRegex.toString().slice(0, 80) + '…';
  return '"' + e.find.slice(0, 60) + (e.find.length > 60 ? '…"' : '"');
}

(async () => {
  const cache = {};
  let applied = 0, alreadyCorrect = 0, missed = 0;

  for (const e of EDITS) {
    if (!cache[e.table]) {
      process.stdout.write('  fetching ' + e.table + '… ');
      cache[e.table] = await listAll(e.table);
      console.log(cache[e.table].length + ' records');
    }
    const rec = cache[e.table].find(r => recordMatches(r, e.match));
    if (!rec) {
      console.warn('✗ no ' + e.table + ' record matching ' + JSON.stringify(e.match));
      missed++;
      continue;
    }

    let hit = false;
    for (const field of e.fields) {
      const cur = rec.fields[field];
      if (typeof cur !== 'string') continue;

      let next;
      if (e.findRegex) {
        if (!e.findRegex.test(cur)) continue;
        next = cur.replace(e.findRegex, e.replace);
      } else {
        if (cur.indexOf(e.find) === -1) continue;
        next = cur.split(e.find).join(e.replace);
      }

      if (next === cur) {
        alreadyCorrect++;
        hit = true;
        break;
      }
      await patchRecord(e.table, rec.id, { [field]: next });
      rec.fields[field] = next; // keep cache in sync for chained edits
      console.log('✓ ' + e.table + ' / ' + JSON.stringify(e.match) + ' / ' + field);
      console.log('   - ' + describe(e));
      console.log('   + "' + (e.replace || '(deleted)').slice(0, 60) + '"');
      applied++;
      hit = true;
      break;
    }

    if (!hit) {
      // Already correct (re-run) is impossible to distinguish from
      // missed without re-reading what we just patched. Check whether
      // the replacement text is already present somewhere — if yes,
      // call it alreadyCorrect.
      const fields = e.fields.map(f => rec.fields[f] || '').join('\n');
      const probe = e.replace && e.replace.length > 6 ? e.replace : null;
      if (probe && fields.indexOf(probe) !== -1) {
        alreadyCorrect++;
      } else {
        console.warn('⚠ no match for ' + describe(e) + ' in ' + e.table + '/' + JSON.stringify(e.match) + '/' + e.fields.join('|'));
        missed++;
      }
    }
  }

  console.log('\nApplied ' + applied + ', already-correct ' + alreadyCorrect + ', missed ' + missed + '.');
  if (missed > 0) {
    console.error('Some edits could not be applied. Review the ⚠ lines above and either fix the source text manually in Airtable or update this script.');
    process.exit(2);
  }
})().catch(err => {
  console.error('✗ ' + err.message);
  process.exit(1);
});
