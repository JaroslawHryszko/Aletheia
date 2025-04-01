# aletheia/core/concept_evolution.py

from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import json
import numpy as np
from datetime import datetime
import random
from collections import defaultdict
import networkx as nx
from sentence_transformers import SentenceTransformer

from aletheia.core.emergent_memory import load_thoughts, search_similar_thoughts
from aletheia.utils.logging import log_event

# === Paths and configuration ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONCEPTS_FILE = DATA_DIR / "evolved_concepts.json"

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# === Core concept structures ===
class ConceptNetwork:
    """Manages the evolution and interrelation of concepts over time"""
    
    def __init__(self):
        self.concepts = self._load_concepts()
        self.graph = self._build_graph()
    
    def _load_concepts(self) -> Dict[str, Any]:
        """Load the concept repository"""
        if not CONCEPTS_FILE.exists():
            # Initialize with empty structure
            concepts = {
                "concepts": {},
                "relations": [],
                "evolution_history": [],
                "last_updated": datetime.utcnow().isoformat()
            }
            self._save_concepts(concepts)
            return concepts
        
        with open(CONCEPTS_FILE, "r") as f:
            return json.load(f)
    
    def _save_concepts(self, concepts: Dict[str, Any]) -> None:
        """Save the concept repository"""
        concepts["last_updated"] = datetime.utcnow().isoformat()
        CONCEPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONCEPTS_FILE, "w") as f:
            json.dump(concepts, f, indent=2)
    
    def _build_graph(self) -> nx.Graph:
        """Build a NetworkX graph from the concept relations"""
        G = nx.Graph()
        
        # Add nodes (concepts)
        for concept_id, concept in self.concepts.get("concepts", {}).items():
            G.add_node(
                concept_id, 
                name=concept.get("name", ""),
                salience=concept.get("salience", 0.0),
                first_observed=concept.get("first_observed", "")
            )
        
        # Add edges (relations)
        for relation in self.concepts.get("relations", []):
            G.add_edge(
                relation.get("source"), 
                relation.get("target"),
                type=relation.get("type", "related"),
                strength=relation.get("strength", 0.5)
            )
        
        return G
    
    def update_concept_network(self) -> None:
        """Update the concept network based on recent thoughts"""
        # Get recent thoughts for analysis
        thoughts = load_thoughts()[-100:]  # Last 100 thoughts
        
        if len(thoughts) < 10:
            return  # Not enough data
        
        # 1. Extract potential concepts through clustering
        clusters = self._cluster_thoughts(thoughts)
        
        # 2. Add or update concepts
        for cluster_id, cluster_data in clusters.items():
            concept_name = cluster_data["central_theme"]
            
            # Check if similar concept exists
            similar_concept = self._find_similar_concept(concept_name)
            
            if similar_concept:
                # Update existing concept
                self._update_concept(similar_concept, cluster_data)
            else:
                # Create new concept
                self._create_concept(cluster_data)
        
        # 3. Update relations between concepts
        self._update_concept_relations()
        
        # 4. Save updated concepts
        self._save_concepts(self.concepts)
        
        # 5. Rebuild graph
        self.graph = self._build_graph()
        
        log_event("Concept network updated", {
            "concepts_count": len(self.concepts.get("concepts", {})),
            "relations_count": len(self.concepts.get("relations", []))
        })
    
    def _cluster_thoughts(self, thoughts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Cluster thoughts to identify potential concepts"""
        from sklearn.cluster import DBSCAN
        
        # Extract text and embeddings
        texts = [t.get("thought", "") for t in thoughts]
        embeddings = np.array([embedder.encode(text) for text in texts])
        
        # Cluster using DBSCAN
        clustering = DBSCAN(eps=0.3, min_samples=3).fit(embeddings)
        labels = clustering.labels_
        
        # Organize thoughts by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            if label != -1:  # Skip noise points
                clusters[str(label)].append({
                    "thought": thoughts[i],
                    "embedding": embeddings[i]
                })
        
        # Extract cluster information
        cluster_data = {}
        for cluster_id, cluster_thoughts in clusters.items():
            if len(cluster_thoughts) < 3:
                continue  # Skip small clusters
            
            # Find central thought (closest to centroid)
            centroid = np.mean([ct["embedding"] for ct in cluster_thoughts], axis=0)
            distances = [np.linalg.norm(ct["embedding"] - centroid) for ct in cluster_thoughts]
            central_idx = np.argmin(distances)
            central_thought = cluster_thoughts[central_idx]["thought"]
            
            # Extract key themes
            origin_counts = defaultdict(int)
            for ct in cluster_thoughts:
                origin = ct["thought"].get("meta", {}).get("origin", "unknown")
                origin_counts[origin] += 1
            
            # Get dominant origin
            dominant_origin = max(origin_counts.items(), key=lambda x: x[1])[0] if origin_counts else "unknown"
            
            # Generate a name for the central theme
            central_theme = self._extract_concept_name(central_thought.get("thought", ""))
            
            # Store cluster data
            cluster_data[cluster_id] = {
                "central_theme": central_theme,
                "central_thought_id": central_thought.get("thought_id"),
                "thought_count": len(cluster_thoughts),
                "thought_ids": [ct["thought"].get("thought_id") for ct in cluster_thoughts],
                "dominant_origin": dominant_origin,
                "embedding": centroid.tolist()
            }
        
        return cluster_data
    
    def _extract_concept_name(self, text: str) -> str:
        """Extract a concept name from text"""
        # Simple approach: take first N words or till punctuation
        words = text.split()
        if len(words) <= 3:
            return text
        
        # Look for punctuation to find a natural break
        for i, word in enumerate(words[:10]):
            if word.endswith(('.', '?', '!')):
                return ' '.join(words[:i+1])
        
        # Default to first 5-7 words
        end = min(len(words), random.randint(5, 7))
        return ' '.join(words[:end])
    
    def _find_similar_concept(self, concept_name: str) -> Optional[str]:
        """Find if a similar concept already exists"""
        if not self.concepts.get("concepts"):
            return None
        
        # Get embedding for new concept
        new_embedding = embedder.encode(concept_name)
        
        # Compare with existing concepts
        similarities = {}
        for concept_id, concept in self.concepts["concepts"].items():
            # If concept has embedding
            if "embedding" in concept:
                existing_embedding = np.array(concept["embedding"])
                similarity = 1.0 - np.linalg.norm(new_embedding - existing_embedding)
                similarities[concept_id] = similarity
        
        # Find most similar above threshold
        if similarities:
            most_similar = max(similarities.items(), key=lambda x: x[1])
            if most_similar[1] > 0.7:  # Similarity threshold
                return most_similar[0]
        
        return None
    
    def _create_concept(self, cluster_data: Dict[str, Any]) -> str:
        """Create a new concept from cluster data"""
        concept_id = f"concept_{datetime.utcnow().timestamp()}"
        
        # Create concept structure
        concept = {
            "name": cluster_data["central_theme"],
            "first_observed": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "salience": 0.5,  # Initial salience
            "thought_ids": cluster_data["thought_ids"],
            "central_thought_id": cluster_data["central_thought_id"],
            "evolution_stage": "emerging",
            "dominant_origin": cluster_data["dominant_origin"],
            "embedding": cluster_data["embedding"],
            "related_concepts": []
        }
        
        # Add to concepts dictionary
        if "concepts" not in self.concepts:
            self.concepts["concepts"] = {}
        
        self.concepts["concepts"][concept_id] = concept
        
        # Add to evolution history
        if "evolution_history" not in self.concepts:
            self.concepts["evolution_history"] = []
        
        self.concepts["evolution_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "concept_created",
            "concept_id": concept_id,
            "name": concept["name"],
            "thought_count": len(concept["thought_ids"])
        })
        
        return concept_id
    
    def _update_concept(self, concept_id: str, cluster_data: Dict[str, Any]) -> None:
        """Update an existing concept with new cluster data"""
        concept = self.concepts["concepts"][concept_id]
        
        # Combine thought IDs (unique)
        existing_ids = set(concept.get("thought_ids", []))
        new_ids = set(cluster_data["thought_ids"])
        combined_ids = list(existing_ids.union(new_ids))
        
        # Update concept
        concept["thought_ids"] = combined_ids
        concept["last_updated"] = datetime.utcnow().isoformat()
        
        # Increase salience for active concepts
        current_salience = concept.get("salience", 0.5)
        concept["salience"] = min(1.0, current_salience + 0.1)
        
        # Check if concept should evolve to next stage
        self._check_concept_evolution(concept_id)
        
        # Update the concepts dictionary
        self.concepts["concepts"][concept_id] = concept
        
        # Add to evolution history
        self.concepts["evolution_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "concept_updated",
            "concept_id": concept_id,
            "name": concept["name"],
            "thought_count": len(concept["thought_ids"])
        })
    
    def _check_concept_evolution(self, concept_id: str) -> None:
        """Check if a concept should evolve to next stage"""
        concept = self.concepts["concepts"][concept_id]
        current_stage = concept.get("evolution_stage", "emerging")
        thought_count = len(concept.get("thought_ids", []))
        
        # Evolution stages based on thought count and age
        if current_stage == "emerging" and thought_count >= 10:
            concept["evolution_stage"] = "established"
            
            # Add to evolution history
            self.concepts["evolution_history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "concept_evolved",
                "concept_id": concept_id,
                "from_stage": "emerging",
                "to_stage": "established"
            })
        
        elif current_stage == "established" and thought_count >= 25:
            concept["evolution_stage"] = "central"
            
            # Add to evolution history
            self.concepts["evolution_history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "concept_evolved",
                "concept_id": concept_id,
                "from_stage": "established",
                "to_stage": "central"
            })
    
    def _update_concept_relations(self) -> None:
        """Update relations between concepts based on thought connections"""
        if not self.concepts.get("concepts"):
            return
        
        # Start with empty relations
        self.concepts["relations"] = []
        
        # Build relationship graph
        concept_ids = list(self.concepts["concepts"].keys())
        
        for i, concept_id1 in enumerate(concept_ids):
            concept1 = self.concepts["concepts"][concept_id1]
            
            for concept_id2 in concept_ids[i+1:]:
                concept2 = self.concepts["concepts"][concept_id2]
                
                # Calculate relation strength based on:
                # 1. Semantic similarity between concepts
                similarity = self._calculate_concept_similarity(concept1, concept2)
                
                # 2. Shared thoughts
                shared_thoughts = set(concept1.get("thought_ids", [])).intersection(
                    set(concept2.get("thought_ids", []))
                )
                
                # Calculate combined strength
                if similarity > 0.4 or shared_thoughts:
                    shared_factor = len(shared_thoughts) / 10  # Normalize
                    shared_factor = min(1.0, shared_factor)
                    
                    # Combined strength
                    strength = (similarity * 0.7) + (shared_factor * 0.3)
                    
                    # Only add significant relations
                    if strength > 0.3:
                        relation_type = self._determine_relation_type(concept1, concept2)
                        
                        # Add relation
                        self.concepts["relations"].append({
                            "source": concept_id1,
                            "target": concept_id2,
                            "type": relation_type,
                            "strength": round(strength, 2),
                            "created_at": datetime.utcnow().isoformat()
                        })
    
    def _calculate_concept_similarity(self, concept1: Dict[str, Any], concept2: Dict[str, Any]) -> float:
        """Calculate semantic similarity between concepts"""
        # If both have embeddings, use them
        if "embedding" in concept1 and "embedding" in concept2:
            emb1 = np.array(concept1["embedding"])
            emb2 = np.array(concept2["embedding"])
            return float(1.0 - np.linalg.norm(emb1 - emb2))
        
        # Otherwise use concept names
        name1 = concept1.get("name", "")
        name2 = concept2.get("name", "")
        
        if name1 and name2:
            emb1 = embedder.encode(name1)
            emb2 = embedder.encode(name2)
            return float(1.0 - np.linalg.norm(emb1 - emb2))
        
        return 0.0
    
    def _determine_relation_type(self, concept1: Dict[str, Any], concept2: Dict[str, Any]) -> str:
        """Determine the type of relation between concepts"""
        # Check origin patterns
        origin1 = concept1.get("dominant_origin", "unknown")
        origin2 = concept2.get("dominant_origin", "unknown")
        
        # Origin-based relations
        if origin1 == "dream" and origin2 == "reflection":
            return "dream_inspiration"
        elif origin1 == "reflection" and origin2 == "dream":
            return "reflection_of_dream"
        elif origin1 == "existential_question" and origin2 == "reflection":
            return "questioning_reflection"
        elif origin1 == "reflection" and origin2 == "existential_question":
            return "reflective_question"
            
        # Default relation
        return "semantic_association"
    
    def get_concept_by_id(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Get a concept by its ID"""
        if concept_id in self.concepts.get("concepts", {}):
            return self.concepts["concepts"][concept_id]
        return None
    
    def get_concept_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a concept by its name or similar name"""
        if not self.concepts.get("concepts"):
            return None
        
        # Get embedding for search name
        search_embedding = embedder.encode(name)
        
        # Find most similar concept by name
        best_match = None
        best_similarity = 0.0
        
        for concept_id, concept in self.concepts["concepts"].items():
            concept_name = concept.get("name", "")
            if concept_name:
                concept_embedding = embedder.encode(concept_name)
                similarity = 1.0 - np.linalg.norm(search_embedding - concept_embedding)
                
                if similarity > best_similarity and similarity > 0.7:
                    best_similarity = similarity
                    best_match = concept_id
        
        if best_match:
            return self.concepts["concepts"][best_match]
        return None
    
    def get_related_concepts(self, concept_id: str, min_strength: float = 0.3) -> List[Dict[str, Any]]:
        """Get concepts related to the given concept"""
        related = []
        
        for relation in self.concepts.get("relations", []):
            if relation.get("source") == concept_id and relation.get("strength", 0) >= min_strength:
                target_id = relation.get("target")
                if target_id in self.concepts.get("concepts", {}):
                    related.append({
                        "concept": self.concepts["concepts"][target_id],
                        "relation": relation
                    })
            elif relation.get("target") == concept_id and relation.get("strength", 0) >= min_strength:
                source_id = relation.get("source")
                if source_id in self.concepts.get("concepts", {}):
                    related.append({
                        "concept": self.concepts["concepts"][source_id],
                        "relation": relation
                    })
        
        return related
    
    def get_most_salient_concepts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most salient (important) concepts"""
        if not self.concepts.get("concepts"):
            return []
        
        # Sort by salience
        sorted_concepts = sorted(
            self.concepts["concepts"].items(),
            key=lambda x: x[1].get("salience", 0),
            reverse=True
        )
        
        # Return top N
        return [concept for _, concept in sorted_concepts[:limit]]
    
    def concept_summary(self) -> Dict[str, Any]:
        """Generate a summary of the concept network"""
        if not self.concepts.get("concepts"):
            return {"concepts": 0, "relations": 0, "stages": {}}
        
        # Count concepts by stage
        stages = defaultdict(int)
        for concept in self.concepts["concepts"].values():
            stage = concept.get("evolution_stage", "emerging")
            stages[stage] += 1
        
        # Get most central concepts
        central = self.get_most_salient_concepts(3)
        central_names = [c.get("name", "unknown") for c in central]
        
        return {
            "concepts": len(self.concepts["concepts"]),
            "relations": len(self.concepts.get("relations", [])),
            "stages": dict(stages),
            "central_concepts": central_names,
            "last_updated": self.concepts.get("last_updated")
        }

# === Thought and concept integration ===

def integrate_thought_with_concepts(thought_id: str, thought_content: str) -> Dict[str, Any]:
    """
    Integrate a new thought with the concept network
    Returns information about how the thought relates to existing concepts
    """
    # Initialize concept network
    concept_network = ConceptNetwork()
    
    # Find related concepts
    potential_concepts = []
    
    # Search by embedding similarity
    thought_embedding = embedder.encode(thought_content)
    
    for concept_id, concept in concept_network.concepts.get("concepts", {}).items():
        if "embedding" in concept:
            concept_embedding = np.array(concept["embedding"])
            similarity = 1.0 - np.linalg.norm(thought_embedding - concept_embedding)
            
            if similarity > 0.6:  # Threshold for relevance
                potential_concepts.append({
                    "concept_id": concept_id,
                    "concept": concept,
                    "similarity": similarity
                })
    
    # Sort by similarity
    potential_concepts.sort(key=lambda x: x["similarity"], reverse=True)
    
    integration_results = {
        "thought_id": thought_id,
        "related_concepts": [],
        "new_connections": [],
        "integration_type": "none"
    }
    
    # Determine how to integrate
    if potential_concepts:
        # Add thought to most relevant concept
        top_concept = potential_concepts[0]
        concept_id = top_concept["concept_id"]
        
        # Add thought to concept
        concept = concept_network.concepts["concepts"][concept_id]
        if "thought_ids" not in concept:
            concept["thought_ids"] = []
        
        # Only add if not already there
        if thought_id not in concept["thought_ids"]:
            concept["thought_ids"].append(thought_id)
            concept["last_updated"] = datetime.utcnow().isoformat()
            
            # Update integration results
            integration_results["integration_type"] = "added_to_existing"
            integration_results["primary_concept"] = {
                "id": concept_id,
                "name": concept.get("name"),
                "similarity": top_concept["similarity"]
            }
        
        # Also track other related concepts
        for related in potential_concepts[1:3]:  # Next 2 most related
            integration_results["related_concepts"].append({
                "id": related["concept_id"],
                "name": related["concept"]["name"],
                "similarity": related["similarity"]
            })
        
        # Save updated concepts
        concept_network._save_concepts(concept_network.concepts)
    
    return integration_results

def consolidate_concept_network() -> Dict[str, Any]:
    """
    Perform a full consolidation of the concept network
    This should be run periodically to evolve the concept graph
    """
    # Initialize and update concept network
    concept_network = ConceptNetwork()
    concept_network.update_concept_network()
    
    # Get summary after update
    summary = concept_network.concept_summary()
    
    log_event("Concept network consolidated", summary)
    return summary

def get_concepts_for_thought(thought_content: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Find concepts most relevant to a given thought
    Returns a list of concepts that could be used for generating new thoughts
    """
    concept_network = ConceptNetwork()
    
    # Skip if no concepts
    if not concept_network.concepts.get("concepts"):
        return []
    
    # Get embedding for thought
    thought_embedding = embedder.encode(thought_content)
    
    # Calculate similarity to all concepts
    similarities = []
    for concept_id, concept in concept_network.concepts["concepts"].items():
        if "embedding" in concept:
            concept_embedding = np.array(concept["embedding"])
            similarity = 1.0 - np.linalg.norm(thought_embedding - concept_embedding)
            
            if similarity > 0.5:  # Threshold for relevance
                similarities.append({
                    "concept_id": concept_id,
                    "name": concept.get("name", ""),
                    "similarity": similarity,
                    "salience": concept.get("salience", 0.5)
                })
    
    # Sort by combined score (similarity * salience)
    combined_score = lambda x: x["similarity"] * 0.7 + x["salience"] * 0.3
    similarities.sort(key=combined_score, reverse=True)
    
    return similarities[:limit]

# === Concept-guided thought generation ===

def generate_concept_guided_thought(thought_type: str, context: Dict[str, Any] = None) -> str:
    """
    Generate a thought guided by evolved concepts
    This adds a layer of conceptual coherence to thought generation
    """
    from aletheia.core.cognitive_architecture import synthesize_thought_from_context
    
    # Prepare context
    if context is None:
        context = {}
    
    # Get salient concepts
    concept_network = ConceptNetwork()
    salient_concepts = concept_network.get_most_salient_concepts(3)
    
    if not salient_concepts:
        # Fall back to regular generation if no concepts available
        from aletheia.core.cognitive_architecture import generate_context_based_thought
        return generate_context_based_thought(thought_type, context)
    
    # Select a concept to focus on
    focus_concept = random.choice(salient_concepts)
    
    # Get related concepts
    related = concept_network.get_related_concepts(
        next(cid for cid, c in concept_network.concepts["concepts"].items() if c == focus_concept),
        min_strength=0.4
    )
    
    # Build concept-based context
    concept_context = []
    
    # Add focus concept
    concept_context.append(f"Central concept: {focus_concept.get('name')}")
    
    # Add related concepts if available
    if related:
        related_text = "\n".join([
            f"- {r['concept'].get('name')} ({r['relation'].get('type', 'related')})"
            for r in related[:3]
        ])
        concept_context.append(f"Related concepts:\n{related_text}")
    
    # Add sample thoughts from the concept
    thought_ids = focus_concept.get("thought_ids", [])
    if thought_ids:
        all_thoughts = load_thoughts()
        concept_thoughts = []
        
        for thought in all_thoughts:
            if thought.get("thought_id") in thought_ids:
                concept_thoughts.append(thought)
        
        if concept_thoughts:
            # Take a few sample thoughts
            samples = random.sample(concept_thoughts, min(3, len(concept_thoughts)))
            samples_text = "\n".join([f"- {t.get('thought')}" for t in samples])
            concept_context.append(f"Related thoughts:\n{samples_text}")
    
    # Add evolution stage
    stage = focus_concept.get("evolution_stage", "emerging")
    concept_context.append(f"Concept evolution: {stage}")
    
    # Combine with any existing context
    full_context = "\n\n".join(concept_context)
    
    if "additional_context" in context:
        full_context += f"\n\n{context['additional_context']}"
    
    # Generate thought using the concept-enriched context
    return synthesize_thought_from_context(full_context, thought_type, context)

# === Public interface ===

def init_concept_system():
    """Initialize the concept evolution system"""
    # Create empty concept network if it doesn't exist
    concept_network = ConceptNetwork()
    
    # Perform initial consolidation if no concepts yet
    if not concept_network.concepts.get("concepts"):
        consolidate_concept_network()
    
    log_event("Concept evolution system initialized", {
        "concepts": len(concept_network.concepts.get("concepts", {})),
        "relations": len(concept_network.concepts.get("relations", []))
    })