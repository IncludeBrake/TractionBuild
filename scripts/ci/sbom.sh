#!/bin/bash
set -e
mkdir -p sbom
cyclonedx-py requirements requirements.lock > sbom/cyclonedx.json
echo "SBOM generated: sbom/cyclonedx.json"
