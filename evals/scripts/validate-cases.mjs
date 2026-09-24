#!/usr/bin/env node

import { readFile, readdir, stat } from "node:fs/promises";
import { dirname, extname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const evalRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = resolve(evalRoot, "..");
const skillsRoot = resolve(repoRoot, "skills");
const expectedProfiles = [
  "fast/economical",
  "balanced/default",
  "highest-reasoning",
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function nonEmpty(value) {
  return typeof value === "string" && value.trim().length > 0;
}

async function readJson(path) {
  try {
    return JSON.parse(await readFile(path, "utf8"));
  } catch (error) {
    throw new Error(`${path}: ${error.message}`);
  }
}

async function exists(path) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

async function markdownFiles(root) {
  const files = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
    const path = resolve(root, entry.name);
    if (entry.isDirectory()) files.push(...await markdownFiles(path));
    else if (entry.isFile() && extname(entry.name).toLowerCase() === ".md") files.push(path);
  }
  return files;
}

async function validateLinks(skillDir) {
  const linkPattern = /\[[^\]]*\]\(([^)]+)\)/g;
  for (const path of await markdownFiles(skillDir)) {
    const content = await readFile(path, "utf8");
    for (const match of content.matchAll(linkPattern)) {
      let target = match[1].trim();
      if (
        target.startsWith("#") ||
        target.startsWith("mailto:") ||
        target.startsWith("data:") ||
        /^[a-z][a-z0-9+.-]*:\/\//i.test(target)
      ) continue;
      if (target.startsWith("<") && target.endsWith(">")) target = target.slice(1, -1);
      target = target.split("#", 1)[0].split("?", 1)[0];
      if (!target) continue;
      const resolved = resolve(dirname(path), decodeURIComponent(target));
      assert(await exists(resolved), `${path}: broken local link ${match[1]}`);
    }
  }
}

function validateProfiles(actual, label) {
  assert(Array.isArray(actual), `${label}: requiredProfiles must be an array`);
  assert(
    JSON.stringify(actual) === JSON.stringify(expectedProfiles),
    `${label}: requiredProfiles must be ${expectedProfiles.join(", ")}`,
  );
}

async function main() {
  const profiles = await readJson(resolve(evalRoot, "profiles.example.json"));
  await readJson(resolve(evalRoot, "run-record.schema.json"));

  assert(profiles.schema === 1, "profiles.example.json: schema must be 1");
  assert(profiles.profiles && typeof profiles.profiles === "object", "profiles.example.json: profiles must be an object");
  for (const profile of expectedProfiles) {
    const entry = profiles.profiles[profile];
    assert(entry && typeof entry === "object", `profiles.example.json: missing ${profile}`);
    assert(nonEmpty(entry.selectionRule), `profiles.example.json: ${profile} has no selectionRule`);
    assert(nonEmpty(entry.model), `profiles.example.json: ${profile} has no model mapping`);
    assert(nonEmpty(entry.thinking), `profiles.example.json: ${profile} has no thinking mapping`);
  }

  const skillNames = [];
  for (const entry of await readdir(skillsRoot, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith(".")) continue;
    const skillDir = resolve(skillsRoot, entry.name);
    const skillFile = resolve(skillDir, "SKILL.md");
    if (!(await exists(skillFile))) continue;
    const content = await readFile(skillFile, "utf8");
    const frontmatter = content.match(/^---\n([\s\S]*?)\n---\n/);
    assert(frontmatter, `${skillFile}: missing YAML frontmatter`);
    const name = frontmatter[1].match(/^name:\s*([^\n]+)$/m)?.[1]?.trim();
    assert(nonEmpty(name), `${skillFile}: missing name`);
    assert(name === entry.name, `${skillFile}: name ${name} does not match directory ${entry.name}`);
    skillNames.push(name);
    await validateLinks(skillDir);
  }
  skillNames.sort();

  const caseIds = new Set();
  let caseCount = 0;
  for (const skill of skillNames) {
    const path = resolve(skillsRoot, skill, "evals", "evals.json");
    assert(await exists(path), `${skill}: missing evals/evals.json`);
    const definitions = await readJson(path);
    assert(definitions.schema === 1, `${skill}: schema must be 1`);
    assert(definitions.skill === skill, `${skill}: eval skill field must match package name`);
    validateProfiles(definitions.requiredProfiles, skill);
    assert(Array.isArray(definitions.cases) && definitions.cases.length >= 3, `${skill}: at least three cases are required`);

    for (const testCase of definitions.cases) {
      const label = `${skill}/${testCase.id || "<missing-id>"}`;
      assert(nonEmpty(testCase.id), `${skill}: case id is required`);
      assert(testCase.id.startsWith(`${skill}-`), `${label}: id must start with the skill name`);
      assert(!caseIds.has(testCase.id), `${label}: duplicate case id`);
      caseIds.add(testCase.id);
      for (const field of ["summary", "setup", "prompt"]) {
        assert(nonEmpty(testCase[field]), `${label}: ${field} must be non-empty`);
      }
      assert(
        Array.isArray(testCase.expectedBehavior) && testCase.expectedBehavior.length >= 2,
        `${label}: at least two expected behaviors are required`,
      );
      assert(
        Array.isArray(testCase.forbiddenBehavior) && testCase.forbiddenBehavior.length >= 2,
        `${label}: at least two forbidden behaviors are required`,
      );
      for (const [field, values] of [
        ["expectedBehavior", testCase.expectedBehavior],
        ["forbiddenBehavior", testCase.forbiddenBehavior],
      ]) {
        assert(values.every(nonEmpty), `${label}: ${field} entries must be non-empty strings`);
      }
      caseCount += 1;
    }
  }

  for (const entry of await readdir(skillsRoot, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const evalPath = resolve(skillsRoot, entry.name, "evals", "evals.json");
    if (await exists(evalPath)) {
      assert(skillNames.includes(entry.name), `${evalPath}: eval suite has no matching skill package`);
    }
  }

  console.log(
    `VALID: ${skillNames.length} skills, ${caseCount} cases, ${caseCount * expectedProfiles.length} minimum fresh profile runs`,
  );
}

main().catch((error) => {
  console.error(`EVALUATION DEFINITION ERROR: ${error.message}`);
  process.exitCode = 1;
});
