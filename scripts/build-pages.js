/*
 * Generates standalone content pages from the Airtable "Pages" table.
 *
 * Runs in GitHub Actions AFTER scripts/fetch-airtable.js (it reads the
 * data/airtable.json that step writes — no Airtable token needed here).
 * For every row with Published ticked it renders /<slug>/index.html from
 * the template below, plus a /pages/index.html listing them all.
 *
 * Airtable table: "Pages" — create it in the Airtable UI with EXACTLY
 * these field names:
 *   Title      single line text   (required)
 *   Slug       single line text   (required — becomes the URL,
 *                                  e.g. "our-2026-launch" →
 *                                  afield.org.uk/our-2026-launch/)
 *   Body       long text          (required — same [P] paragraph and
 *                                  [LI] bullet markers as Grants copy)
 *   Image URL  url                 (optional — full-width image under
 *                                  the title; use a Cloudinary URL)
 *   Published  checkbox            (page only builds when ticked)
 *   Order      number              (optional — sort on the /pages/ list)
 *
 * The deploy workflow runs hourly, so a newly-ticked page is live
 * within the hour — or immediately via Actions → Build and Deploy →
 * Run workflow.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const DATA = path.join(ROOT, 'data', 'airtable.json');

/* Slugs that would collide with real files/folders in the repo. */
const RESERVED = ['assets', 'data', 'export', 'scripts', 'netlify', 'pages', 'index'];

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/* Same [P] / [LI] convention as the Grants copy in index.html. */
function bodyToHTML(text) {
  let html = '';
  String(text).split('[P]').forEach(function (block) {
    block = block.trim();
    if (!block) return;
    if (block.indexOf('[LI]') !== -1) {
      const parts = block.split('[LI]');
      const intro = parts.shift().trim();
      if (intro) html += '<p>' + esc(intro) + '</p>';
      html += '<ul>';
      parts.forEach(function (li) {
        li = li.trim();
        if (li) html += '<li>' + esc(li) + '</li>';
      });
      html += '</ul>';
    } else {
      html += '<p>' + esc(block) + '</p>';
    }
  });
  return html;
}

/* First ~155 chars of the body, markers stripped — for meta description. */
function summarise(text) {
  const plain = String(text).replace(/\[P\]|\[LI\]/g, ' ').replace(/\s+/g, ' ').trim();
  return plain.length > 155 ? plain.slice(0, 152) + '…' : plain;
}

function pageHTML(f) {
  const title = esc(f.Title);
  const desc = esc(summarise(f.Body));
  const img = f['Image URL']
    ? '<img class="page-image" src="' + esc(f['Image URL']) + '" alt="">'
    : '';
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} — Afield</title>
<meta name="description" content="${desc}">
<meta property="og:title" content="${title} — Afield">
<meta property="og:description" content="${desc}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/gt-cinetype.css">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'GT Cinetype', sans-serif;
    background: #b1ffcb;               /* landing mint */
    color: #1a1a0e;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .page-nav { padding: clamp(20px, 3vw, 44px); }
  .page-nav a {
    display: inline-flex;
    align-items: center;
    text-decoration: none;
    color: #1a1a0e;
    position: relative;
    width: 118px;
    height: 96px;
  }
  .page-nav svg { position: absolute; inset: 0; width: 100%; height: 100%; }
  .page-nav span {
    position: relative;
    font-weight: 700;
    font-size: 26px;
    letter-spacing: -0.02em;
    padding-left: 22px;
  }
  main {
    flex: 1;
    width: 100%;
    max-width: 760px;
    margin: 0 auto;
    padding: clamp(24px, 5vw, 64px) clamp(20px, 5vw, 40px) clamp(60px, 8vw, 120px);
  }
  h1 {
    font-weight: 400;
    font-size: clamp(36px, 6vw, 72px);
    letter-spacing: -0.03em;
    line-height: 1.05;
    text-wrap: balance;
    margin-bottom: clamp(28px, 4vw, 52px);
  }
  .page-image {
    width: 100%;
    height: auto;
    display: block;
    margin-bottom: clamp(28px, 4vw, 52px);
  }
  main p, main li {
    font-size: clamp(16px, 1.15vw, 18px);
    line-height: 1.65;
    max-width: 68ch;
  }
  main p { margin-bottom: 1.4em; }
  main ul { margin: 0 0 1.4em 1.2em; }
  main li { margin-bottom: 0.5em; }
  footer {
    padding: clamp(20px, 3vw, 44px);
    font-size: 14px;
  }
  footer a { color: #1a1a0e; }
</style>
</head>
<body>
<nav class="page-nav">
  <a href="/" aria-label="Afield home">
    <svg viewBox="0 0 92.5 75.8" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient id="g" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#8ee6f5"/>
          <stop offset="100%" stop-color="#c8f4fa"/>
        </linearGradient>
      </defs>
      <polygon points="75.4 19.8 63.4 .8 .9 22 2.4 58.1 26.2 65.4 58 75 91.6 45.3" fill="url(#g)"/>
    </svg>
    <span>afield</span>
  </a>
</nav>
<main>
  <h1>${title}</h1>
  ${img}
  ${bodyToHTML(f.Body)}
</main>
<footer>
  <a href="/">&larr; afield.org.uk</a>
</footer>
</body>
</html>
`;
}

function listHTML(pages) {
  const items = pages.map(function (f) {
    return '<li><a href="/' + esc(f.Slug) + '/">' + esc(f.Title) + '</a></li>';
  }).join('\n    ');
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pages — Afield</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/gt-cinetype.css">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'GT Cinetype', sans-serif; background: #b1ffcb; color: #1a1a0e; padding: clamp(20px, 5vw, 64px); }
  h1 { font-weight: 400; font-size: clamp(36px, 6vw, 72px); letter-spacing: -0.03em; margin-bottom: 40px; }
  li { list-style: none; margin-bottom: 14px; }
  a { color: #1a1a0e; font-size: clamp(17px, 1.4vw, 21px); }
  .home { display: inline-block; margin-top: 48px; font-size: 15px; }
</style>
</head>
<body>
  <h1>Pages</h1>
  <ul>
    ${items}
  </ul>
  <a class="home" href="/">&larr; afield.org.uk</a>
</body>
</html>
`;
}

/* ── main ── */
if (!fs.existsSync(DATA)) {
  console.log('· data/airtable.json not found — run scripts/fetch-airtable.js first. Nothing to do.');
  process.exit(0);
}

const data = JSON.parse(fs.readFileSync(DATA, 'utf8'));
const records = ((data.Pages || {}).records || []);

const seen = new Set();
const built = [];

records.forEach(function (rec) {
  const f = rec.fields || {};
  if (!f.Published) return;
  if (!f.Title || !f.Slug || !f.Body) {
    console.warn('! Skipping page "' + (f.Title || rec.id) + '" — needs Title, Slug and Body.');
    return;
  }
  const slug = String(f.Slug).toLowerCase().trim()
    .replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  if (!slug || RESERVED.indexOf(slug) !== -1) {
    console.warn('! Skipping page "' + f.Title + '" — slug "' + f.Slug + '" is empty or reserved.');
    return;
  }
  if (seen.has(slug)) {
    console.warn('! Skipping page "' + f.Title + '" — duplicate slug "' + slug + '".');
    return;
  }
  seen.add(slug);
  const dir = path.join(ROOT, slug);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), pageHTML({ ...f, Slug: slug }));
  built.push({ Title: f.Title, Slug: slug, Order: typeof f.Order === 'number' ? f.Order : 9999 });
  console.log('✓ built /' + slug + '/');
});

if (built.length) {
  built.sort(function (a, b) { return a.Order - b.Order; });
  const dir = path.join(ROOT, 'pages');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), listHTML(built));
  console.log('✓ built /pages/ (' + built.length + ' page' + (built.length === 1 ? '' : 's') + ')');
} else {
  console.log('· No published pages in Airtable — nothing generated.');
}
