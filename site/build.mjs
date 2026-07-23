// Static site generator for skills.henryzh.dev
// Parses every <skill>/SKILL.md in the repo root, groups them using the
// category headings from README.md, and emits a clean editorial catalog
// plus a detail page per skill.

import { readFileSync, writeFileSync, readdirSync, statSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import matter from "gray-matter";
import { marked } from "marked";
import {
  CATEGORIES,
  PIPELINE,
  categorizeSkill,
  categoryLabel,
  normalize,
} from "./map.config.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = join(__dirname, "..");
const DIST = join(__dirname, "dist");
const GH = "https://github.com/caezium/skills";
const GH_TREE = `${GH}/tree/main`;
const GH_BLOB = `${GH}/blob/main`;
const INSTALLED_SNAPSHOT = join(__dirname, "installed-skills.json");

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

function loadInstalledSnapshot() {
  if (!existsSync(INSTALLED_SNAPSHOT)) {
    return { schemaVersion: 1, updatedAt: null, skills: [] };
  }
  try {
    const snapshot = JSON.parse(readFileSync(INSTALLED_SNAPSHOT, "utf8"));
    if (!Array.isArray(snapshot.skills)) throw new Error("skills must be an array");
    return snapshot;
  } catch (error) {
    throw new Error(`Invalid installed-skills.json: ${error.message}`);
  }
}

function buildInventory(repoSkills, snapshot) {
  const byName = new Map();

  for (const skill of snapshot.skills) {
    const key = normalize(skill.name);
    if (!key) continue;
    byName.set(key, {
      name: skill.name,
      description: skill.description || "",
      sources: Array.isArray(skill.sources) ? skill.sources : [],
      copies: Number(skill.copies) || 1,
      repoSlug: null,
    });
  }

  for (const skill of repoSkills) {
    const key = normalize(skill.name);
    const existing = byName.get(key) || {
      name: skill.name,
      description: "",
      sources: [],
      copies: 1,
      repoSlug: null,
    };
    existing.name = skill.name;
    existing.description = skill.description || existing.description;
    existing.sources = [...new Set([...existing.sources, "personal"])].sort();
    existing.repoSlug = skill.slug;
    byName.set(key, existing);
  }

  return [...byName.values()]
    .map((skill) => {
      const category = categorizeSkill(skill);
      return {
        ...skill,
        category: category.id,
        categoryMethod: category.method,
        blurb: firstSentence(skill.description),
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name, "en", { sensitivity: "base" }));
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

function layout({ title, description, body, page, footerNote = null }) {
  const homeCurrent = page === "home" ? ` aria-current="page"` : "";
  const mapCurrent = page === "map" ? ` aria-current="page"` : "";
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
      <a href="/"${homeCurrent}>Catalog</a>
      <a href="/map/"${mapCurrent}>Production map</a>
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
    <p class="muted">${footerNote ? esc(footerNote) : "Generated from SKILL.md frontmatter and rebuilt on every push."}</p>
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

function pipelineSkillHtml(name, inventoryByName) {
  const skill = inventoryByName.get(normalize(name));
  if (!skill) return `<span class="skill-token unavailable">${esc(name)}</span>`;
  if (skill.repoSlug) {
    return `<a class="skill-token" href="/skills/${esc(skill.repoSlug)}/">${esc(skill.name)}</a>`;
  }
  return `<span class="skill-token external" title="Installed outside the personal skills repository">${esc(skill.name)}</span>`;
}

function inventoryCardHtml(skill) {
  const source = skill.sources.length ? skill.sources.join(", ") : "personal";
  const copyLabel = skill.copies > 1 ? `${skill.copies} installed copies` : "1 installed copy";
  const content = `<h3>${esc(skill.name)}</h3>
        <p>${esc(skill.blurb || "No description provided.")}</p>
        <span class="source">${esc(source)} · ${esc(copyLabel)}</span>`;
  const search = esc(`${skill.name} ${skill.description} ${categoryLabel(skill.category)} ${source}`.toLowerCase());

  if (skill.repoSlug) {
    return `      <a class="inventory-card" href="/skills/${esc(skill.repoSlug)}/" data-search="${search}">
        ${content}
      </a>`;
  }
  return `      <article class="inventory-card external-card" data-search="${search}">
        ${content}
      </article>`;
}

function pipelineHtml(inventory) {
  const inventoryByName = new Map(inventory.map((skill) => [normalize(skill.name), skill]));
  return PIPELINE.map((stage) => {
    const skills = stage.skills
      .map((name) => pipelineSkillHtml(name, inventoryByName))
      .join("");
    return `  <article class="pipeline-stage" id="${esc(stage.id)}">
    <div class="stage-copy">
      <h3>${esc(stage.title)}</h3>
      <p>${esc(stage.description)}</p>
    </div>
    <div class="stage-tools">
      <div class="skill-tokens">${skills}</div>
      ${stage.gap ? `<p class="gap">${esc(stage.gap)}</p>` : ""}
      <p class="gate">${esc(stage.gate)}</p>
    </div>
  </article>`;
  }).join("\n");
}

function mapPage(inventory, snapshot) {
  const counts = new Map();
  for (const skill of inventory) {
    counts.set(skill.category, (counts.get(skill.category) || 0) + 1);
  }

  const categoryNav = [
    ...CATEGORIES.filter((category) => counts.has(category.id)),
    ...(counts.has("review") ? [{ id: "review", label: "Needs review" }] : []),
  ]
    .map((category) => `<a href="#category-${esc(category.id)}">${esc(category.label)} <span>${counts.get(category.id) || 0}</span></a>`)
    .join("");

  const groups = [
    ...CATEGORIES,
    { id: "review", label: "Needs review" },
  ]
    .filter((category) => counts.has(category.id))
    .map((category) => {
      const cards = inventory
        .filter((skill) => skill.category === category.id)
        .map(inventoryCardHtml)
        .join("\n");
      return `<section class="inventory-group" id="category-${esc(category.id)}" data-inventory-group>
  <header>
    <h2>${esc(category.label)}</h2>
    <span>${counts.get(category.id)} skills</span>
  </header>
  <div class="inventory-grid">
${cards}
  </div>
</section>`;
    })
    .join("\n");

  const repoCount = inventory.filter((skill) => skill.repoSlug).length;
  const externalCount = inventory.length - repoCount;
  const updated = snapshot.updatedAt
    ? new Date(snapshot.updatedAt).toISOString().slice(0, 10)
    : "repository build";

  const body = `<section class="map-hero">
  <div>
    <p class="kicker">Installed skills map</p>
    <h1>From an idea to production</h1>
    <p class="lede">A practical sequence for challenging ideas, limiting scope, shipping safely, and learning from real use.</p>
  </div>
  <dl class="map-stats">
    <div><dt>Unique skills</dt><dd>${inventory.length}</dd></div>
    <div><dt>Personal repo</dt><dd>${repoCount}</dd></div>
    <div><dt>Runtime and plugins</dt><dd>${externalCount}</dd></div>
    <div><dt>Snapshot</dt><dd>${esc(updated)}</dd></div>
  </dl>
</section>

<section class="pipeline">
  <header class="section-intro">
    <h2>The production path</h2>
    <p>Use the smallest relevant set. Each gate exists because later detail multiplies the cost of an earlier mistake.</p>
  </header>
${pipelineHtml(inventory)}
</section>

<aside class="map-principle">
  <h2>When the AI should stop and ask</h2>
  <p>Ask when the answer changes product value, external behavior, irreversible architecture, risk tolerance, or scope. Look up repository facts and continue independently for reversible implementation details already settled by the spec.</p>
</aside>

<section class="inventory">
  <header class="section-intro inventory-intro">
    <div>
      <h2>Full installed inventory</h2>
      <p>The local snapshot includes personal skills, shared agent skills, Codex skills, and installed plugin skills.</p>
    </div>
    <label class="map-search">
      <span>Filter skills</span>
      <input id="map-q" type="search" placeholder="Name, purpose, or category" autocomplete="off">
    </label>
  </header>
  <nav class="category-nav" aria-label="Skill categories">${categoryNav}</nav>
  <p id="map-count" class="map-count" aria-live="polite"></p>
${groups}
</section>

<script>
(function(){
  var input=document.getElementById('map-q');
  var cards=[].slice.call(document.querySelectorAll('.inventory-card'));
  var groups=[].slice.call(document.querySelectorAll('[data-inventory-group]'));
  var count=document.getElementById('map-count');
  function run(){
    var value=input.value.trim().toLowerCase();
    var visible=0;
    cards.forEach(function(card){
      var hit=!value||card.dataset.search.indexOf(value)>-1;
      card.hidden=!hit;
      if(hit)visible++;
    });
    groups.forEach(function(group){
      group.hidden=!group.querySelector('.inventory-card:not([hidden])');
    });
    count.textContent=value ? visible+' of '+cards.length+' skills' : '';
  }
  input.addEventListener('input',run);
})();
</script>`;

  return layout({
    title: "Production skills map - skills.henryzh.dev",
    description: `A production workflow and categorized inventory of ${inventory.length} installed agent skills.`,
    body,
    page: "map",
    footerNote: `Installed snapshot ${updated}. Repository skills are refreshed during every build.`,
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
  const snapshot = loadInstalledSnapshot();
  const inventory = buildInventory(skills, snapshot);

  rmSync(DIST, { recursive: true, force: true });
  mkdirSync(DIST, { recursive: true });

  writeFileSync(join(DIST, "index.html"), indexPage(skills, readme, mine));
  const mapDirectory = join(DIST, "map");
  mkdirSync(mapDirectory, { recursive: true });
  writeFileSync(join(mapDirectory, "index.html"), mapPage(inventory, snapshot));
  writeFileSync(join(DIST, "skills.json"), `${JSON.stringify({
    updatedAt: snapshot.updatedAt,
    count: inventory.length,
    skills: inventory.map(({ name, description, sources, copies, repoSlug, category }) => ({
      name,
      description,
      sources,
      copies,
      repoSlug,
      category,
    })),
  }, null, 2)}\n`);
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

  console.log(`Built ${skills.length} repository skills and ${inventory.length} installed skills → ${DIST}`);
}

const CSS = readFileSync(join(__dirname, "style.css"), "utf8");

build();
