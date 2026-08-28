#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import process from "node:process";
import { parseDocument } from "yaml";

function usage() {
  console.log("Usage: node scripts/validate-yaml.mjs <file> [--max-lines <positive-integer>]");
}

function parseArgs(args) {
  if (args.includes("--help") || args.includes("-h")) {
    usage();
    process.exit(0);
  }

  if (args.length === 0) {
    throw new Error("missing YAML file path");
  }

  const file = args[0];
  let maxLines;

  for (let index = 1; index < args.length; index += 1) {
    const argument = args[index];
    if (argument !== "--max-lines") {
      throw new Error(`unknown argument: ${argument}`);
    }

    const value = args[index + 1];
    if (!value || !/^\d+$/.test(value) || Number(value) < 1) {
      throw new Error("--max-lines requires a positive integer");
    }
    maxLines = Number(value);
    index += 1;
  }

  return { file, maxLines };
}

async function main() {
  const { file, maxLines } = parseArgs(process.argv.slice(2));
  const source = await readFile(file, "utf8");
  const document = parseDocument(source, {
    prettyErrors: true,
    strict: true,
    uniqueKeys: true,
  });

  if (document.errors.length > 0) {
    for (const error of document.errors) {
      console.error(`YAML ERROR: ${error.message}`);
    }
    process.exitCode = 1;
    return;
  }

  const lineCount = source.length === 0 ? 0 : source.split(/\r?\n/).length - (source.endsWith("\n") ? 1 : 0);
  if (maxLines !== undefined && lineCount > maxLines) {
    console.error(`LINE LIMIT ERROR: ${lineCount} lines exceeds max-lines ${maxLines}`);
    process.exitCode = 1;
    return;
  }

  const limit = maxLines === undefined ? "no max-lines supplied" : `max-lines ${maxLines}`;
  console.log(`VALID: ${file} (${lineCount} lines; ${limit})`);
}

main().catch((error) => {
  console.error(`VALIDATION ERROR: ${error.message}`);
  process.exitCode = 1;
});
