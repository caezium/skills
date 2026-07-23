import {
  existsSync,
  readFileSync,
  readdirSync,
  realpathSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import matter from "gray-matter";
import { normalize } from "./map.config.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = realpathSync(join(__dirname, ".."));
const OUTPUT = join(__dirname, "installed-skills.json");
const HOME = process.env.HOME || "";
const IGNORED_DIRECTORIES = new Set([
  ".git",
  ".next",
  "dist",
  "node_modules",
  "__pycache__",
]);

function defaultRoots() {
  return [
    { path: REPO, source: "personal" },
    { path: join(HOME, ".agents", "skills"), source: "shared" },
    { path: join(HOME, ".codex", "skills"), source: "codex" },
    { path: join(HOME, ".codex", "plugins", "cache", "openai-bundled"), source: "plugin" },
    { path: join(HOME, ".codex", "plugins", "cache", "openai-primary-runtime"), source: "plugin" },
  ];
}

function configuredRoots() {
  const value = process.env.SKILLS_SCAN_ROOTS?.trim();
  if (!value) return defaultRoots();
  return value
    .split(":")
    .map((path) => path.trim())
    .filter(Boolean)
    .map((path) => ({ path: resolve(path), source: "configured" }));
}

function walkSkillFiles(root) {
  if (!existsSync(root.path)) return [];
  const files = [];
  const seenDirectories = new Set();

  function walk(directory) {
    let realDirectory;
    try {
      realDirectory = realpathSync(directory);
      if (seenDirectories.has(realDirectory)) return;
      seenDirectories.add(realDirectory);
    } catch {
      return;
    }

    let entries;
    try {
      entries = readdirSync(directory, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of entries) {
      if (entry.name === "SKILL.md") {
        files.push({ path: join(directory, entry.name), source: root.source });
        continue;
      }
      if (IGNORED_DIRECTORIES.has(entry.name)) continue;
      // The runtime directories contain convenience symlinks back to the
      // personal repo and version aliases such as plugin "latest" pointers.
      // The canonical targets are scanned separately, so following those
      // links would inflate copy counts and include inactive cache aliases.
      if (!entry.isDirectory()) continue;

      const child = join(directory, entry.name);
      try {
        if (statSync(child).isDirectory()) walk(child);
      } catch {
        // Broken or inaccessible links are irrelevant to the public inventory.
      }
    }
  }

  walk(root.path);
  return files;
}

function readSkill(file) {
  try {
    const raw = readFileSync(file.path, "utf8");
    const { data } = matter(raw);
    const name = String(data.name || dirname(file.path).split("/").at(-1) || "").trim();
    if (!name) return null;
    return {
      key: normalize(name),
      name,
      description: publicDescription(data.description),
      source: file.source,
    };
  } catch (error) {
    console.warn(`Skipping unreadable skill metadata: ${file.path} (${error.message})`);
    return null;
  }
}

function publicDescription(value = "") {
  const text = String(value).replace(/\s+/g, " ").trim();
  const sentence = text.match(/^.*?(?:[.!?。！？](?=\s|$)|$)/)?.[0] || text;
  if (sentence.length <= 280) return sentence;
  const shortened = sentence.slice(0, 277);
  const boundary = shortened.lastIndexOf(" ");
  return `${shortened.slice(0, boundary > 180 ? boundary : 277).trim()}...`;
}

function collect() {
  const byName = new Map();
  for (const root of configuredRoots()) {
    for (const file of walkSkillFiles(root)) {
      const skill = readSkill(file);
      if (!skill) continue;
      const existing = byName.get(skill.key) || {
        name: skill.name,
        description: "",
        sources: new Set(),
        copies: 0,
      };
      existing.copies += 1;
      existing.sources.add(skill.source);
      if (skill.description.length > existing.description.length) {
        existing.description = skill.description;
      }
      byName.set(skill.key, existing);
    }
  }

  return [...byName.values()]
    .map((skill) => ({
      name: skill.name,
      description: skill.description,
      sources: [...skill.sources].sort(),
      copies: skill.copies,
    }))
    .sort((a, b) => a.name.localeCompare(b.name, "en", { sensitivity: "base" }));
}

function comparable(snapshot) {
  return JSON.stringify({
    schemaVersion: snapshot.schemaVersion,
    skills: snapshot.skills,
  });
}

function writeSnapshot() {
  const skills = collect();
  const next = {
    schemaVersion: 1,
    updatedAt: new Date().toISOString(),
    skills,
  };

  if (existsSync(OUTPUT)) {
    try {
      const current = JSON.parse(readFileSync(OUTPUT, "utf8"));
      if (comparable(current) === comparable(next)) {
        console.log(`Installed-skill snapshot already current (${skills.length} unique skills).`);
        return;
      }
    } catch {
      // Replace malformed snapshots with a verified one.
    }
  }

  writeFileSync(OUTPUT, `${JSON.stringify(next, null, 2)}\n`);
  console.log(`Updated ${relative(REPO, OUTPUT)} with ${skills.length} unique skills.`);
}

writeSnapshot();
