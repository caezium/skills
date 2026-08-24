import assert from "node:assert/strict";
import test from "node:test";
import { CATEGORIES, PIPELINE, categorizeSkill } from "./map.config.mjs";

test("uses the curated category for known skills", () => {
  assert.deepEqual(categorizeSkill({ name: "to-spec" }), {
    id: "product",
    method: "curated",
  });
});

test("routes new Lark skills by prefix", () => {
  assert.deepEqual(categorizeSkill({ name: "lark-new-resource" }), {
    id: "lark",
    method: "prefix",
  });
});

test("routes an unknown skill from its description", () => {
  assert.deepEqual(categorizeSkill({
    name: "release-helper",
    description: "Deploy releases through GitHub Actions CI/CD.",
  }), {
    id: "delivery",
    method: "keywords",
  });
});

test("keeps ambiguous new skills visible for review", () => {
  assert.deepEqual(categorizeSkill({
    name: "unfamiliar-helper",
    description: "Performs a highly specific operation.",
  }), {
    id: "review",
    method: "unclassified",
  });
});

test("does not recommend retired skills", () => {
  const retired = new Set([
    "design-an-interface",
    "pinia-best-practices",
    "prd-to-issues",
    "prd-to-plan",
    "qa",
    "request-refactor-plan",
    "triage-issue",
    "ui-skills",
    "vueuse-best-practices",
    "write-a-prd",
    "writing-great-skills",
  ]);
  const recommended = [
    ...CATEGORIES.flatMap((category) => category.names),
    ...PIPELINE.flatMap((stage) => stage.skills),
  ];
  assert.deepEqual(recommended.filter((name) => retired.has(name)), []);
});
