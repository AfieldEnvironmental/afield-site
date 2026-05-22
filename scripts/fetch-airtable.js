/*
 * Fetches all Airtable tables used by the site and writes them to
 * data/airtable.json. Runs inside GitHub Actions on push, on a schedule,
 * and on manual trigger. The Airtable token never reaches the browser —
 * it lives only in GitHub Secrets and only during this build step.
 */

const fs   = require('fs');
const path = require('path');

/* The script tries to sort by an "Order" column first; if a table doesn't
   have that column Airtable returns 422 and we retry without the sort. */
const TABLES = ['Site Config', 'Grants', 'Values', 'Team', 'Cycler Words'];
const TOKEN  = process.env.AIRTABLE_TOKEN;
const BASE   = process.env.AIRTABLE_BASE;

if (!TOKEN || !BASE) {
  console.error('✗ Missing AIRTABLE_TOKEN or AIRTABLE_BASE env vars.');
  console.error('  Add them at: Settings → Secrets and variables → Actions');
  process.exit(1);
}

async function rawFetch(name, withSort) {
  let url = 'https://api.airtable.com/v0/' + BASE + '/' + encodeURIComponent(name);
  if (withSort) url += '?sort[0][field]=Order&sort[0][direction]=asc';
  const res = await fetch(url, { headers: { Authorization: 'Bearer ' + TOKEN } });
  return { res, body: await res.text() };
}

async function fetchTable(name) {
  /* Try with Order sort first. If the table doesn't have an Order field,
     Airtable returns 422 UNKNOWN_FIELD_NAME — retry without the sort. */
  let { res, body } = await rawFetch(name, true);
  if (res.status === 422 && body.indexOf('UNKNOWN_FIELD_NAME') !== -1) {
    process.stdout.write('(no Order col, unsorted) ');
    ({ res, body } = await rawFetch(name, false));
  }
  if (!res.ok) {
    throw new Error('Airtable "' + name + '" failed: ' + res.status + ' ' + body);
  }
  return JSON.parse(body);
}

(async () => {
  const data = {};
  for (const name of TABLES) {
    process.stdout.write('  fetching "' + name + '"... ');
    data[name] = await fetchTable(name);
    console.log('✓ ' + ((data[name].records || []).length) + ' records');
  }

  const outDir = path.join(__dirname, '..', 'data');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'airtable.json'), JSON.stringify(data));

  console.log('✓ wrote data/airtable.json (' +
    fs.statSync(path.join(outDir, 'airtable.json')).size + ' bytes)');
})().catch(err => {
  console.error('✗ Build failed:', err.message);
  process.exit(1);
});
