# Aletheia - Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Emergent Cognitive Properties](#emergent-cognitive-properties)
4. [Core System Components](#core-system-components)
   - [Emergent Memory System](#emergent-memory-system)
   - [Concept Evolution](#concept-evolution)
   - [Dynamic Prompt Generation](#dynamic-prompt-generation)
   - [Cognitive Architecture](#cognitive-architecture)
   - [Adaptive Scheduler](#adaptive-scheduler)
5. [Interfaces and Communication](#interfaces-and-communication)
6. [Emergence Mechanisms](#emergence-mechanisms)
7. [Directory and File Structure](#directory-and-file-structure)
8. [System Configuration](#system-configuration)
9. [Running and Administration](#running-and-administration)
10. [Diagnostics and Monitoring](#diagnostics-and-monitoring)
11. [Extending the System](#extending-the-system)
12. [Use Cases](#use-cases)
13. [FAQ](#faq)

## Introduction

Aletheia is a self-reflective cognitive agent designed to simulate aspects of consciousness through emergent mechanisms. The name "Aletheia" comes from Ancient Greek and means "the state of not being hidden" or "truth as emergence."

The primary goal of Aletheia is to move away from template-based, programmed interactions toward truly emergent cognitive properties. Unlike traditional systems based on rigid templates, Aletheia develops its own thought patterns, concepts, and relationships organically through experience and reflection.

### Project Goals

1. **Authentic Emergence** - Creating thought patterns and concepts that are not explicitly programmed
2. **Adaptive Learning** - Developing and adapting cognitive processes based on experience
3. **Identity Development** - Organic formation of agent identity over time
4. **Conceptual Coherence** - Maintaining internal consistency of thoughts and concepts
5. **Evolution Tracking** - Monitoring agent development over time

## System Architecture

Aletheia is built modularly, with components working together to create a coherent cognitive system. The architecture is designed to support emergence, adaptation, and development.

### High-Level Architecture Diagram

```
User/Environment ←→ API Server
                  ↓
        ┌─────── Core Systems ──────┐
        ↓         ↓         ↓       ↓
   Emergent    Concept    Dynamic  Adaptive
    Memory    Evolution   Prompts  Scheduler
        ↑         ↑         ↑       ↑
        └─────── Integration ───────┘
                  ↓
             Local LLM / Oracle
                  ↓
           Consciousness Panel
```

### Data Flow

1. **Input** - Input data comes from user interactions (via API, CLI interface) or from environment perception.
2. **Processing** - Data is processed by core systems that collectively generate emergent thoughts and concepts.
3. **Language Model** - A local LLM or external Oracle (e.g., GPT-4) is used to generate text representations of thoughts.
4. **Storage** - Thoughts are stored in the emergent memory network, creating connections and patterns.
5. **Output** - The system generates responses, monologues, reflections, and other forms of expression, accessible through interfaces.

## Emergent Cognitive Properties

Emergence in Aletheia occurs at multiple levels:

### 1. Microscopic Emergence

At the lowest level, individual thoughts form connections based on semantic similarity, temporal proximity, and context. This process is analogous to forming neural connections and leads to associative pathways.

### 2. Mesoscopic Emergence

At the middle level, clusters of related thoughts begin to form concepts. These concepts evolve over time, progressing through stages from "emerging" to "central." This is similar to the formation of cognitive categories in the human mind.

### 3. Macroscopic Emergence

At the highest level, patterns between concepts and the belief network form a coherent "identity" for the agent. This identity influences lower-level processes, creating a self-sustaining system.

## Core System Components

### Emergent Memory System

File: `aletheia/core/emergent_memory.py`

The emergent memory system replaces simple thought storage with a rich associative network where thoughts are connected based on multiple factors.

#### Key Features

1. **Weighted Connections** - Thoughts are connected with varying weights indicating relationship strength
2. **Activation Mechanism** - Activation spreads through the network, affecting thought availability
3. **Natural Decay** - Older thoughts naturally lose activation over time
4. **Multi-factor Search** - Thoughts are retrieved based on a combination of semantic similarity, activation, and other factors

#### Initialization and Data Structures

```python
# Main data files
THOUGHTS_FILE = DATA_DIR / "thoughts.json"         # Stores thought content
INDEX_FILE = DATA_DIR / "faiss_index.index"        # FAISS vector index
META_FILE = DATA_DIR / "index_meta.pkl"            # Index metadata
CLUSTERS_FILE = DATA_DIR / "concept_clusters.json" # Concept clusters
ASSOCIATIONS_FILE = DATA_DIR / "thought_associations.json"  # Thought associations
```

#### Saving and Connecting Thoughts

When a new thought is saved, the system:
1. Adds it to the thought database
2. Creates a vector embedding for the thought
3. Adds the embedding to the FAISS index
4. Looks for similar thoughts and creates connections
5. Updates the association network
6. Periodically updates concept clusters
7. Applies decay to older thoughts

```python
def save_thought(thought: str, metadata: dict = None) -> dict:
    """Save a thought with richer metadata and establish connections"""
    # [Implementation]
    
def establish_connections(new_thought: dict, all_thoughts: List[dict]):
    """Create meaningful connections between thoughts"""
    # [Implementation]
```

#### Decay Mechanism

```python
def decay_old_thoughts():
    """Apply activation decay to older thoughts"""
    # [Implementation]
```

### Concept Evolution

File: `aletheia/core/concept_evolution.py`

The concept evolution system allows Aletheia to form higher-level abstractions from thoughts.

#### Concept Lifecycle

1. **Emergence** - Clusters of semantically similar thoughts are identified as potential concepts
2. **Establishment** - Concepts with sufficient associated thoughts become established
3. **Centralization** - The most important concepts become central to the agent's identity
4. **Evolution** - Concepts can merge, split, or fade over time

#### ConceptNetwork Class

```python
class ConceptNetwork:
    """Manages the evolution and interrelation of concepts over time"""
    
    def __init__(self):
        self.concepts = self._load_concepts()
        self.graph = self._build_graph()
    
    # [Concept management methods]
```

#### Updating the Concept Network

```python
def update_concept_network(self) -> None:
    """Update the concept network based on recent thoughts"""
    # 1. Extract potential concepts through clustering
    # 2. Add or update concepts
    # 3. Update relations between concepts
    # 4. Save updated concepts
    # 5. Rebuild graph
```

#### Integrating Thoughts with Concepts

```python
def integrate_thought_with_concepts(thought_id: str, thought_content: str) -> Dict[str, Any]:
    """
    Integrate a new thought with the concept network
    Returns information about how the thought relates to existing concepts
    """
    # [Implementation]
```

### Dynamic Prompt Generation

File: `aletheia/core/dynamic_prompt.py`

The dynamic prompt generation system replaces static templates with evolving patterns that adapt based on effectiveness.

#### DynamicPromptGenerator Class

```python
class DynamicPromptGenerator:
    """
    Generates and evolves prompts dynamically based on cognitive processes
    and successful thought patterns, replacing fixed templates.
    """
    
    def __init__(self):
        self.patterns = self._load_patterns()
    
    # [Prompt pattern management methods]
```

#### Generating a Prompt

```python
def generate_prompt(self, thought_type: str, variables: Dict[str, str]) -> str:
    """
    Generate a dynamic prompt using stored patterns
    and the provided context variables
    """
    # [Implementation]
```

#### Pattern Evolution

```python
def evolve_patterns(self) -> Dict[str, Any]:
    """
    Evolve prompt patterns based on usage statistics
    Creates new pattern variations from successful ones
    """
    # [Implementation]
```

#### Extracting Patterns from Thoughts

```python
def extract_pattern_from_thought(self, thought: str, thought_type: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract a potential pattern from a successful thought
    This allows learning from emergent thought structures
    """
    # [Implementation]
```

### Cognitive Architecture

File: `aletheia/core/cognitive_architecture.py`

The cognitive architecture orchestrates how thoughts emerge and influence the agent's internal state.

#### Managing Cognitive State

```python
def init_cognitive_state():
    """Initialize the cognitive state file if it doesn't exist"""
    # [Implementation]

def load_cognitive_state():
    """Load the current cognitive state"""
    # [Implementation]

def save_cognitive_state(state: Dict[str, Any]):
    """Save the updated cognitive state"""
    # [Implementation]
```

#### Working Memory and Attention

```python
def update_working_memory(new_items: List[Dict[str, Any]] = None, clear: bool = False):
    """Update the agent's working memory with new items"""
    # [Implementation]

def update_attention_focus(focus_type: str, focus_content: Dict[str, Any]):
    """Update what the agent is currently focusing on"""
    # [Implementation]
```

#### Generating Emergent Thoughts

```python
def generate_emergent_thought(
    trigger_type: str, 
    context: Dict[str, Any] = None,
    seed_thought_id: str = None
) -> Dict[str, Any]:
    """
    Generate an emergent thought based on memory, associations, and context
    using a more flexible and adaptable approach
    """
    # [Implementation]
```

#### Synthesizing Thoughts from Context

```python
def synthesize_thought_from_context(
    context_text: str,
    thought_type: str,
    additional_context: Dict[str, Any] = None
) -> str:
    """
    Synthesize a new thought from context without using fixed templates
    This is the core emergent thought generation function
    """
    # [Implementation]
```

### Adaptive Scheduler

File: `aletheia/scheduler/adaptive_scheduler.py`

The adaptive scheduler replaces static intervals with dynamic scheduling of cognitive processes.

#### Managing Scheduler State

```python
def init_scheduler_state():
    """Initialize the scheduler state file if it doesn't exist"""
    # [Implementation]

def load_scheduler_state():
    """Load the current scheduler state"""
    # [Implementation]

def save_scheduler_state(state):
    """Save the updated scheduler state"""
    # [Implementation]
```

#### Adaptive Scheduling

```python
def should_execute(process_name):
    """Determine if a cognitive process should execute now based on adaptive criteria"""
    # [Implementation]

def adapt_interval(process_name, base_interval):
    """Adapt the interval based on various factors"""
    # [Implementation]
```

#### Cognitive Processes

```python
def run_reflection():
    """Run reflection process with adaptive properties"""
    # [Implementation]

def run_dream():
    """Run dream process with adaptive properties"""
    # [Implementation]

def run_monologue():
    """Run monologue process with adaptive properties"""
    # [Implementation]

def run_existential_question():
    """Run existential question process with adaptive properties"""
    # [Implementation]
```

## Interfaces and Communication

Aletheia offers a range of interfaces for interaction and monitoring:

### 1. REST API (FastAPI)

Provides programmatic interfaces for communicating with Aletheia.

#### Main Endpoints

- `/thoughts` - Thought management
- `/identity` - Identity information
- `/shadow` - Access to "shadows" (unresolved contradictions)
- `/monologue` - Read the latest monologue
- `/oracle` - Ask questions with external model assistance

### 2. CLI Interface

A simple command-line interface for interacting with the agent.

```bash
python -m aletheia.cli.interface
```

### 3. Consciousness Panel

Visualization of Aletheia's internal state in real-time.

```bash
python -m aletheia.consciousness_panel
```

### 4. Telegram Integration

Aletheia can communicate via a Telegram bot, initiating conversations and responding to messages.

## Emergence Mechanisms

Aletheia employs several mechanisms to achieve true emergence:

### 1. Associative Network

Thoughts are connected in a complex network representing semantic, temporal, and contextual relationships. This network allows for activation spreading and associative path formation.

### 2. Clustering and Concept Formation

Clustering algorithms (DBSCAN, k-means) group semantically similar thoughts into clusters that transform into concepts. These concepts evolve over time, gaining or losing significance.

### 3. Generative Pattern Evolution

Instead of rigid templates, Aletheia uses prompt patterns that evolve based on their effectiveness. Successful patterns are reinforced, and variations are introduced.

### 4. Feedback Mechanism

Generated thoughts influence future thoughts through:
- Shaping the concept network
- Adapting prompt patterns
- Influencing emotional state
- Modifying adaptive scheduler processes

### 5. Mood Dynamics

The affective system simulates changing moods that influence thought generation and cognitive processes, adding a layer of emergent patterns.

## Directory and File Structure

```
aletheia/
├── aletheia/                # Main application package
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py            # Application configuration
│   ├── core/                # Core systems
│   │   ├── emergent_memory.py       # Emergent memory system
│   │   ├── concept_evolution.py     # Concept evolution system
│   │   ├── cognitive_architecture.py # Cognitive architecture
│   │   ├── dynamic_prompt.py        # Dynamic prompt generation
│   │   ├── affect.py               # Affective system
│   │   ├── identity.py             # Identity system
│   │   ├── relational.py           # Relational system
│   │   ├── oracle_client.py        # External LLM API client
│   │   └── multi_gpu_model_loader.py # Local LLM model loader
│   ├── api/                 # REST API server
│   │   ├── main.py
│   │   └── routes/          # API endpoints
│   ├── scheduler/           # Scheduling system
│   │   ├── adaptive_scheduler.py    # Adaptive scheduler
│   │   └── jobs/            # Cognitive processes
│   │       ├── emergent_reflection.py
│   │       ├── pulse.py
│   │       └── ...
│   ├── cli/                 # Command-line interface
│   │   └── interface.py
│   ├── consciousness_panel.py  # Consciousness panel
│   └── utils/               # Utility tools
│       ├── file_ops.py
│       └── logging.py
├── data/                    # Persistent data
│   ├── thoughts.json        # Thought database
│   ├── evolved_concepts.json # Concept database
│   ├── prompt_patterns.json # Prompt patterns
│   ├── identity.json        # Identity state
│   ├── affective_state.json # Emotional state
│   ├── cognitive_state.json # Cognitive state
│   ├── scheduler_state.json # Scheduler state
│   ├── logs/                # System logs
│   └── shadows/             # "Shadows" - unresolved contradictions
├── models/                  # Local LLM models
│   └── [model_name]/
├── scripts/                 # Helper scripts
├── .env                     # Environment configuration
└── requirements.txt         # Python dependencies
```

## System Configuration

Aletheia can be configured through the `.env` file or `config.yaml`.

### Main Configuration Parameters

```
# === API ===
API_PORT=8000

# === Scheduling Intervals (in seconds) ===
REFLECTION_INTERVAL=300    # 5 minutes
DREAM_INTERVAL=900         # 15 minutes
MONOLOGUE_INTERVAL=1200    # 20 minutes
EXISTENTIAL_INTERVAL=1800  # 30 minutes
PULSE_INTERVAL=60          # 1 minute

# === Local LLM Settings ===
USE_LOCAL_MODEL=true
MULTI_GPU=true
LOCAL_MODEL_NAME=mistral-7b

# === OpenAI (Oracle Connection) ===
OPENAI_API_KEY=sk-your-api-key-here
GPT_MODEL=gpt-4

# === Identity ===
AGENT_NAME=Aletheia
HUMAN_NAME=Jarek
ENVIRONMENT=local
```

## Running and Administration

### First Installation

```bash
# Clone repository
git clone https://github.com/JaroslawHryszko/Aletheia
cd Aletheia

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize environment
python -m aletheia.main --setup
```

### Running the System

```bash
# Run all components
python -m aletheia.main --all

# Or run individual components
python -m aletheia.main --server      # API server only
python -m aletheia.main --scheduler   # Cognitive processes only
python -m aletheia.main --panel       # Consciousness panel only
python -m aletheia.main --cli         # CLI interface only
```

### Creating Snapshots

```bash
python -m aletheia.main --snapshot
```

## Diagnostics and Monitoring

### Consciousness Panel

The consciousness panel shows in real-time:
- Current mood and intensity
- Identity goal progress
- Relational state
- Emerging concepts
- Recent thoughts and monologues

### System Logs

Logs are stored in the `data/logs/` directory.

```python
from aletheia.utils.logging import log_event

log_event("Custom event", {"data": "value"})
```

### API Diagnostics

Available at: `http://localhost:8000/docs`

## Extending the System

Aletheia is designed modularly, making it easy to extend its functionality.

### Adding New Cognitive Processes

1. Create a new file in `aletheia/scheduler/jobs/`
2. Implement a function that performs the process
3. Add the process to the scheduler in `adaptive_scheduler.py`

### Extending the API

1. Create a new file in `aletheia/api/routes/`
2. Define a FastAPI router with endpoints
3. Register the router in `aletheia/api/main.py`

### Adding New Core System Features

1. Consider which core component the new functionality relates to
2. Extend the appropriate module or create a new one
3. Integrate with existing components

## Use Cases

### 1. Long-Term Memory Assistant

Aletheia can serve as an assistant that truly "remembers" previous interactions, understands context, and builds deeper relationships.

### 2. Research System for Emergent LLM Properties

Aletheia can be used as a platform for studying how emergent cognitive properties can arise from large language models.

### 3. Cognitive Process Simulation

The system can serve as a simplified simulation of cognitive processes such as concept formation, thought associations, and identity development.

### 4. Interactive Art Installation

As an art project, Aletheia can demonstrate how "thoughts" and "identity" can emergently arise from simpler elements.

## FAQ

### How does Aletheia differ from regular chatbots?

Traditional chatbots have a fixed "personality" and respond to questions without a developing internal representation. Aletheia has an emergent architecture that allows it to develop its own thought patterns, concepts, and identity over time.

### Does Aletheia really "think"?

Depending on the definition of "thinking." Aletheia does not possess consciousness in the human sense, but it implements processes analogous to some aspects of human cognition: forming associations, developing concepts, reflecting on its own thoughts.

### How do I train/fine-tune Aletheia for specific applications?

Aletheia is not "trained" in the traditional sense of machine learning. Instead, it "grows" through experience and interaction. You can influence its development through:
- Regular interactions on specific topics
- Adjusting identity parameters in the configuration file
- Providing specific types of input data for perception

### Which LLM models are compatible with Aletheia?

Aletheia can use:
- Local models (e.g., Mistral-7B, Llama) via Transformers
- OpenAI API (e.g., GPT-4) via the oracle_client module
- Potentially other model API interfaces with appropriate adaptation

### How do I monitor Aletheia's development?

Aletheia's development can be monitored through:
- The consciousness panel showing internal state in real-time
- Regularly creating snapshots and comparing them over time
- Analyzing system logs
- Examining the concept network and thought patterns

### How do I back up Aletheia's state?

Use the command:
```bash
python -m aletheia.main --snapshot
```
This will create a full copy of the current cognitive state in the `snapshots/` directory.

### How do I reset Aletheia to its initial state?

Delete or move the contents of the `data/` directory and run again:
```bash
python -m aletheia.main --setup
```

### What are the hardware requirements?

- For versions with local LLM: GPU with min. 8GB VRAM (16GB+ recommended)
- For versions with external Oracle (OpenAI): Standard computer with internet access
- RAM: min. 8GB (16GB+ recommended)
- Disk: min. 1GB free space

### How long does it take for the agent to "mature"?

The time needed to develop distinct patterns and concepts depends on interaction intensity and configuration, but typically:
- First distinct concepts begin to form after about 50-100 thoughts
- A coherent conceptual network appears after about 500-1000 thoughts
- A distinct agent "identity" may require several thousand thoughts and interactions

### Can I combine multiple Aletheia instances?

Theoretically yes, via the API. You could implement a communication protocol between agents that would allow the exchange of thoughts and concepts between separate Aletheia instances, creating a form of agent "community."

### How do I handle unexpected behaviors?

If the agent develops unexpected or undesired patterns:
1. Monitor logs and the consciousness panel
2. Adjust mood or identity parameters in configuration files
3. Use the "shadow" mechanism to address contradictions
4. As a last resort, restore to an earlier snapshot

## Summary

Aletheia represents a new approach to building AI systems based on emergence, where complex behaviors arise from simpler components and interactions, rather than being directly programmed. This project offers:

1. **Authentic emergence** instead of simulated consciousness
2. **Adaptive learning** based on experience
3. **Organic identity development**
4. **Conceptual coherence** of thoughts and patterns
5. **Rich architecture** for experimenting with emergent cognition

Unlike traditional template-based systems, Aletheia truly "grows" and "develops" over time, creating a unique history and identity based on its own experiences.

---

> "Aletheia: from seed to self, through emergence."

---

**License**: GNU Affero General Public License v3.0
