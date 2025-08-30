# ZeroToShip Glue Patch

This patch adds **minimal, production-lean glue** so you can run a complete
Validator → Advisory → COMPLETED flow behind a **clean FastAPI** entrypoint.

## What’s included
- `src/zerotoship/core/agent_registry.py` — registry that returns adapter-wrapped crews
- `src/zerotoship/core/workflow_engine.py` — fixed imports + lean engine
- `src/zerotoship/crews/adapters.py` — proper imports + schema enforcement
- `src/zerotoship/api/app_v1.py` — minimal FastAPI app with 3 routes
- `tests/test_e2e_min.py` — sanity E2E for the slice
- `Makefile.patch` — run/test helpers

> NOTE: This patch **does not** remove or rewrite any existing modules.

## Apply the patch
Unzip the contents of `zerotoship_glue_patch.zip` into your repo root so files land under `src/zerotoship/...`.

## Install (if needed)
Ensure these packages exist in your env (most are already present):
```
pip install fastapi uvicorn prometheus-client pytest
```

## Run
```
make -f Makefile.patch run
```
Then:
```
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/v1/projects -H "Content-Type: application/json" -d '{
  "name":"demo","description":"desc","hypothesis":"X for Y","target_avatars":["startup_entrepreneur"],"workflow":"validation_and_launch"
}'
```

## Test (minimal E2E)
```
make -f Makefile.patch test
```

## Next steps (after green)
- Wire Neo4j persistence by calling your `ProjectRegistry` inside the background `runner()` in `app_v1.py`.
- Swap `app_v1.py` into Dockerfile/compose or point uvicorn there.
- Expand the engine `order` to include `execution`, `builder`, etc., once Validator+Advisory are solid.
