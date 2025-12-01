import json, subprocess, sys, pathlib

OUT = pathlib.Path(__file__).resolve().parents[1] / "out"
OUT.mkdir(parents=True, exist_ok=True)

def run(cmd, out_file):
    """Run a command and save output to a file"""
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=OUT.parents[1])
    output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nEXIT CODE: {result.returncode}"
    (OUT / out_file).write_text(output, encoding='utf-8')
    return result.returncode

print("\n=== PYTHON DIAGNOSTICS STARTING ===\n")

exit_code = 0

# 1. Check code style and common bugs
exit_code |= run(["ruff", "check", "--output-format", "full", "."], "python_ruff.txt")

# 2. Check types
exit_code |= run(["mypy", "--pretty", "--show-error-codes", "."], "python_mypy.txt")

# 3. Run tests
exit_code |= run(["pytest", "-v", "--tb=short"], "python_pytest.txt")

# 4. Measure test coverage
run(["coverage", "run", "-m", "pytest", "-q"], "python_coverage_raw.txt")
run(["coverage", "report", "-m"], "python_coverage.txt")

# 5. Security scan
exit_code |= run(["bandit", "-r", ".", "-f", "txt"], "python_bandit.txt")

# 6. Check for vulnerable packages
exit_code |= run(["pip-audit", "-r", "requirements.txt"], "python_pip_audit.txt")

# Save summary
with open(OUT / "python_summary.json", "w") as f:
    json.dump({"overall_exit_code": exit_code}, f, indent=2)

print(f"\n=== DIAGNOSTICS COMPLETE (exit code: {exit_code}) ===")
print(f"Results saved to: {OUT.resolve()}")
sys.exit(0)  # Always exit 0 so the pipeline continues