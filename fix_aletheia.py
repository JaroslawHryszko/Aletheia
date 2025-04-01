#!/usr/bin/env python3
"""
Aletheia JSON Repair Script
---------------------------
This script fixes JSON corruption issues in the Aletheia system.
It scans all JSON files for errors and attempts to repair them.

Usage:
    python fix_aletheia.py [--backup] [--directory DIR]

Options:
    --backup     Create a full backup of data directory before repairs
    --directory  Specify the Aletheia data directory (default: ./aletheia/data)
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime
import traceback

def create_backup(data_dir):
    """Create a full backup of the data directory"""
    try:
        # Create timestamp for backup
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = data_dir.parent / f"data_backup_{timestamp}"
        
        # Copy the entire directory
        shutil.copytree(data_dir, backup_dir)
        
        print(f"✅ Created backup: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None

def repair_json_file(file_path):
    """
    Attempt to repair a JSON file
    Returns tuple: (success, file_data or None, error_message or None)
    """
    try:
        # Check if file exists
        if not file_path.exists():
            return False, None, "File does not exist"
        
        # Check if it's empty
        if file_path.stat().st_size == 0:
            return False, None, "File is empty"
        
        # Try to parse the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            data = json.loads(content)
            # File is valid
            return True, data, None
        except json.JSONDecodeError as e:
            error_line = e.lineno
            error_col = e.colno
            error_msg = str(e)
            print(f"  Error at line {error_line}, column {error_col}: {error_msg}")
            
            # Check for backup version
            backup_path = file_path.with_suffix(".json.bak")
            if backup_path.exists():
                try:
                    with open(backup_path, "r", encoding="utf-8") as f:
                        backup_content = f.read()
                    backup_data = json.loads(backup_content)
                    return True, backup_data, "Recovered from backup"
                except Exception as backup_err:
                    return False, None, f"Backup also corrupted: {str(backup_err)}"
            
            # Try simple repairs for common issues
            if "Expecting ',' delimiter" in error_msg:
                # Missing comma - very basic repair attempt
                lines = content.split('\n')
                problem_line = lines[error_line - 1]
                
                # Very simple approach - insert a comma at the error position
                fixed_line = problem_line[:error_col] + "," + problem_line[error_col:]
                lines[error_line - 1] = fixed_line
                
                fixed_content = '\n'.join(lines)
                try:
                    fixed_data = json.loads(fixed_content)
                    return True, fixed_data, "Fixed missing comma"
                except:
                    pass  # If that didn't work, continue to other repair methods
            
            # Try using default empty structures
            if file_path.name == "thoughts.json":
                return True, [], "Initialized with empty array"
            elif "identity.json" in file_path.name:
                # Basic identity structure
                default_identity = {
                    "created_at": datetime.utcnow().isoformat(),
                    "interests": ["self-discovery"],
                    "goals": {
                        "self_discovery": {
                            "description": "Understand what 'I' means in my context.",
                            "progress": 0.1
                        }
                    }
                }
                return True, default_identity, "Initialized with default identity"
            elif "affective_state.json" in file_path.name:
                default_mood = {"mood": "neutral", "intensity": 0.5}
                return True, default_mood, "Initialized with default mood"
            
            return False, None, f"Unrecoverable JSON error: {error_msg}"
            
    except Exception as e:
        return False, None, f"Error processing file: {str(e)}"

def scan_and_fix_json_files(data_dir):
    """
    Scan all JSON files in the data directory and attempt to fix corruption issues
    """
    fixed_count = 0
    error_count = 0
    total_count = 0
    
    # Get all JSON files
    json_files = list(data_dir.glob("**/*.json"))
    print(f"Found {len(json_files)} JSON files to check")
    
    # Process each file
    for file_path in json_files:
        total_count += 1
        print(f"\nProcessing {file_path.relative_to(data_dir)}:")
        
        # Ensure we have a backup of this specific file
        file_backup = file_path.with_suffix(".json.bak")
        if not file_backup.exists():
            try:
                shutil.copy2(file_path, file_backup)
                print(f"  Created file-specific backup: {file_backup.name}")
            except Exception as e:
                print(f"  Warning: Failed to create file backup: {e}")
        
        # Attempt repair
        success, data, message = repair_json_file(file_path)
        
        if success:
            if message:
                print(f"  ✅ {message}")
                
            # Save the repaired data
            try:
                # Use temporary file for safety
                temp_path = file_path.with_suffix(".json.tmp")
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Verify the temporary file
                with open(temp_path, "r", encoding="utf-8") as f:
                    json.load(f)
                
                # Replace the original file
                temp_path.replace(file_path)
                print(f"  ✅ File saved successfully")
                fixed_count += 1
            except Exception as save_err:
                print(f"  ❌ Error saving repaired file: {save_err}")
                error_count += 1
        else:
            print(f"  ❌ Repair failed: {message}")
            error_count += 1
    
    return total_count, fixed_count, error_count

def create_file_utils():
    """Create the file_utilities.py module if it doesn't exist"""
    file_utils_content = """
import json
import os
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Union

class FileLock:
    \"\"\"
    A simple file-based locking mechanism to prevent concurrent access to files.
    \"\"\"
    def __init__(self, file_path: Union[str, Path], timeout: int = 10):
        self.file_path = Path(file_path)
        self.lock_path = self.file_path.with_suffix(self.file_path.suffix + ".lock")
        self.timeout = timeout
        self.locked = False

    def acquire(self) -> bool:
        \"\"\"Acquire the lock, waiting up to timeout seconds\"\"\"
        start_time = time.time()
        while True:
            try:
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(f"Could not acquire lock for {self.file_path} within {self.timeout}s")
                
                # Check if lock exists and if it's not stale
                if self.lock_path.exists():
                    # Check if lock is too old (e.g., 5 minutes)
                    if time.time() - self.lock_path.stat().st_mtime > 300:  # 5 minutes
                        self.lock_path.unlink(missing_ok=True)
                    else:
                        time.sleep(0.1)
                        continue
                
                # Create lock file
                with open(self.lock_path, "w") as f:
                    f.write(f"{os.getpid()},{datetime.utcnow().isoformat()}")
                
                self.locked = True
                return True
            except FileExistsError:
                time.sleep(0.1)
                continue
            except Exception as e:
                raise RuntimeError(f"Error acquiring lock: {e}")

    def release(self) -> None:
        \"\"\"Release the lock if held\"\"\"
        if self.locked and self.lock_path.exists():
            try:
                self.lock_path.unlink()
                self.locked = False
            except Exception as e:
                print(f"Warning: Could not release lock {self.lock_path}: {e}")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def safe_json_save(file_path: Union[str, Path], data: Any) -> bool:
    \"\"\"
    Safely save data to a JSON file with backup creation and validation.
    
    Args:
        file_path: Path to the JSON file
        data: Data to be saved (must be JSON-serializable)
        
    Returns:
        bool: True if save was successful, False otherwise
    \"\"\"
    file_path = Path(file_path)
    
    # Create parent directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup if file exists
    if file_path.exists():
        backup_path = file_path.with_suffix(".json.bak")
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            print(f"Warning: Could not create backup of {file_path}: {e}")
    
    # Save to temporary file
    temp_path = file_path.with_suffix(".json.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Validate saved file
        with open(temp_path, "r", encoding="utf-8") as f:
            json.load(f)  # Try parsing
        
        # Replace target file
        os.replace(temp_path, file_path)
        
        return True
    except Exception as e:
        print(f"Error saving file {file_path}: {e}")
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass
        return False


def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    \"\"\"
    Safely load JSON data from a file with error handling and backup recovery.
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is corrupted
        
    Returns:
        The loaded data or the default value
    \"\"\"
    file_path = Path(file_path)
    
    if not file_path.exists():
        return default
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # Try to recover from backup
        backup_path = file_path.with_suffix(".json.bak")
        if backup_path.exists():
            try:
                print(f"Attempting to recover {file_path} from backup...")
                with open(backup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Restore from backup
                safe_json_save(file_path, data)
                return data
            except Exception as backup_err:
                print(f"Backup recovery failed for {file_path}: {backup_err}")
        
        print(f"JSON decode error in {file_path}: {e}")
        return default
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return default
"""

    try:
        # Create the utils directory if it doesn't exist
        utils_dir = Path("aletheia/utils")
        utils_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the module
        utils_file = utils_dir / "file_utilities.py"
        with open(utils_file, "w", encoding="utf-8") as f:
            f.write(file_utils_content)
        
        print(f"✅ Created file utilities module: {utils_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating file utilities module: {e}")
        return False

def create_integrity_check():
    """Create the integrity_check.py module"""
    integrity_check_content = """
from pathlib import Path
import json
import time
from datetime import datetime
import shutil

def run_integrity_check():
    \"\"\"
    Periodically check the integrity of JSON files and repair if needed.
    This helps prevent cascading corruption issues in the cognitive system.
    \"\"\"
    try:
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        json_files = list(data_dir.glob("*.json"))
        
        results = {}
        issues_found = 0
        repairs_made = 0
        
        print(f"🔍 Starting integrity check of {len(json_files)} files...")
        
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
                    except Exception as restore_err:
                        results[file_path.name] += f" (repair failed: {str(restore_err)})"
                else:
                    # No backup available
                    results[file_path.name] += " (no backup available)"
            except Exception as e:
                results[file_path.name] = f"unexpected error: {str(e)}"
        
        # Create a snapshot if issues were found and repaired
        if issues_found > 0:
            try:
                snapshot_dir = data_dir.parent / "snapshots" / f"integrity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                snapshot_dir.mkdir(parents=True, exist_ok=True)
                
                for file_path in json_files:
                    if file_path.exists():
                        shutil.copy2(file_path, snapshot_dir / file_path.name)
            except Exception:
                pass
        
        print(f"🔍 Integrity check completed: {len(json_files)} files checked, "
              f"{issues_found} issues found, {repairs_made} repairs made")
        
        return {
            "files_checked": len(json_files),
            "issues_found": issues_found,
            "repairs_made": repairs_made,
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Integrity check error: {e}")
        return {
            "error": str(e)
        }
"""

    try:
        # Create the jobs directory if it doesn't exist
        jobs_dir = Path("aletheia/scheduler/jobs")
        jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the module
        integrity_file = jobs_dir / "integrity_check.py"
        with open(integrity_file, "w", encoding="utf-8") as f:
            f.write(integrity_check_content)
        
        print(f"✅ Created integrity check module: {integrity_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating integrity check module: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fix JSON corruption in Aletheia")
    parser.add_argument("--backup", action="store_true", help="Create full backup before fixing")
    parser.add_argument("--directory", type=str, default="./aletheia/data", 
                       help="Path to Aletheia data directory")
    
    args = parser.parse_args()
    
    try:
        # Convert directory to Path
        data_dir = Path(args.directory).resolve()
        
        if not data_dir.exists():
            print(f"❌ Data directory does not exist: {data_dir}")
            return 1
            
        print(f"🔍 Starting Aletheia JSON repair on: {data_dir}")
        
        # Create backup if requested
        if args.backup:
            backup_dir = create_backup(data_dir)
            if not backup_dir:
                print("⚠️ Failed to create backup, do you want to continue? (y/n)")
                response = input().lower()
                if response != 'y':
                    print("Operation cancelled.")
                    return 1
        
        # Create helper modules
        create_file_utils()
        create_integrity_check()
        
        # Scan and fix JSON files
        total, fixed, errors = scan_and_fix_json_files(data_dir)
        
        print("\n===== Summary =====")
        print(f"Total files processed: {total}")
        print(f"Files fixed: {fixed}")
        print(f"Files with errors: {errors}")
        
        if errors > 0:
            print("\n⚠️ Some files could not be fixed. You may need to restore from a backup.")
        else:
            print("\n✅ All JSON files have been processed successfully.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())