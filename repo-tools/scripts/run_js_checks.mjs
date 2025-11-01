import { execSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, "..", "out");
mkdirSync(OUT, { recursive: true });

function run(cmd, file) {
  console.log("Running:", cmd);
  try {
    const output = execSync(cmd, { encoding: "utf8", cwd: resolve(__dirname, "..", "..") });
    writeFileSync(join(OUT, file), output);
  } catch (e) {
    const output = (e.stdout || "") + "\n" + (e.stderr || "");
    writeFileSync(join(OUT, file), output);
  }
}

console.log("\n=== JAVASCRIPT DIAGNOSTICS STARTING ===\n");

run("npm run lint", "js_eslint.txt");
run("npm run typecheck", "js_tsc.txt");
run("npm audit --json", "js_npm_audit.json");

console.log("\n=== JS DIAGNOSTICS COMPLETE ===");