export const CATEGORIES = [
  {
    id: "product",
    label: "Product discovery, decisions, and planning",
    names: [
      "playbook",
      "grill-me",
      "grilling",
      "grill-with-docs",
      "llm-council",
      "domain-modeling",
      "decision-extractor",
      "design-an-interface",
      "write-a-prd",
      "to-spec",
      "prd-to-plan",
      "prd-to-issues",
      "to-tickets",
      "request-refactor-plan",
      "triage",
      "triage-issue",
      "qa",
      "linear",
      "throughline",
      "recap",
      "handoff",
      "setup-matt-pocock-skills",
    ],
    keywords: ["decision", "prd", "spec", "ticket", "triage", "roadmap", "planning", "product", "requirements"],
  },
  {
    id: "engineering",
    label: "Implementation, testing, and review",
    names: [
      "implement",
      "tdd",
      "code-review",
      "improve-codebase-architecture",
      "prune",
      "web-perf",
      "vue-best-practices",
      "pinia-best-practices",
      "vueuse-best-practices",
      "find-docs",
      "openai-docs",
      "full-output-enforcement",
      "create-rule",
      "git-guardrails-claude-code",
      "update-cursor-settings",
      "shell",
      "scaffold-exercises",
    ],
    keywords: ["implement", "test", "review", "refactor", "architecture", "performance", "typescript", "debug", "code"],
  },
  {
    id: "delivery",
    label: "Pull requests, CI, and deployment",
    names: [
      "create-pr",
      "yeet",
      "buildspace-ci-cd",
      "sites-building",
      "sites-hosting",
      "macrocosm-ci",
      "macrocosm-launch",
      "dayflow-sync",
      "stats-sync",
    ],
    keywords: ["deploy", "release", "github actions", "ci/cd", "pull request", "publish", "sync upstream"],
  },
  {
    id: "interface",
    label: "Interface and product design",
    names: [
      "awesome-design-md",
      "design-taste-frontend",
      "design-taste-frontend-v1",
      "gpt-taste",
      "high-end-visual-design",
      "industrial-brutalist-ui",
      "minimalist-ui",
      "make-interfaces-feel-better",
      "redesign-existing-projects",
      "stitch-design-taste",
      "superdesign",
      "ui-skills",
      "figma",
      "clone-site",
      "image-to-code",
      "imagegen-frontend-mobile",
      "imagegen-frontend-web",
      "app-screenshots",
    ],
    keywords: ["frontend", "interface", "ui", "ux", "design system", "website", "landing page", "figma"],
  },
  {
    id: "images",
    label: "Images, illustration, and brand assets",
    names: [
      "imagegen",
      "brandkit",
      "art-skill-maker",
      "chiken-emote-illustrations",
      "henry-avatar-illustrations",
      "nib",
    ],
    keywords: ["image", "illustration", "art", "avatar", "brand", "visual asset"],
  },
  {
    id: "research",
    label: "Research, browsers, and visual explanation",
    names: [
      "last30days",
      "digest",
      "alphaxiv-paper-lookup",
      "defuddle",
      "control-in-app-browser",
      "playwright",
      "atlas",
      "screenshot",
      "visualize",
    ],
    keywords: ["research", "browser", "web page", "screenshot", "paper", "visualization", "digest"],
  },
  {
    id: "artifacts",
    label: "Documents, data, and canvases",
    names: [
      "documents",
      "pdf",
      "Presentations",
      "Spreadsheets",
      "excel-live-control",
      "template-creator",
      "jupyter-notebook",
      "json-canvas",
      "tldraw-offline",
    ],
    keywords: ["document", "pdf", "spreadsheet", "presentation", "notebook", "canvas", "excel"],
  },
  {
    id: "knowledge",
    label: "Knowledge and personal workflows",
    names: [
      "obsidian-vault",
      "obsidian-cli",
      "obsidian-markdown",
      "obsidian-bases",
      "obsidian-convert",
      "vault-resync",
      "chatlog",
      "dayflow-pull",
      "1-1-prep",
      "daily-roundup",
      "week-prep",
      "monday",
      "friday",
    ],
    keywords: ["obsidian", "vault", "briefing", "weekly", "meeting", "notes", "wechat"],
  },
  {
    id: "lark",
    label: "Lark and Feishu collaboration",
    names: [
      "lark-shared",
      "lark-contact",
      "lark-calendar",
      "lark-task",
      "lark-im",
      "lark-mail",
      "lark-doc",
      "lark-markdown",
      "lark-drive",
      "lark-wiki",
      "lark-sheets",
      "lark-base",
      "lark-slides",
      "lark-whiteboard",
      "lark-minutes",
      "lark-vc",
      "lark-vc-agent",
      "lark-event",
      "lark-approval",
      "lark-attendance",
      "lark-okr",
      "lark-apps",
      "lark-openapi-explorer",
      "lark-skill-maker",
      "lark-workflow-meeting-summary",
      "lark-workflow-standup-report",
    ],
    prefixes: ["lark-"],
    keywords: ["lark", "feishu", "飞书"],
  },
  {
    id: "platform",
    label: "Cloudflare, agents, and messaging",
    names: [
      "cloudflare",
      "agents-sdk",
      "durable-objects",
      "workers-best-practices",
      "wrangler",
      "cloudflare-email-service",
      "sandbox-sdk",
      "imessage",
      "chat-adapter-imessage",
      "spectrum",
      "photon-cli",
      "macrocosm-dev",
      "macrocosm-handbook",
    ],
    keywords: ["cloudflare", "worker", "agent", "imessage", "photon", "sandbox", "messaging"],
  },
  {
    id: "meta",
    label: "Skill, plugin, and agent systems",
    names: [
      "skill-creator",
      "create-skill",
      "writing-great-skills",
      "install-skill",
      "skill-installer",
      "find-skills",
      "migrate-to-skills",
      "plugin-creator",
      "create-subagent",
      "vista-dashboard",
    ],
    keywords: ["skill", "plugin", "subagent", "agent status", "codex"],
  },
  {
    id: "specialized",
    label: "Mac and specialized operations",
    names: ["burrow-system-tools"],
    keywords: ["macos", "mac ", "system health", "process", "disk"],
  },
];

export const PIPELINE = [
  {
    id: "evidence",
    title: "Collect evidence",
    description: "Separate observed user and system facts from assumptions before discussing a solution.",
    gate: "Problem gate: confirm the user, problem, baseline, and success measure.",
    skills: ["last30days", "find-docs", "qa", "chatlog", "digest", "alphaxiv-paper-lookup", "defuddle"],
  },
  {
    id: "challenge",
    title: "Challenge the idea",
    description: "Walk the decision tree, test edge cases, and make terminology and tradeoffs explicit.",
    gate: "Continue only when unresolved branches and contradictory assumptions are visible.",
    skills: ["grill-with-docs", "grilling", "grill-me", "domain-modeling", "llm-council"],
  },
  {
    id: "decision",
    title: "Make the investment decision",
    description: "Choose to proceed, prototype, defer, or reject, with confidence and kill criteria recorded.",
    gate: "Decision gate: the human owns this call and the accepted debt budget.",
    skills: ["llm-council", "decision-extractor"],
    gap: "Missing owner: idea-gate",
  },
  {
    id: "prototype",
    title: "Prototype the expensive unknown",
    description: "Test the riskiest interaction, interface, data behavior, or feasibility assumption before hardening.",
    gate: "User feedback: show the smallest realistic prototype to target users.",
    skills: ["design-an-interface", "figma", "superdesign", "jupyter-notebook", "imagegen-frontend-web", "imagegen-frontend-mobile"],
  },
  {
    id: "specify",
    title: "Freeze the behavior boundary",
    description: "Capture success, acceptance behavior, testing seams, constraints, and explicit out-of-scope work.",
    gate: "Spec gate: approve behavior and scope before creating implementation tickets.",
    skills: ["to-spec", "write-a-prd", "domain-modeling", "throughline"],
  },
  {
    id: "slice",
    title: "Cut vertical slices",
    description: "Create narrow, end-to-end tickets that are independently demoable and fit one fresh context.",
    gate: "Approve granularity, blockers, and every human-review checkpoint.",
    skills: ["to-tickets", "prd-to-plan", "prd-to-issues"],
  },
  {
    id: "build",
    title: "Build one slice",
    description: "Implement through public behavior, keep the change minimal, and verify continuously.",
    gate: "Do not start the next slice until the current one is green and reviewable.",
    skills: ["implement", "tdd", "find-docs", "workers-best-practices", "vue-best-practices"],
  },
  {
    id: "validate",
    title: "Validate the direction",
    description: "Review standards and spec fidelity, then hand-test the first complete path before multiplying it.",
    gate: "Slice gate: a human verifies the first end-to-end behavior and adjacent regressions.",
    skills: ["code-review", "recap", "web-perf", "qa"],
  },
  {
    id: "ready",
    title: "Prove production readiness",
    description: "Check security, migrations, failures, observability, cost, rollout, rollback, and operational ownership.",
    gate: "Release gate: accept remaining risks with named owners and rollback triggers.",
    skills: ["code-review", "workers-best-practices", "web-perf", "buildspace-ci-cd"],
    gap: "Missing owner: production-readiness-review",
  },
  {
    id: "release",
    title: "Release and learn",
    description: "Ship through a staged rollout, capture real feedback, and preserve decisions and final state.",
    gate: "Reopen the decision if results cross a kill criterion or invalidate the problem framing.",
    skills: ["create-pr", "yeet", "sites-hosting", "wrangler", "triage", "decision-extractor", "recap"],
  },
];

const exactCategory = new Map();
for (const category of CATEGORIES) {
  for (const name of category.names) exactCategory.set(normalize(name), category.id);
}

export function normalize(value = "") {
  return String(value).trim().toLowerCase();
}

export function categorizeSkill(skill) {
  const name = normalize(skill.name || skill.slug);
  const exact = exactCategory.get(name);
  if (exact) return { id: exact, method: "curated" };

  for (const category of CATEGORIES) {
    if (category.prefixes?.some((prefix) => name.startsWith(prefix))) {
      return { id: category.id, method: "prefix" };
    }
  }

  const haystack = `${name} ${normalize(skill.description)}`;
  let best = null;
  for (const category of CATEGORIES) {
    const score = (category.keywords || []).reduce(
      (total, keyword) => total + (keywordMatches(haystack, keyword) ? 1 : 0),
      0,
    );
    if (!best || score > best.score) best = { id: category.id, score };
  }

  return best?.score > 0
    ? { id: best.id, method: "keywords" }
    : { id: "review", method: "unclassified" };
}

function keywordMatches(haystack, value) {
  const keyword = normalize(value);
  if (!keyword) return false;
  if (/[^\x00-\x7F]/.test(keyword)) return haystack.includes(keyword);
  const escaped = keyword
    .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    .replace(/\s+/g, "\\s+");
  return new RegExp(`(^|[^a-z0-9])${escaped}([^a-z0-9]|$)`, "i").test(haystack);
}

export function categoryLabel(id) {
  return CATEGORIES.find((category) => category.id === id)?.label || "Needs review";
}
