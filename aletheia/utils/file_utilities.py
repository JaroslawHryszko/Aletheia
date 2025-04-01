"""
Utility functions for safe file operations in Aletheia.
These utilities help prevent JSON corruption and handle concurrent access.
"""

import json
import os
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Union
from aletheia.utils.logging import log_event

class FileLock:
    """
    A simple file-based locking mechanism to prevent concurrent access to files.
    """
    def __init__(self, file_path: Union[str, Path], timeout: int = 10):
        self.file_path = Path(file_path)
        self.lock_path = self.file_path.with_suffix(self.file_path.suffix + ".lock")
        self.timeout = timeout
        self.locked = False

    def acquire(self) -> bool:
        """Acquire the lock, waiting up to timeout seconds"""
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
        """Release the lock if held"""
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
    """
    Safely save data to a JSON file with backup creation and validation.
    
    Args:
        file_path: Path to the JSON file
        data: Data to be saved (must be JSON-serializable)
        
    Returns:
        bool: True if save was successful, False otherwise
    """
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
            log_event("Backup creation failed", {"file": str(file_path), "error": str(e)})
    
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
        log_event("File save error", {"file": str(file_path), "error": str(e)})
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass
        return False


def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Safely load JSON data from a file with error handling and backup recovery.
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is corrupted
        
    Returns:
        The loaded data or the default value
    """
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
                log_event("File recovered from backup", {"file": str(file_path)})
                return data
            except Exception as backup_err:
                print(f"Backup recovery failed for {file_path}: {backup_err}")
                log_event("Backup recovery failed", {"file": str(file_path), "error": str(backup_err)})
        
        print(f"JSON decode error in {file_path}: {e}")
        log_event("JSON decode error", {"file": str(file_path), "error": str(e)})
        return default
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        log_event("File load error", {"file": str(file_path), "error": str(e)})
        return default


def fix_json_files(directory_path: Union[str, Path]) -> Dict[str, str]:
    """
    Attempt to fix all JSON files in the specified directory.
    
    Args:
        directory_path: Path to directory containing JSON files
        
    Returns:
        Dict mapping filenames to results
    """
    directory = Path(directory_path)
    json_files = list(directory.glob("*.json"))
    results = {}
    
    for file_path in json_files:
        print(f"Checking file: {file_path}")
        try:
            # Try to read the file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Try to parse
            try:
                data = json.loads(content)
                print(f"✅ File {file_path.name} is valid")
                results[file_path.name] = "valid"
                
                # Save corrected version (optional)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
            except json.JSONDecodeError as e:
                print(f"❌ Error in file {file_path.name}: {e}")
                results[file_path.name] = f"error: {str(e)}"
                
                # Try to recover from backup
                backup_path = file_path.with_suffix(".json.bak")
                if backup_path.exists():
                    try:
                        print(f"Restoring from backup: {backup_path}")
                        with open(backup_path, "r", encoding="utf-8") as f:
                            backup_content = f.read()
                            # Validate backup
                            json.loads(backup_content)
                        
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(backup_content)
                        
                        results[file_path.name] += " (restored from backup)"
                    except Exception as backup_err:
                        results[file_path.name] += f" (backup restoration failed: {str(backup_err)})"
                else:
                    results[file_path.name] += " (no backup available)"
                
        except Exception as e:
            print(f"❗ Error processing file {file_path.name}: {e}")
            results[file_path.name] = f"processing error: {str(e)}"
    
    log_event("JSON files check completed", {
        "checked": len(json_files),
        "results": results
    })
    
    return results