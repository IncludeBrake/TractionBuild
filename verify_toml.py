import tomllib
import sys

try:
    with open('C:/Users/jthri/Dev/MySauce/TractionBuild/pyproject.toml', 'rb') as f:
        config = tomllib.load(f)
    
    # Check structure
    assert 'tool' in config
    assert 'ruff' in config['tool']
    assert 'line-length' in config['tool']['ruff']
    assert 'lint' in config['tool']['ruff']
    assert 'select' in config['tool']['ruff']['lint']
    
    print("✅ pyproject.toml is valid!")
    print(f"✅ Ruff line-length: {config['tool']['ruff']['line-length']}")
    print(f"✅ Ruff lint rules: {config['tool']['ruff']['lint']['select']}")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
