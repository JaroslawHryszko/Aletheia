#!/bin/bash

NOW=$(date +"%Y%m%d_%H%M%S")
SNAPSHOT_DIR="snapshots/$NOW"

echo "📸 Creating Aletheia snapshot: $SNAPSHOT_DIR"

mkdir -p "$SNAPSHOT_DIR"

# Core cognitive data
cp -r data/thoughts.json "$SNAPSHOT_DIR/thoughts.json"
cp -r data/identity.json "$SNAPSHOT_DIR/identity.json"
cp -r data/affective_state.json "$SNAPSHOT_DIR/affective_state.json"
cp -r data/relational_map.json "$SNAPSHOT_DIR/relational_map.json"

# Optional logs and shadows
cp -r data/logs "$SNAPSHOT_DIR/logs"
cp -r data/shadows "$SNAPSHOT_DIR/shadows"

# Latest status
cp -r data/status.json "$SNAPSHOT_DIR/status.json"

echo "✅ Snapshot complete."
