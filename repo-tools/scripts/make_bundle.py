import pathlib
import tarfile
import json

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "repo-tools" / "out"
BUNDLE = ROOT / "repo-tools" / "repo_doctor_bundle"
BUNDLE.mkdir(exist_ok=True)

# File types we want to include
KEEP_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".toml", ".yaml", ".yml", 
                   ".md", ".txt", ".ini", ".cfg", ".sh", ".ps1", ".env.example"}
KEEP_NAMES = {"Dockerfile", "requirements.txt", "package.json", "pyproject.toml", 
              ".python-version", "README.md"}

# Load ignore patterns
ignore_file = ROOT / "repo-tools" / "config" / "ignore_globs.txt"
ignore_patterns = []
if ignore_file.exists():
    ignore_patterns = [line.strip() for line in ignore_file.read_text().splitlines() 
                      if line.strip() and not line.startswith("#")]

def should_ignore(path_str):
    """Check if path matches any ignore pattern"""
    for pattern in ignore_patterns:
        pattern_clean = pattern.rstrip("/**")
        if pattern_clean in path_str.replace("\\", "/"):
            return True
    return False

def should_keep(filepath):
    """Decide if we should include this file"""
    path_str = str(filepath.relative_to(ROOT)).replace("\\", "/")
    
    if should_ignore(path_str):
        return False
    
    return filepath.suffix in KEEP_EXTENSIONS or filepath.name in KEEP_NAMES

print("Scanning repository...")
files = [p for p in ROOT.rglob("*") 
         if p.is_file() 
         and "repo-tools" not in str(p.relative_to(ROOT))
         and should_keep(p)]

print(f"Found {len(files)} source files to include")

# Collect artifacts
artifacts = list(OUT.glob("*")) if OUT.exists() else []
print(f"Found {len(artifacts)} diagnostic artifacts")

# Create manifest
manifest = {
    "files": [str(p.relative_to(ROOT)) for p in files],
    "artifacts": [str(p.relative_to(OUT)) for p in artifacts]
}
(BUNDLE / "manifest.json").write_text(json.dumps(manifest, indent=2))

# Create tarball
print("Creating bundle...")
with tarfile.open(BUNDLE / "repo_doctor.tar.gz", "w:gz") as tar:
    for p in files:
        tar.add(p, arcname=str(p.relative_to(ROOT)))
    for a in artifacts:
        tar.add(a, arcname=f"artifacts/{a.name}")

# Create README
(BUNDLE / "READ_ME_FIRST.md").write_text("""# Repo Doctor Bundle

This archive contains:
- Curated source files (no deps, no binaries)
- artifacts/: all diagnostic outputs (tests, linters, security scans)
- manifest.json: index of everything included

## How to use
Upload this bundle to your AI assistant with the prompt in PROMPT_repo_doctor.md
""")

# Create AI prompt
(BUNDLE / "PROMPT_repo_doctor.md").write_text("""You are a senior software engineer performing a code health audit.

**Your inputs:**
- Source files (Python, JS, config)
- artifacts/: test results, linter output, security scans, coverage reports

**Your task:**
1. Read all artifact files to understand what's failing
2. Identify root causes (not symptoms)
3. Create a prioritized fix plan (P0 = blocks everything, P1 = high impact, P2 = polish)
4. For each fix, provide:
   - Exact file path
   - Unified diff patch
   - Why this fixes the root cause
5. If you need more info, list the exact command to run

**Output format:**