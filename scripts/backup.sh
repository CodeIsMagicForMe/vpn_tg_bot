#!/usr/bin/env bash
set -euo pipefail

# Базовый шаблон бэкапа Postgres -> S3-совместимое хранилище
# Требует переменные: POSTGRES_*, MINIO_* и установленный rclone с конфигом `r2:`

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILE="backup_${TIMESTAMP}.sql.gz"

echo "Dumping Postgres..."
pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$FILE"

echo "Uploading to object storage..."
rclone copy "$FILE" r2:vpn-config-backups/

rm "$FILE"
echo "Backup completed: $FILE"
