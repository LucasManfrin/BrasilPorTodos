import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const required = [
  "README.md",
  "AGENTS.md",
  "CONTRIBUTING.md",
  "SECURITY.md",
  "CHANGELOG.md",
  "LICENSE",
  "docs/README.md",
  "docs/project/STATUS.md",
  "docs/project/STATUS_HISTORY.md",
  "docs/project/REPOSITORY_AUDIT.md",
  "docs/governance/PUBLICATION.md",
  ".agents/README.md",
  "docs/product/VISION.md",
  "docs/product/V1_SCOPE.md",
  "docs/product/ROADMAP.md",
  "docs/architecture/ARCHITECTURE.md",
  "docs/architecture/DECISIONS.md",
  "docs/data/METHODOLOGY.md",
  "docs/data/CONTEXT_EVIDENCE.md",
  "docs/data/GRAPH_CONTRACT.md",
  "docs/data/FIRST_CONTEXT_RESEARCH.md",
  "docs/data/DATA_SOURCES.md",
  "docs/governance/LICENSING.md",
  "docs/architecture/DATA_MODEL.md",
  "docs/architecture/AUTHENTICATION.md",
  "docs/project/BACKLOG.md",
  "docs/development/DEVELOPMENT.md",
  "docs/development/DOCKER_LOCAL.md",
  "docs/development/E2E.md",
  "docs/development/VERIFICATION.md",
  "docs/design/DESIGN.md",
  "docs/design/DATA_EXPLORER.md",
  "docs/data/INDICATORS.md",
  "docs/data/FISCAL_BASELINE.md",
  "docs/data/FISCAL_COMPOSITION.md",
  "docs/data/FISCAL_INTEREST.md",
  "docs/data/FEDERAL_SPENDING_RESEARCH.md",
  "docs/data/FISCAL_SPENDING.md",
  "docs/data/GENERAL_GOVERNMENT.md",
  "docs/data/SICONFI_RESEARCH.md",
  "docs/data/PUBLIC_SECTOR_RESEARCH.md",
  "docs/data/FISCAL_COMPATIBILITY.md",
  "docs/data/FISCAL_SCENARIOS.md",
  "docs/product/PROPOSAL_CREATION.md",
  "docs/data/EMPLOYMENT_INDICATORS.md",
  "docs/data/RESEARCH_BRIEF.md",
  "docs/product/GRAPH_EXPLORER.md",
  "docs/governance/CONTENT_POLICY_DRAFT.md",
  ".agents/COORDINATOR.md",
  ".agents/FISCAL.md",
  ".agents/FRONTEND.md",
  ".agents/BACKEND.md",
  ".agents/QA.md",
  ".agents/DOCS.md",
  "backend/AGENTS.md",
  "frontend/AGENTS.md",
  "backend/app/integrations/AGENTS.md",
  "docs/AGENTS.md"
];
const errors = required.filter((path) => !existsSync(join(root, path))).map((path) => `Missing: ${path}`);
function checkDirectory(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if ([".local", "node_modules", ".git", ".next", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__"].includes(entry.name)) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) checkDirectory(path);
    else if (entry.name.endsWith(".md")) {
      const content = readFileSync(path, "utf8");
      for (const match of content.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
        const target = match[1].split("#")[0];
        if (!target || /^[a-z]+:/i.test(target) || target.startsWith("//")) continue;
        if (!existsSync(resolve(dirname(path), decodeURIComponent(target)))) errors.push(`${path}: broken link ${target}`);
      }
    }
  }
}
checkDirectory(root);
if (errors.length) { console.error(errors.join("\n")); process.exitCode = 1; }
else console.log("Required documents and local Markdown links verified.");
