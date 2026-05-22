/*
 * Fetches all Airtable tables used by the site and writes them to
 * data/airtable.json. Runs inside GitHub Actions on push, on a schedule,
 * and on manual trigger. The Airtable token never reaches the browser —
 * it lives only in GitHub Secrets and only during this build step.
 */

const fs   = require('fs');
const path = require('path');

/* Tables that have an "Order" column get sorted; "Site Config" is just
   key/value pairs and has no Order field, so it's fetched unsorted. */
const TABLES = [
  { name: 'Site Config',  sort: false },
  { name: 'Grants',       sort: true  },
  { name: 'Values',       sort: true  },
  { name: 'Team',         sort: true  },
  { name: 'Cycler Words', sort: true  },
];
const TOKEN  = process.env.AIRTABLE_TOKEN;
const BASE   = process.env.AIRTABLE_BASE;

if (!TOKEN || !BASE) {
  console.error('✗ Missing AIRTABLE_TOKEN or AIRTABLE_BASE env vars.');
  console.error('  Add them at: Settings → Secrets and variables → Actions');
  process.exit(1);
}

async function fetchTable(name, sort) {
  let url = 'https://api.airtable.com/v0/' + BASE + '/' + encodeURIComponent(name);
  if (sort) url += '?sort[0][field]=Order&sort[0][direction]=asc';

  const res = await fetch(url, {
    headers: { Authorization: 'Bearer ' + TOKEN }
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error('Airtable "' + name + '" failed: ' + res.status + ' ' + body);
  }
  return res.json();
}

(async () => {
  const data = {};
  for (const t of TABLES) {
    process.stdout.write('  fetching "' + t.name + '"... ');
    data[t.name] = await fetchTable(t.name, t.sort);
    console.log('✓ ' + ((data[t.name].records || []).length) + ' records');
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
