#!/usr/bin/env python3
from src.tractionbuild.core.settings import get_settings
s = get_settings()
# Never print secret values:
print("✅ Settings loaded. Required keys present. ENV=", s.ENV)