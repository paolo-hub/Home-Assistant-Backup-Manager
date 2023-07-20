#!/bin/bash

KEEP=$1

snaps=$(curl -sSL -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/backups | jq -c '.data.backups[] | {date,slug,name}' | sort -r)

echo "$snaps" | tail -n +$((KEEP + 1)) | while read -r backup; do
slug=$(echo "$backup" | jq -r .slug)
curl -sSL -X DELETE -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/backups/${slug}
done
