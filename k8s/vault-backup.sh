#!/bin/bash
# Vault Backup Script for ZeroToShip
# Run this script regularly for disaster recovery

BACKUP_DIR="/tmp/vault-backups"
DATE=\
BACKUP_FILE="\/vault-backup-\.json"

mkdir -p \

# Export all secrets (requires root token)
vault kv list -format=json secret/zerotoship > \

echo "Backup created: \"
