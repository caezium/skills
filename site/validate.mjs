import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { CATEGORIES, PIPELINE, normalize } from "./map.config.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = join(__dirname, "dist");
const requiredFiles = [
  join(DIST, "index.html"),
  join(DIST, "map", "index.html"),
  join(DIST, "skills.json"),
  join(DIST, "style.css"),
  join(DIST, "404.html"),
];

for (const file of requiredFiles) {
  assert.ok(existsSync(file), `Missing generated file: ${file}`);
}

const inventory = JSON.parse(readFileSync(join(DIST, "skills.json"), "utf8"));
assert.equal(inventory.count, inventory.skills.length, "Inventory count does not match its skill array");
assert.ok(inventory.count > 0, "Inventory is empty");

const names = inventory.skills.map((skill) => normalize(skill.name));
assert.equal(new Set(names).size, names.length, "Inventory contains duplicate public skill names");

const categoryIds = new Set([...CATEGORIES.map((category) => category.id), "review"]);
for (const skill of inventory.skills) {
  assert.ok(skill.name, "Every inventory item needs a public name");
  assert.ok(categoryIds.has(skill.category), `Unknown category '${skill.category}' for ${skill.name}`);
}

const installed = new Set(names);
for (const stage of PIPELINE) {
  assert.ok(stage.title && stage.description && stage.gate, `Pipeline stage '${stage.id}' is incomplete`);
  for (const skill of stage.skills) {
    assert.ok(installed.has(normalize(skill)), `Pipeline references missing skill '${skill}'`);
  }
}

const map = readFileSync(join(DIST, "map", "index.html"), "utf8");
assert.match(map, /id="map-q"/, "Map page is missing inventory search");
for (const stage of PIPELINE) {
  assert.ok(map.includes(`id="${stage.id}"`), `Map page is missing stage '${stage.id}'`);
}

const reviewCount = inventory.skills.filter((skill) => skill.category === "review").length;
if (reviewCount) {
  console.warn(`${reviewCount} skills need category review; they remain visible on the generated page.`);
}

console.log(`Validated ${inventory.count} unique installed skills across ${CATEGORIES.length} use-case groups.`);
