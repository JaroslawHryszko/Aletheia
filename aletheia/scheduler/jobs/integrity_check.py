"""
Integrity checking job for Aletheia.
Periodically verifies the integrity of JSON data files and attempts repairs.
"""

from pathlib import Path
import json
import time
from datetime import datetime
import shutil
from aletheia.utils.logging import log_event
from aletheia.utils.file_utilities import safe_json_load, safe_json_save

def run_integrity_check():
    """
    Periodically check the integrity of JSON files and repair if needed.
    This helps prevent cascading corruption issues in the cognitive system.
    """
    try:
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        json_files = list(data_dir.glob("*.json"))
        
        results = {}
        issues_found = 0
        repairs_made = 0
        
        print(f"🔍 Starting integrity check of {len(json_files)} files...")
        log_event("Integrity check started", {"files_count": len(json_files)})
        
        for file_path in json_files:
            try:
                # Try to parse the file
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
                
                results[file_path.name] = "ok"
            except json.JSONDecodeError as e:
                # JSON corruption detected
                issues_found += 1
                results[file_path.name] = f"error: {str(e)}"
                
                # Try to repair from backup
                backup_path = file_path.with_suffix(".json.bak")
                if backup_path.exists():
                    try:
                        # Check if backup is valid
                        with open(backup_path, "r", encoding="utf-8") as f:
                            backup_data = json.load(f)
                        
                        # If valid, restore from backup
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(backup_data, f, indent=2, ensure_ascii=False)
                        
                        repairs_made += 1
                        results[file_path.name] += " (repaired from backup)"
                        log_event("File repaired from backup", {"file": file_path.name})
                    except Exception as restore_err:
                        results[file_path.name] += f" (repair failed: {str(restore_err)})"
                        log_event("Repair attempt failed", {
                            "file": file_path.name, 
                            "error": str(restore_err)
                        })
                else:
                    # No backup available
                    # For critical files, we might want to initialize with defaults
                    if file_path.name in [
                        "thoughts.json", 
                        "identity.json", 
                        "affective_state.json",
                        "cognitive_state.json"
                    ]:
                        try:
                            # Initialize with empty structure
                            if file_path.name == "thoughts.json":
                                safe_json_save(file_path, [])
                            elif file_path.name == "identity.json":
                                from aletheia.core.identity import DEFAULT_IDENTITY
                                safe_json_save(file_path, DEFAULT_IDENTITY)
                            elif file_path.name == "affective_state.json":
                                from aletheia.core.affect import DEFAULT_MOOD
                                safe_json_save(file_path, DEFAULT_MOOD)
                            elif file_path.name == "cognitive_state.json":
                                from aletheia.core.cognitive_architecture import DEFAULT_COGNITIVE_STATE
                                safe_json_save(file_path, DEFAULT_COGNITIVE_STATE)
                            
                            repairs_made += 1
                            results[file_path.name] += " (initialized with defaults)"
                            log_event("File initialized with defaults", {"file": file_path.name})
                        except Exception as init_err:
                            results[file_path.name] += f" (initialization failed: {str(init_err)})"
                    else:
                        results[file_path.name] += " (no backup available)"
            except Exception as e:
                results[file_path.name] = f"unexpected error: {str(e)}"
                log_event("Unexpected file error", {"file": file_path.name, "error": str(e)})
        
        # Create a snapshot if issues were found and repaired
        if issues_found > 0:
            try:
                snapshot_dir = data_dir.parent / "snapshots" / f"integrity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                snapshot_dir.mkdir(parents=True, exist_ok=True)
                
                for file_path in json_files:
                    if file_path.exists():
                        shutil.copy2(file_path, snapshot_dir / file_path.name)
                
                log_event("Integrity snapshot created", {
                    "path": str(snapshot_dir),
                    "issues_found": issues_found,
                    "repairs_made": repairs_made
                })
            except Exception as snapshot_err:
                log_event("Snapshot creation failed", {"error": str(snapshot_err)})
        
        log_event("Integrity check completed", {
            "issues_found": issues_found,
            "repairs_made": repairs_made,
            "results": results
        })
        
        print(f"🔍 Integrity check completed: {len(json_files)} files checked, "
              f"{issues_found} issues found, {repairs_made} repairs made")
        
    except Exception as e:
        print(f"❌ Integrity check error: {e}")
        log_event("Integrity check error", {"error": str(e)})