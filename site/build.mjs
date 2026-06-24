// Static site generator for skills.henryzh.dev
// Parses every <skill>/SKILL.md in the repo root, groups them using the
// category headings from README.md, and emits a clean editorial catalog
// plus a detail page per skill.

import { readFileSync, writeFileSync, readdirSync, statSync, mkdirSync, rmSync, cpSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import matter from "gray-matter";
import { marked } from "marked";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = join(__dirname, "..");
const DIST = join(__dirname, "dist");
const GH = "https://github.com/caezium/skills";
const GH_TREE = `${GH}/tree/main`;
const GH_BLOB = `${GH}/blob/main`;

// Directories at repo root that are not skills.
const NOT_SKILLS = new Set(["site", "bin", "commands", ".git", ".github", "node_modules"]);

// ---------------------------------------------------------------------------
// Collect skills
// ---------------------------------------------------------------------------
function collectSkills() {
  const skills = [];
  for (const name of readdirSync(REPO)) {
    if (NOT_SKILLS.has(name) || name.startsWith(".")) continue;
    const dir = join(REPO, name);
    if (!statSync(dir).isDirectory()) continue;
    const skillFile = join(dir, "SKILL.md");
    if (!existsSync(skillFile)) continue;
    const raw = readFileSync(skillFile, "utf8");
    const { data, content } = matter(raw);
    const supporting = readdirSync(dir)
      .filter((f) => f !== "SKILL.md" && f.endsWith(".md"));
    skills.push({
      slug: name,
      name: data.name || name,
      description: (data.description || "").trim(),
      version: data.version ? String(data.version) : null,
      argumentHint: data["argument-hint"] || null,
      author: data.author || null,
      tags: extractTags(data),
      body: content.trim(),
      supporting,
    });
  }
  return skills;
}

function extractTags(data) {
  const t = data?.metadata?.openclaw?.tags || data?.tags;
  if (Array.isArray(t)) return t.slice(0, 12);
  return [];
}

// ---------------------------------------------------------------------------
// Parse README for category grouping + curated one-liners
// ---------------------------------------------------------------------------
function parseReadme() {
  const md = readFileSync(join(REPO, "README.md"), "utf8");
  const lines = md.split("\n");
  const map = {}; // slug -> { category, blurb }
  const order = []; // category order
  let category = null;
  let inSkills = false;
  for (const line of lines) {
    if (/^##\s+Skills\b/.test(line)) { inSkills = true; continue; }
    if (/^##\s+Slash commands/.test(line)) { inSkills = false; continue; }
    if (!inSkills) continue;
    const h = line.match(/^###\s+(.+?)\s*$/);
    if (h) {
      category = h[1].trim();
      if (!order.includes(category)) order.push(category);
      continue;
    }
    const item = line.match(/^-\s+\*\*([^*]+)\*\*\s+[—-]\s+(.+?)\s*$/);
    if (item && category) {
      const slug = item[1].trim();
      map[slug] = { category, blurb: item[2].trim() };
    }
  }
  return { map, order };
}

// ---------------------------------------------------------------------------
// Markdown rendering: rewrite relative .md links to GitHub blob URLs
// ---------------------------------------------------------------------------
function renderBody(body, slug) {
  const renderer = new marked.Renderer();
  const origLink = renderer.link.bind(renderer);
  renderer.link = function (href, title, text) {
    if (typeof href === "object" && href !== null) {
      // marked v12 passes a token object
      const token = href;
      let h = token.href || "";
      if (isRelative(h)) token.href = `${GH_BLOB}/${slug}/${h}`;
      return origLink(token);
    }
    let h = href || "";
    if (isRelative(h)) href = `${GH_BLOB}/${slug}/${h}`;
    return origLink(href, title, text);
  };
  return marked.parse(body, { renderer, mangle: false, headerIds: true });
}

function isRelative(h) {
  return h && !/^(https?:|mailto:|#|\/)/.test(h);
}

// ---------------------------------------------------------------------------
// HTML templates
// ---------------------------------------------------------------------------
function esc(s = "") {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function layout({ title, description, body, page }) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
</head>
<body class="page-${page}">
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/">skills<span>.henryzh.dev</span></a>
    <nav>
      <a href="${GH}">GitHub ↗</a>
    </nav>
  </div>
</header>
<main class="wrap">
${body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <p>A personal directory of agent skills. Source of truth: <a href="${GH}">caezium/skills</a>.</p>
    <p class="muted">Generated from <code>SKILL.md</code> frontmatter · rebuilt on every push.</p>
  </div>
</footer>
</body>
</html>`;
}

function cardHtml(s) {
  return `      <a class="card" href="/skills/${esc(s.slug)}/" data-search="${esc((s.name + " " + s.description + " " + s.tags.join(" ")).toLowerCase())}">
        <h3>${esc(s.name)}${s.version ? `<span class="ver">v${esc(s.version)}</span>` : ""}</h3>
        <p>${esc(s._blurb)}</p>
      </a>`;
}

function sectionHtml(label, list, { id } = {}) {
  const cards = list
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(cardHtml)
    .join("\n");
  return `  <section class="cat"${id ? ` id="${esc(id)}"` : ""} data-cat="${esc(label)}">
    <h2>${esc(label)}</h2>
    <div class="grid">
${cards}
    </div>
  </section>`;
}

function indexPage(skills, readme, mine) {
  const byCat = new Map();
  for (const cat of readme.order) byCat.set(cat, []);
  const OTHER = "Other";
  for (const s of skills) {
    const meta = readme.map[s.slug];
    const cat = meta?.category || OTHER;
    if (!byCat.has(cat)) byCat.set(cat, []);
    s._blurb = meta?.blurb || firstSentence(s.description);
    byCat.get(cat).push(s);
  }

  const mineSet = new Set(mine);
  const mineList = skills.filter((s) => mineSet.has(s.slug));
  const mineSection = mineList.length
    ? sectionHtml(`Made by me · ${mineList.length}`, mineList, { id: "mine" })
    : "";

  const sections =
    mineSection +
    "\n" +
    [...byCat.entries()]
      .filter(([, list]) => list.length)
      .map(([cat, list]) => sectionHtml(cat, list))
      .join("\n");

  const body = `<section class="hero">
  <h1>Agent skills</h1>
  <p class="lede">A working directory of ${skills.length} skills for coding agents — Claude Code, Cursor, and friends. Each one is a single <code>SKILL.md</code> the agent loads on demand.</p>
  <div class="search">
    <input id="q" type="search" placeholder="Search ${skills.length} skills…" autocomplete="off" aria-label="Search skills">
    <span id="count" class="count"></span>
  </div>
</section>
${sections}
<script>
(function(){
  var q=document.getElementById('q'),count=document.getElementById('count');
  var cards=[].slice.call(document.querySelectorAll('.card'));
  var cats=[].slice.call(document.querySelectorAll('.cat'));
  function run(){
    var v=q.value.trim().toLowerCase();
    var n=0;
    cards.forEach(function(c){
      var hit=!v||c.dataset.search.indexOf(v)>-1;
      c.style.display=hit?'':'none';
      if(hit)n++;
    });
    cats.forEach(function(s){
      var any=s.querySelector('.card:not([style*="none"])');
      s.style.display=any?'':'none';
    });
    count.textContent=v?(n+' / '+cards.length):'';
  }
  q.addEventListener('input',run);
})();
</script>`;

  return layout({
    title: "skills.henryzh.dev — a directory of agent skills",
    description: `A personal directory of ${skills.length} agent skills for Claude Code, Cursor, and other coding agents.`,
    body,
    page: "home",
  });
}

function firstSentence(text = "") {
  const m = text.match(/^(.*?[.!?])(\s|$)/);
  let s = (m ? m[1] : text).trim();
  // drop trailing "Use when …" triggers from the lede
  return s.replace(/\s*Use when.*$/i, "").trim() || text;
}

function skillPage(s, readme) {
  const meta = readme.map[s.slug];
  const cat = meta?.category || "Other";
  const tags = s.tags.length
    ? `<ul class="tags">${s.tags.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>`
    : "";
  const supporting = s.supporting.length
    ? `<aside class="supporting">
    <h2>Supporting files</h2>
    <ul>${s.supporting.map((f) => `<li><a href="${GH_BLOB}/${esc(s.slug)}/${esc(f)}">${esc(f)}</a></li>`).join("")}</ul>
  </aside>`
    : "";

  const body = `<article class="skill">
  <p class="crumb"><a href="/">skills</a> <span>/</span> <span class="muted">${esc(cat)}</span></p>
  <header class="skill-head">
    <h1>${esc(s.name)}${s.version ? `<span class="ver">v${esc(s.version)}</span>` : ""}</h1>
    <p class="desc">${esc(s.description)}</p>
    ${s.argumentHint ? `<p class="arghint"><code>${esc(s.argumentHint)}</code></p>` : ""}
    ${tags}
    <p class="links">
      <a class="btn" href="${GH_TREE}/${esc(s.slug)}">View folder on GitHub ↗</a>
      <a class="btn ghost" href="${GH_BLOB}/${esc(s.slug)}/SKILL.md">Raw SKILL.md ↗</a>
    </p>
  </header>
  <div class="prose">
${renderBody(s.body, s.slug)}
  </div>
  ${supporting}
</article>`;

  return layout({
    title: `${s.name} — skills.henryzh.dev`,
    description: firstSentence(s.description),
    body,
    page: "skill",
  });
}

// ---------------------------------------------------------------------------
// Build
// ---------------------------------------------------------------------------
function loadMine() {
  const f = join(__dirname, "mine.json");
  if (!existsSync(f)) return [];
  try {
    const arr = JSON.parse(readFileSync(f, "utf8"));
    return Array.isArray(arr) ? arr : arr.mine || [];
  } catch {
    return [];
  }
}

function build() {
  const skills = collectSkills();
  const readme = parseReadme();
  const mine = loadMine();

  rmSync(DIST, { recursive: true, force: true });
  mkdirSync(DIST, { recursive: true });

  writeFileSync(join(DIST, "index.html"), indexPage(skills, readme, mine));
  writeFileSync(join(DIST, "style.css"), CSS);

  for (const s of skills) {
    const dir = join(DIST, "skills", s.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "index.html"), skillPage(s, readme));
  }

  // 404
  writeFileSync(join(DIST, "404.html"), layout({
    title: "Not found — skills.henryzh.dev",
    description: "Page not found.",
    body: `<section class="hero"><h1>404</h1><p class="lede">That skill wandered off. <a href="/">Back to the directory.</a></p></section>`,
    page: "home",
  }));

  console.log(`Built ${skills.length} skills + index → ${DIST}`);
}

const CSS = readFileSync(join(__dirname, "style.css"), "utf8");

build();
