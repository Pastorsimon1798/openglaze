#!/bin/bash
# OpenGlaze Backup Script
# Backs up the default SQLite database and uploaded files.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="openglaze_backup_${DATE}"
DB_PATH="${DATABASE_PATH:-glaze.db}"
UPLOAD_DIR="${UPLOAD_DIR:-frontend/uploads}"

mkdir -p "$BACKUP_DIR"

echo "================================================"
echo "  OpenGlaze Backup"
echo "================================================"
echo "Database: $DB_PATH"
echo "Uploads:  $UPLOAD_DIR"
echo ""

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$workdir/${BACKUP_NAME}_database.db"
    echo "  ✓ Database copied"
else
    echo "  ! Database not found at $DB_PATH; skipping database copy"
fi

if [ -d "$UPLOAD_DIR" ]; then
    tar -czf "$workdir/${BACKUP_NAME}_uploads.tar.gz" "$UPLOAD_DIR"
    echo "  ✓ Uploads archived"
else
    echo "  ! Upload directory not found at $UPLOAD_DIR; skipping uploads"
fi

if [ -f ".env" ]; then
    grep -viE 'KEY|SECRET|PASSWORD|TOKEN|CREDENTIAL' .env > "$workdir/${BACKUP_NAME}_config.env" || true
    echo "  ✓ Non-sensitive config copied"
fi

if [ -z "$(find "$workdir" -type f -maxdepth 1 2>/dev/null)" ]; then
    echo "No backup inputs found."
    exit 1
fi

tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" -C "$workdir" .
echo "  ✓ Backup written: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
ls -lh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
