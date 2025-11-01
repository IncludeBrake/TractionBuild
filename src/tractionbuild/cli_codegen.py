import argparse
from src.tractionbuild.database.project_registry import ProjectRegistry
from src.tractionbuild.tools.code_tools import CodeGenerator, CodeSpec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--app-name", required=True)
    ap.add_argument("--profile", default="elite")
    args = ap.parse_args()

    r = ProjectRegistry()
    gen = CodeGenerator(r)
    with r.transaction(args.project_id) as tx:
        out = gen.generate_service(CodeSpec(
            project_id=args.project_id, app_name=args.app_name, profile=args.profile
        ), tx)
        print({"ok": True, "written": out["written"], "profile": out["profile"]})

if __name__ == "__main__":
    main()
