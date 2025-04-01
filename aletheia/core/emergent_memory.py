"""
Enhanced emergent memory system for Aletheia.
Includes improved error handling and file saving to prevent JSON corruption.
"""

import json
import os
import faiss
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional, Union
import random
from collections import defaultdict

from aletheia.utils.logging import log_event
from aletheia.utils.file_utilities import FileLock, safe_json_save, safe_json_load

# === Paths and configuration ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
THOUGHTS_FILE = DATA_DIR / "thoughts.json"
INDEX_FILE = DATA_DIR / "faiss_index.index"
META_FILE = DATA_DIR / "index_meta.pkl"
CLUSTERS_FILE = DATA_DIR / "concept_clusters.json"
ASSOCIATIONS_FILE = DATA_DIR / "thought_associations.json"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# === Load embedding model ===
try:
    embedder = SentenceTransformer(EMBEDDING_MODEL)
except Exception as e:
    print(f"Warning: Error loading embedding model: {e}")
    log_event("Embedding model load error", {"error": str(e)})
    # We'll create a fallback embedder that returns zeros
    # This allows the system to continue running even if the model fails to load
    class DummyEmbedder:
        def encode(self, texts, **kwargs):
            if isinstance(texts, str):
                return np.zeros(EMBEDDING_DIM, dtype=np.float32)
            return np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
    embedder = DummyEmbedder()

# === Initialize memory ===
def init_storage():
    """Initialize all storage files with proper error handling"""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        
        # Initialize thoughts.json
        if not THOUGHTS_FILE.exists():
            with FileLock(THOUGHTS_FILE):
                safe_json_save(THOUGHTS_FILE, [])

        # Initialize FAISS index
        if not INDEX_FILE.exists():
            try:
                index = faiss.IndexFlatL2(EMBEDDING_DIM)
                faiss.write_index(index, str(INDEX_FILE))
            except Exception as e:
                print(f"Error initializing FAISS index: {e}")
                log_event("FAISS index initialization error", {"error": str(e)})

        # Initialize meta file
        if not META_FILE.exists():
            try:
                with open(META_FILE, "wb") as f:
                    pickle.dump([], f)
            except Exception as e:
                print(f"Error initializing meta file: {e}")
                log_event("Meta file initialization error", {"error": str(e)})
                
        # Initialize clusters file
        if not CLUSTERS_FILE.exists():
            with FileLock(CLUSTERS_FILE):
                safe_json_save(CLUSTERS_FILE, {
                    "clusters": [], 
                    "last_updated": datetime.utcnow().isoformat()
                })
                
        # Initialize associations file
        if not ASSOCIATIONS_FILE.exists():
            with FileLock(ASSOCIATIONS_FILE):
                safe_json_save(ASSOCIATIONS_FILE, {
                    "associations": {}, 
                    "last_updated": datetime.utcnow().isoformat()
                })
                
        log_event("Storage initialization complete", {
            "path": str(DATA_DIR)
        })
    except Exception as e:
        print(f"Error initializing storage: {e}")
        log_event("Storage initialization error", {"error": str(e)})
        raise

# === Core memory operations ===
def load_thoughts() -> List[Dict[str, Any]]:
    """
    Load thoughts from storage with error handling
    """
    with FileLock(THOUGHTS_FILE):
        return safe_json_load(THOUGHTS_FILE, default=[])

def save_thought(thought: str, metadata: dict = None) -> dict:
    """
    Save a thought with richer metadata and establish connections
    Enhanced with proper error handling and file locking
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        
        # Sanitize thought text to avoid control characters that can break JSON
        thought = thought.strip()
        # Replace control characters with spaces
        thought = ''.join(ch if ord(ch) >= 32 else ' ' for ch in thought)
        
        # Enrich metadata
        if metadata is None:
            metadata = {}
        
        entry = {
            "timestamp": timestamp,
            "thought": thought,
            "meta": metadata or {},
            "thought_id": f"t_{int(datetime.utcnow().timestamp())}",
            "connections": [],
            "activation": 1.0,
            "relevance_score": 0.0
        }

        # Safe load and save with file locking
        with FileLock(THOUGHTS_FILE):
            thoughts = safe_json_load(THOUGHTS_FILE, default=[])
            thoughts.append(entry)
            safe_json_save(THOUGHTS_FILE, thoughts)

        # Embed and save to FAISS with proper error handling
        try:
            vec = embedder.encode([entry["thought"]])[0]
            index, meta = load_index()
            
            # Check if index is valid
            if index is None or meta is None:
                raise ValueError("Failed to load valid index")
                
            index.add(np.array([vec], dtype=np.float32))
            meta.append(entry)
            save_index(index, meta)
        except Exception as e:
            print(f"Warning: Error updating index for thought: {e}")
            log_event("Index update error", {"error": str(e), "thought_id": entry["thought_id"]})
        
        # Connect this thought to other relevant thoughts
        try:
            all_thoughts = load_thoughts()
            establish_connections(entry, all_thoughts)
        except Exception as e:
            print(f"Warning: Error establishing connections: {e}")
            log_event("Connection error", {"error": str(e), "thought_id": entry["thought_id"]})
        
        # Periodically update conceptual clusters (every ~20 thoughts)
        try:
            if len(thoughts) % 20 == 0:
                update_concept_clusters()
        except Exception as e:
            print(f"Warning: Error updating concept clusters: {e}")
            log_event("Concept clusters update error", {"error": str(e)})
        
        # Decay activation of older thoughts
        try:
            if len(thoughts) % 10 == 0:
                decay_old_thoughts()
        except Exception as e:
            print(f"Warning: Error during thought activation decay: {e}")
            log_event("Activation decay error", {"error": str(e)})
        
        return entry
    except Exception as e:
        print(f"Error saving thought: {e}")
        log_event("Save thought error", {"error": str(e)})
        # Create a minimal valid entry to return
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "thought": thought[:100] + "..." if len(thought) > 100 else thought,
            "meta": metadata or {},
            "thought_id": f"t_error_{int(datetime.utcnow().timestamp())}",
            "error": str(e)
        }

def establish_connections(new_thought: dict, all_thoughts: List[dict]):
    """Create meaningful connections between thoughts with error handling"""
    try:
        if not all_thoughts or len(all_thoughts) < 2:
            return
        
        # Find semantically similar thoughts
        similar_thoughts = search_similar_thoughts(
            new_thought["thought"], 
            top_k=5, 
            exclude_id=new_thought["thought_id"]
        )
        
        # Load existing associations
        with FileLock(ASSOCIATIONS_FILE):
            associations = safe_json_load(
                ASSOCIATIONS_FILE, 
                default={"associations": {}, "last_updated": datetime.utcnow().isoformat()}
            )
        
        # Create connections based on similarity and origin types
        connections = []
        for similar in similar_thoughts:
            # Skip if this is the same thought
            if similar.get("thought_id") == new_thought["thought_id"]:
                continue
                
            # Calculate connection strength based on multiple factors
            connection_strength = calculate_connection_strength(new_thought, similar)
            
            if connection_strength > 0.3:
                connection = {
                    "to_id": similar.get("thought_id"),
                    "strength": connection_strength,
                    "type": determine_connection_type(new_thought, similar),
                    "created_at": datetime.utcnow().isoformat()
                }
                connections.append(connection)
                
                # Update the global associations graph
                source_id = new_thought["thought_id"]
                target_id = similar.get("thought_id")
                
                if source_id not in associations["associations"]:
                    associations["associations"][source_id] = []
                
                associations["associations"][source_id].append({
                    "to": target_id,
                    "strength": connection_strength,
                    "type": connection["type"]
                })
        
        # Update the new thought with its connections
        update_thought_connections(new_thought["thought_id"], connections)
        
        # Save updated associations
        with FileLock(ASSOCIATIONS_FILE):
            associations["last_updated"] = datetime.utcnow().isoformat()
            safe_json_save(ASSOCIATIONS_FILE, associations)
    except Exception as e:
        print(f"Error establishing connections: {e}")
        log_event("Connection establishment error", {
            "error": str(e), 
            "thought_id": new_thought.get("thought_id")
        })

def calculate_connection_strength(thought1: dict, thought2: dict) -> float:
    """Calculate the strength of connection between two thoughts"""
    try:
        # Base strength from semantic similarity
        vec1 = embedder.encode([thought1["thought"]])[0]
        vec2 = embedder.encode([thought2["thought"]])[0]
        semantic_similarity = max(0, min(1, 1.0 - (np.linalg.norm(vec1 - vec2) / 2.0)))
        
        # Factor in time proximity
        try:
            time1 = datetime.fromisoformat(thought1["timestamp"])
            time2 = datetime.fromisoformat(thought2["timestamp"])
            time_diff = abs((time1 - time2).total_seconds() / 3600)  # in hours
            time_factor = 1.0 / (1.0 + 0.1 * time_diff)  # Decay with time difference
        except (ValueError, KeyError):
            # If timestamp parsing fails, use default value
            time_factor = 0.5
        
        # Factor in origin relationship
        origin1 = thought1.get("meta", {}).get("origin", "unknown")
        origin2 = thought2.get("meta", {}).get("origin", "unknown")
        origin_factor = 1.2 if origin1 == origin2 else 0.8
        
        # Combined strength (weighted average)
        strength = (semantic_similarity * 0.6) + (time_factor * 0.2) + (origin_factor * 0.2)
        return min(1.0, max(0.0, strength))
    except Exception as e:
        print(f"Error calculating connection strength: {e}")
        log_event("Connection strength calculation error", {"error": str(e)})
        return 0.5  # Default moderate strength on error

def determine_connection_type(thought1: dict, thought2: dict) -> str:
    """Determine the type of connection between thoughts"""
    try:
        origin1 = thought1.get("meta", {}).get("origin", "unknown")
        origin2 = thought2.get("meta", {}).get("origin", "unknown")
        
        # Logic to determine connection type
        if origin1 == "dream" and origin2 == "reflection":
            return "dream_inspiration"
        elif origin1 == "reflection" and origin2 == "dream":
            return "reflection_of_dream"
        elif origin1 == origin2:
            return f"shared_{origin1}_context"
        elif "existential_question" in [origin1, origin2]:
            return "philosophical_link"
        else:
            return "semantic_association"
    except Exception as e:
        # Fallback on error
        return "semantic_association"

def update_thought_connections(thought_id: str, connections: List[dict]):
    """Update a thought's connections in storage"""
    try:
        with FileLock(THOUGHTS_FILE):
            thoughts = safe_json_load(THOUGHTS_FILE, default=[])
            
            for i, thought in enumerate(thoughts):
                if thought.get("thought_id") == thought_id:
                    thoughts[i]["connections"] = connections
                    safe_json_save(THOUGHTS_FILE, thoughts)
                    return
    except Exception as e:
        print(f"Error updating thought connections: {e}")
        log_event("Connection update error", {"error": str(e), "thought_id": thought_id})

# === Conceptual clustering and emergent concepts ===
def update_concept_clusters():
    """Generate and update conceptual clusters from thoughts"""
    try:
        thoughts = load_thoughts()
        if len(thoughts) < 10:  # Need enough thoughts for meaningful clusters
            return
        
        # Extract embeddings for clustering
        texts = [t["thought"] for t in thoughts]
        embeddings = embedder.encode(texts)
        
        # Use FAISS for clustering
        n_clusters = min(max(3, len(thoughts) // 10), 20)  # Dynamic number of clusters
        kmeans = faiss.Kmeans(d=EMBEDDING_DIM, k=n_clusters, niter=20)
        kmeans.train(np.array(embeddings).astype(np.float32))
        
        # Get cluster assignments
        _, labels = kmeans.index.search(np.array(embeddings).astype(np.float32), 1)
        
        # Organize thoughts by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(labels.flatten()):
            thought_data = thoughts[i].copy()
            clusters[int(label)].append(thought_data)
        
        # Extract key concepts from each cluster
        cluster_data = []
        for cluster_id, cluster_thoughts in clusters.items():
            # Get the centroid thought
            cluster_center = kmeans.centroids[cluster_id]
            distances = [np.linalg.norm(embedder.encode([t["thought"]])[0] - cluster_center) for t in cluster_thoughts]
            central_thought_idx = np.argmin(distances)
            central_thought = cluster_thoughts[central_thought_idx]
            
            # Generate cluster concept
            concept = {
                "id": f"concept_{cluster_id}",
                "central_thought": central_thought["thought"],
                "thought_ids": [t["thought_id"] for t in cluster_thoughts],
                "size": len(cluster_thoughts),
                "created_at": datetime.utcnow().isoformat(),
                "common_themes": extract_common_themes(cluster_thoughts)
            }
            cluster_data.append(concept)
        
        # Save updated clusters
        with FileLock(CLUSTERS_FILE):
            safe_json_save(CLUSTERS_FILE, {
                "clusters": cluster_data,
                "last_updated": datetime.utcnow().isoformat()
            })
    except Exception as e:
        print(f"Error updating concept clusters: {e}")
        log_event("Concept clusters update error", {"error": str(e)})
    
def extract_common_themes(thoughts: List[dict]) -> List[str]:
    """Extract common themes or concepts from a group of thoughts"""
    try:
        # Simple implementation combining common origins and basic term frequency
        # In a more advanced version, this could use topic modeling or NLP extraction
        
        origins = defaultdict(int)
        for thought in thoughts:
            origin = thought.get("meta", {}).get("origin", "unknown")
            origins[origin] += 1
        
        # Return the most common origins as "themes"
        themes = [o for o, c in sorted(origins.items(), key=lambda x: x[1], reverse=True)[:3]]
        
        return themes
    except Exception as e:
        print(f"Error extracting common themes: {e}")
        log_event("Theme extraction error", {"error": str(e)})
        return ["unknown"]

# === Memory activation and decay ===
def decay_old_thoughts():
    """Apply activation decay to older thoughts with error handling"""
    try:
        with FileLock(THOUGHTS_FILE):
            thoughts = safe_json_load(THOUGHTS_FILE, default=[])
            current_time = datetime.utcnow()
            
            for i, thought in enumerate(thoughts):
                # Skip if no activation value yet
                if "activation" not in thought:
                    thoughts[i]["activation"] = 1.0
                    continue
                    
                # Calculate age in days
                try:
                    thought_time = datetime.fromisoformat(thought["timestamp"])
                    age_days = (current_time - thought_time).total_seconds() / (24 * 3600)
                    
                    # Apply decay function
                    decay_factor = 1.0 / (1.0 + 0.05 * age_days)  # Slow decay
                    thoughts[i]["activation"] *= decay_factor
                    
                    # Don't let activation drop below 0.1
                    thoughts[i]["activation"] = max(0.1, thoughts[i]["activation"])
                except (ValueError, KeyError):
                    # If timestamp parsing fails, assign default activation
                    thoughts[i]["activation"] = 0.5
            
            safe_json_save(THOUGHTS_FILE, thoughts)
    except Exception as e:
        print(f"Error during thought activation decay: {e}")
        log_event("Activation decay error", {"error": str(e)})

# === Advanced search and retrieval ===
def search_similar_thoughts(query: str, top_k: int = 5, exclude_id: str = None) -> List[dict]:
    """Find semantically similar thoughts with enhanced filtering and error handling"""
    try:
        index, meta = load_index()
        if index is None or meta is None or len(meta) == 0:
            return []

        query_vec = embedder.encode([query])[0]
        
        # Get more results than needed for filtering
        k_search = min(top_k * 2, len(meta))
        D, I = index.search(np.array([query_vec], dtype=np.float32), k_search)
        
        # Filter and sort results
        results = []
        for idx in I[0]:
            if idx < len(meta):
                thought = meta[idx]
                # Skip excluded thought
                if exclude_id and thought.get("thought_id") == exclude_id:
                    continue
                    
                # Apply activation as a factor in relevance
                activation = thought.get("activation", 1.0)
                semantic_score = 1.0 - (D[0][list(I[0]).index(idx)] / 2.0)  # Convert distance to similarity
                
                # Combined relevance score
                relevance = (semantic_score * 0.7) + (activation * 0.3)
                thought_copy = thought.copy()
                thought_copy["relevance_score"] = relevance
                
                results.append(thought_copy)
        
        # Sort by relevance and return top_k
        sorted_results = sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)
        return sorted_results[:top_k]
    except Exception as e:
        print(f"Error searching similar thoughts: {e}")
        log_event("Similar thought search error", {"error": str(e), "query": query[:50]})
        return []

def get_associated_thoughts(thought_id: str, min_strength: float = 0.4) -> List[dict]:
    """Get thoughts associated with the given thought through connections"""
    try:
        associations = load_associations()
        if thought_id not in associations["associations"]:
            return []
        
        # Get all thoughts that have strong enough connections
        associated_ids = []
        for assoc in associations["associations"][thought_id]:
            if assoc.get("strength", 0) >= min_strength:
                associated_ids.append(assoc.get("to", ""))
        
        # Retrieve the actual thoughts
        all_thoughts = load_thoughts()
        associated_thoughts = []
        for thought in all_thoughts:
            if thought.get("thought_id") in associated_ids:
                associated_thoughts.append(thought)
        
        return associated_thoughts
    except Exception as e:
        print(f"Error getting associated thoughts: {e}")
        log_event("Associated thoughts error", {"error": str(e), "thought_id": thought_id})
        return []

def get_concept_thoughts(concept_id: str) -> List[dict]:
    """Get all thoughts belonging to a concept cluster"""
    try:
        with FileLock(CLUSTERS_FILE):
            clusters = safe_json_load(CLUSTERS_FILE, default={"clusters": []})["clusters"]
        
        for cluster in clusters:
            if cluster["id"] == concept_id:
                thought_ids = cluster.get("thought_ids", [])
                
                # Retrieve the thoughts
                all_thoughts = load_thoughts()
                return [t for t in all_thoughts if t.get("thought_id") in thought_ids]
        
        return []
    except Exception as e:
        print(f"Error getting concept thoughts: {e}")
        log_event("Concept thoughts error", {"error": str(e), "concept_id": concept_id})
        return []

# === Utility functions ===
def load_associations():
    """Load the thought associations graph"""
    with FileLock(ASSOCIATIONS_FILE):
        return safe_json_load(
            ASSOCIATIONS_FILE, 
            default={"associations": {}, "last_updated": datetime.utcnow().isoformat()}
        )

def generate_thought_trace(start_id: str, depth: int = 3, branch_factor: int = 2) -> List[dict]:
    """Generate a trace of connected thoughts starting from a seed thought"""
    try:
        all_thoughts = load_thoughts()
        thought_dict = {t.get("thought_id", ""): t for t in all_thoughts}
        
        if start_id not in thought_dict:
            return []
        
        trace = [thought_dict[start_id]]
        current_ids = [start_id]
        
        for _ in range(depth):
            next_ids = []
            for current_id in current_ids:
                # Get connected thoughts
                connected = []
                for thought in all_thoughts:
                    for conn in thought.get("connections", []):
                        if conn.get("to_id") == current_id:
                            connected.append((thought.get("thought_id", ""), conn.get("strength", 0)))
                
                # Add self-connections from the current thought
                current_thought = thought_dict.get(current_id)
                if current_thought:
                    for conn in current_thought.get("connections", []):
                        connected.append((conn.get("to_id", ""), conn.get("strength", 0)))
                
                # Sort by connection strength and take the top few
                sorted_connections = sorted(connected, key=lambda x: x[1], reverse=True)
                for conn_id, _ in sorted_connections[:branch_factor]:
                    if conn_id in thought_dict and conn_id not in [t.get("thought_id") for t in trace]:
                        trace.append(thought_dict[conn_id])
                        next_ids.append(conn_id)
            
            current_ids = next_ids
            if not current_ids:
                break
        
        return trace
    except Exception as e:
        print(f"Error generating thought trace: {e}")
        log_event("Thought trace error", {"error": str(e), "start_id": start_id})
        return []

# === FAISS I/O with error handling ===
def load_index():
    """Load FAISS index with error handling"""
    try:
        index = faiss.read_index(str(INDEX_FILE))
        
        try:
            with open(META_FILE, "rb") as f:
                meta = pickle.load(f)
        except Exception as meta_error:
            print(f"Error loading meta file: {meta_error}")
            log_event("Meta file load error", {"error": str(meta_error)})
            # Try to rebuild meta from thoughts.json
            thoughts = load_thoughts()
            meta = thoughts
            # Save rebuilt meta
            try:
                with open(META_FILE, "wb") as f:
                    pickle.dump(meta, f)
                print("Meta file rebuilt from thoughts.json")
                log_event("Meta file rebuilt", {"count": len(meta)})
            except Exception as rebuild_error:
                print(f"Error rebuilding meta file: {rebuild_error}")
                log_event("Meta rebuild error", {"error": str(rebuild_error)})
                
        return index, meta
    except Exception as e:
        print(f"Error loading index: {e}")
        log_event("Index load error", {"error": str(e)})
        
        # Try to rebuild index if it's corrupted
        try:
            thoughts = load_thoughts()
            if thoughts:
                print("Attempting to rebuild index from thoughts...")
                index = faiss.IndexFlatL2(EMBEDDING_DIM)
                
                # Embed all thoughts
                embeddings = []
                for thought in thoughts:
                    try:
                        vec = embedder.encode([thought["thought"]])[0]
                        embeddings.append(vec)
                    except Exception as embed_err:
                        print(f"Error embedding thought: {embed_err}")
                        # Add zero vector as fallback
                        embeddings.append(np.zeros(EMBEDDING_DIM, dtype=np.float32))
                
                # Add all embeddings to index
                if embeddings:
                    index.add(np.array(embeddings, dtype=np.float32))
                    
                # Save rebuilt index
                faiss.write_index(index, str(INDEX_FILE))
                
                # Save meta
                with open(META_FILE, "wb") as f:
                    pickle.dump(thoughts, f)
                
                print(f"Index rebuilt with {len(thoughts)} thoughts")
                log_event("Index rebuilt", {"count": len(thoughts)})
                
                return index, thoughts
                
        except Exception as rebuild_error:
            print(f"Error rebuilding index: {rebuild_error}")
            log_event("Index rebuild error", {"error": str(rebuild_error)})
        
        return None, None

def save_index(index, meta):
    """Save FAISS index with error handling"""
    try:
        # Make backup before saving
        if INDEX_FILE.exists():
            backup_path = INDEX_FILE.with_suffix(".index.bak")
            try:
                import shutil
                shutil.copy2(INDEX_FILE, backup_path)
            except Exception as backup_err:
                print(f"Warning: Could not create index backup: {backup_err}")
                
        if META_FILE.exists():
            backup_meta_path = META_FILE.with_suffix(".pkl.bak")
            try:
                import shutil
                shutil.copy2(META_FILE, backup_meta_path)
            except Exception as backup_err:
                print(f"Warning: Could not create meta backup: {backup_err}")
        
        # Save new files
        faiss.write_index(index, str(INDEX_FILE))
        
        with open(META_FILE, "wb") as f:
            pickle.dump(meta, f)
        
        return True
    except Exception as e:
        print(f"Error saving index: {e}")
        log_event("Index save error", {"error": str(e)})
        
        # Try to restore from backup if save failed
        try:
            backup_path = INDEX_FILE.with_suffix(".index.bak")
            backup_meta_path = META_FILE.with_suffix(".pkl.bak")
            
            if backup_path.exists() and backup_meta_path.exists():
                print("Restoring index and meta from backup...")
                import shutil
                shutil.copy2(backup_path, INDEX_FILE)
                shutil.copy2(backup_meta_path, META_FILE)
                print("Index and meta restored from backup")
                log_event("Index restored from backup", {})
        except Exception as restore_err:
            print(f"Error restoring index from backup: {restore_err}")
            log_event("Index restore error", {"error": str(restore_err)})
            
        return False