#!/bin/bash
set -e
pip install --dry-run -r requirements.lock
echo "Dependency migration validated"
