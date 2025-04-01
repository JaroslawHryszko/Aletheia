# aletheia/core/emergent_memory.py

import json
import os
import faiss
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional
import random
from collections import defaultdict

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
embedder = SentenceTransformer(EMBEDDING_MODEL)

# === Initialize memory ===
def init_storage():
    DATA_DIR.mkdir(exist_ok=True)
    if not THOUGHTS_FILE.exists():
        with open(THOUGHTS_FILE, "w") as f:
            json.dump([], f)

    if not INDEX_FILE.exists():
        index = faiss.IndexFlatL2(EMBEDDING_DIM)
        faiss.write_index(index, str(INDEX_FILE))

    if not META_FILE.exists():
        with open(META_FILE, "wb") as f:
            pickle.dump([], f)
            
    if not CLUSTERS_FILE.exists():
        with open(CLUSTERS_FILE, "w") as f:
            json.dump({"clusters": [], "last_updated": datetime.utcnow().isoformat()}, f)
            
    if not ASSOCIATIONS_FILE.exists():
        with open(ASSOCIATIONS_FILE, "w") as f:
            json.dump({"associations": {}, "last_updated": datetime.utcnow().isoformat()}, f)

# === Core memory operations ===
def load_thoughts():
    with open(THOUGHTS_FILE, "r") as f:
        return json.load(f)

def save_thought(thought: str, metadata: dict = None) -> dict:
    """Save a thought with richer metadata and establish connections"""
    timestamp = datetime.utcnow().isoformat()
    
    # Enrich metadata with more information
    if metadata is None:
        metadata = {}
    
    entry = {
        "timestamp": timestamp,
        "thought": thought.strip(),
        "meta": metadata or {},
        "thought_id": f"t_{int(datetime.utcnow().timestamp())}",
        "connections": [],
        "activation": 1.0,
        "relevance_score": 0.0
    }

    # Save to JSON
    thoughts = load_thoughts()
    thoughts.append(entry)
    with open(THOUGHTS_FILE, "w") as f:
        json.dump(thoughts, f, indent=2)

    # Embed and save to FAISS
    vec = embedder.encode([entry["thought"]])[0]
    index, meta = load_index()
    index.add(np.array([vec], dtype=np.float32))
    meta.append(entry)

    save_index(index, meta)
    
    # Connect this thought to other relevant thoughts
    establish_connections(entry, thoughts)
    
    # Periodically update conceptual clusters (every ~20 thoughts)
    if len(thoughts) % 20 == 0:
        update_concept_clusters()
        
    # Decay activation of older thoughts
    decay_old_thoughts()
    
    return entry

def establish_connections(new_thought: dict, all_thoughts: List[dict]):
    """Create meaningful connections between thoughts"""
    if not all_thoughts or len(all_thoughts) < 2:
        return
    
    # Find semantically similar thoughts
    similar_thoughts = search_similar_thoughts(new_thought["thought"], top_k=5, exclude_id=new_thought["thought_id"])
    
    # Load existing associations
    associations = load_associations()
    
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
    associations["last_updated"] = datetime.utcnow().isoformat()
    with open(ASSOCIATIONS_FILE, "w") as f:
        json.dump(associations, f, indent=2)

def calculate_connection_strength(thought1: dict, thought2: dict) -> float:
    """Calculate the strength of connection between two thoughts"""
    # Base strength from semantic similarity
    vec1 = embedder.encode([thought1["thought"]])[0]
    vec2 = embedder.encode([thought2["thought"]])[0]
    semantic_similarity = 1.0 - (np.linalg.norm(vec1 - vec2) / 2.0)
    
    # Factor in time proximity
    time1 = datetime.fromisoformat(thought1["timestamp"])
    time2 = datetime.fromisoformat(thought2["timestamp"])
    time_diff = abs((time1 - time2).total_seconds() / 3600)  # in hours
    time_factor = 1.0 / (1.0 + 0.1 * time_diff)  # Decay with time difference
    
    # Factor in origin relationship
    origin1 = thought1.get("meta", {}).get("origin", "unknown")
    origin2 = thought2.get("meta", {}).get("origin", "unknown")
    origin_factor = 1.2 if origin1 == origin2 else 0.8
    
    # Combined strength (weighted average)
    strength = (semantic_similarity * 0.6) + (time_factor * 0.2) + (origin_factor * 0.2)
    return min(1.0, max(0.0, strength))

def determine_connection_type(thought1: dict, thought2: dict) -> str:
    """Determine the type of connection between thoughts"""
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

def update_thought_connections(thought_id: str, connections: List[dict]):
    """Update a thought's connections in storage"""
    thoughts = load_thoughts()
    for i, thought in enumerate(thoughts):
        if thought.get("thought_id") == thought_id:
            thoughts[i]["connections"] = connections
            break
    
    with open(THOUGHTS_FILE, "w") as f:
        json.dump(thoughts, f, indent=2)

# === Conceptual clustering and emergent concepts ===
def update_concept_clusters():
    """Generate and update conceptual clusters from thoughts"""
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
    with open(CLUSTERS_FILE, "w") as f:
        json.dump({
            "clusters": cluster_data,
            "last_updated": datetime.utcnow().isoformat()
        }, f, indent=2)
    
def extract_common_themes(thoughts: List[dict]) -> List[str]:
    """Extract common themes or concepts from a group of thoughts"""
    # Simple implementation combining common origins and basic term frequency
    # In a more advanced version, this could use topic modeling or NLP extraction
    
    origins = defaultdict(int)
    for thought in thoughts:
        origin = thought.get("meta", {}).get("origin", "unknown")
        origins[origin] += 1
    
    # Return the most common origins as "themes"
    themes = [o for o, c in sorted(origins.items(), key=lambda x: x[1], reverse=True)[:3]]
    
    return themes

# === Memory activation and decay ===
def decay_old_thoughts():
    """Apply activation decay to older thoughts"""
    thoughts = load_thoughts()
    current_time = datetime.utcnow()
    
    for i, thought in enumerate(thoughts):
        # Skip if no activation value yet
        if "activation" not in thought:
            thoughts[i]["activation"] = 1.0
            continue
            
        # Calculate age in days
        thought_time = datetime.fromisoformat(thought["timestamp"])
        age_days = (current_time - thought_time).total_seconds() / (24 * 3600)
        
        # Apply decay function
        decay_factor = 1.0 / (1.0 + 0.05 * age_days)  # Slow decay
        thoughts[i]["activation"] *= decay_factor
        
        # Don't let activation drop below 0.1
        thoughts[i]["activation"] = max(0.1, thoughts[i]["activation"])
    
    with open(THOUGHTS_FILE, "w") as f:
        json.dump(thoughts, f, indent=2)

# === Advanced search and retrieval ===
def search_similar_thoughts(query: str, top_k: int = 5, exclude_id: str = None) -> List[dict]:
    """Find semantically similar thoughts with enhanced filtering"""
    index, meta = load_index()
    if len(meta) == 0:
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

def get_associated_thoughts(thought_id: str, min_strength: float = 0.4) -> List[dict]:
    """Get thoughts associated with the given thought through connections"""
    associations = load_associations()
    if thought_id not in associations["associations"]:
        return []
    
    # Get all thoughts that have strong enough connections
    associated_ids = []
    for assoc in associations["associations"][thought_id]:
        if assoc["strength"] >= min_strength:
            associated_ids.append(assoc["to"])
    
    # Retrieve the actual thoughts
    all_thoughts = load_thoughts()
    associated_thoughts = []
    for thought in all_thoughts:
        if thought.get("thought_id") in associated_ids:
            associated_thoughts.append(thought)
    
    return associated_thoughts

def get_concept_thoughts(concept_id: str) -> List[dict]:
    """Get all thoughts belonging to a concept cluster"""
    with open(CLUSTERS_FILE, "r") as f:
        clusters = json.load(f)["clusters"]
    
    for cluster in clusters:
        if cluster["id"] == concept_id:
            thought_ids = cluster["thought_ids"]
            
            # Retrieve the thoughts
            all_thoughts = load_thoughts()
            return [t for t in all_thoughts if t.get("thought_id") in thought_ids]
    
    return []

# === Utility functions ===
def load_associations():
    """Load the thought associations graph"""
    if not ASSOCIATIONS_FILE.exists():
        return {"associations": {}, "last_updated": datetime.utcnow().isoformat()}
        
    with open(ASSOCIATIONS_FILE, "r") as f:
        return json.load(f)

def generate_thought_trace(start_id: str, depth: int = 3, branch_factor: int = 2) -> List[dict]:
    """Generate a trace of connected thoughts starting from a seed thought"""
    all_thoughts = load_thoughts()
    thought_dict = {t.get("thought_id"): t for t in all_thoughts}
    
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
                        connected.append((thought.get("thought_id"), conn.get("strength", 0)))
            
            # Add self-connections from the current thought
            current_thought = thought_dict.get(current_id)
            if current_thought:
                for conn in current_thought.get("connections", []):
                    connected.append((conn.get("to_id"), conn.get("strength", 0)))
            
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

# === FAISS I/O ===
def load_index():
    index = faiss.read_index(str(INDEX_FILE))
    with open(META_FILE, "rb") as f:
        meta = pickle.load(f)
    return index, meta

def save_index(index, meta):
    faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "wb") as f:
        pickle.dump(meta, f)