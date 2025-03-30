#!/bin/bash
NOW=$(date +"%Y%m%d_%H%M")
SNAPSHOT_DIR="snapshots/$NOW"
mkdir -p "$SNAPSHOT_DIR"
cp -r data "$SNAPSHOT_DIR/"
cp -r aletheia/core "$SNAPSHOT_DIR/"
cp config.yaml "$SNAPSHOT_DIR/"

echo "🧾 Snapshot zapisany w $SNAPSHOT_DIR"
