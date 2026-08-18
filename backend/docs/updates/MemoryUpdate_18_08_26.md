Design and implement a modular memory system for CIEL.

The goal is to make CIEL's memory behave more like human memory instead of simply saving every conversation and running vector search over it.

CIEL should have multiple types of memory, each with a different purpose.

## 1. Working Memory

Working memory is temporary context for the current task or conversation.

It should contain things such as:

* Recent conversation messages
* Current user request
* Current task state
* Tool outputs
* Router decisions
* Memories retrieved for the current request
* Temporary variables and intermediate state

Working memory should primarily live in RAM and should not automatically be persisted.

It should be cleared or reduced when a task/session finishes.

---

## 2. Episodic Memory

Episodic memory stores things that happened in previous interactions.

Examples:

* A discussion about redesigning the CIEL router
* A bug that was fixed
* A decision made about a project
* A previous troubleshooting session
* A significant user event or experience

Use a vector database for retrieval because episodic memories will often be searched semantically rather than by exact keywords.

Do not permanently embed every raw message as an independent memory.

Instead, preserve raw conversations separately and periodically convert meaningful groups of messages into concise "episodes".

An episode should contain data such as:

* Unique ID
* Timestamp
* Session ID
* Summary
* Topics
* Related project
* Importance score
* Source message IDs
* Access count
* Last accessed time
* Memory strength

The text summary of the episode should be embedded into the vector database.

SQLite should remain the source of truth. The vector database should act as a semantic retrieval index that can be rebuilt from SQLite if necessary.

---

## 3. Semantic Memory

Semantic memory stores stable facts that CIEL knows.

Examples:

* CIEL is written in Python
* A project uses a certain framework
* The user prefers a certain tool
* A project currently has a particular architecture
* A person's relationship to another entity
* Configuration information

These facts should be stored structurally in SQLite rather than relying entirely on vector search.

Represent facts approximately as:

* id
* subject
* predicate
* object
* confidence
* source
* created_at
* updated_at
* valid_from
* valid_until
* status

Example:

subject = "CIEL Router"

predicate = "uses_model"

object = "Gemma2:9b"

Do not blindly overwrite facts when they change.

Support historical facts using validity dates.

For example, if CIEL previously used one model and later changes to another model, preserve both facts and mark when each one was valid.

This allows CIEL to answer both:

"What model does CIEL currently use?"

and:

"What model was CIEL using six months ago?"

---

## 4. Entity and Relationship Memory

CIEL should maintain a lightweight knowledge graph.

Do not introduce a dedicated graph database initially. SQLite is sufficient.

Create an `entities` system where important things can have persistent identities.

Examples of entity types:

* Person
* Project
* Application
* Tool
* Programming language
* Device
* Service
* Repository
* Organisation

Then create relationships between entities.

Examples:

Ali -> develops -> CIEL

CIEL -> uses -> Python

CIEL -> contains -> Router

CIEL -> integrates_with -> LifeOS

Router -> uses -> Model

Suggested tables:

entities:

* id
* type
* name
* description
* created_at
* updated_at

relationships:

* id
* source_entity_id
* relation
* target_entity_id
* confidence
* source
* created_at
* valid_from
* valid_until

The purpose of this layer is to give CIEL structured understanding of how known things relate to each other.

---

## 5. Procedural Memory

Procedural memory stores reusable knowledge about how to perform tasks.

Examples:

* How to safely deploy a project
* How the user normally creates a Python project
* How to back up a database
* How to run a specific development workflow
* How to solve a recurring problem

A procedure should contain:

* id
* name
* description
* trigger or conditions
* steps
* related entities/projects
* success count
* failure count
* confidence
* last used
* created_at
* updated_at

Store procedure steps as structured JSON where appropriate.

Procedural memory should later be able to improve through usage.

If a procedure succeeds repeatedly, increase its confidence.

If it repeatedly fails, lower its confidence or flag it for review.

---

## 6. Memory Manager

Create a central `MemoryManager`.

The main LLM and router should not directly manipulate individual databases.

The intended architecture is:

User
→ Main LLM
→ Router / Coordinator
→ MemoryManager
→ Individual memory systems

The MemoryManager should provide a clean API such as:

* remember()
* recall()
* retrieve_context()
* consolidate()
* reinforce()
* forget()
* resolve_conflicts()

Internally it should coordinate:

* WorkingMemory
* EpisodicMemory
* SemanticMemory
* EntityMemory
* ProceduralMemory

Suggested conceptual structure:

```python
class MemoryManager:
    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.entities = EntityMemory()
        self.procedural = ProceduralMemory()

    def remember(self, data):
        ...

    def recall(self, query):
        ...

    def retrieve_context(self, request):
        ...

    def consolidate(self):
        ...

    def reinforce(self, memory_id):
        ...

    def forget(self):
        ...
```

Keep each memory subsystem modular so storage technologies can be replaced later without rewriting the entire system.

---

## 7. Memory Classification

Every interaction should not automatically become permanent memory.

After or during an interaction, a memory analysis process should determine whether useful information exists.

Classify information into categories such as:

* Episodic
* Semantic fact
* Preference
* Project update
* Entity
* Relationship
* Procedure
* Temporary information
* Irrelevant / do not store

For example, if the user says:

"I changed CIEL's router from model A to model B because model B handles structured JSON better."

The memory system may extract:

Semantic memory:

CIEL Router -> uses_model -> Model B

Project update:

router model changed from Model A to Model B

Episodic memory:

The user changed the router model because Model B provided better structured JSON reliability.

The system should be capable of storing multiple memory types from one interaction.

---

## 8. Memory Retrieval

Do not simply run the current user message through vector search and inject the top results.

Create a retrieval stage that decides which memory systems are relevant.

Example request:

"Why did I change CIEL's router model?"

The retrieval system might decide to query:

* Semantic memory for the current router model
* Episodic memory for previous model-change discussions
* Project memory/entity context for CIEL Router

The results should then be combined into a compact context object for the LLM.

For example:

```text
Relevant memory context:

Current router model:
Model B

Relevant episode:
The router was changed from Model A to Model B because Model B produced more reliable structured JSON.

Related project:
CIEL

Related component:
Router
```

Avoid injecting large amounts of irrelevant memory into the context window.

---

## 9. Memory Scoring and Forgetting

Not every memory should remain equally important forever.

Each episodic memory should have values such as:

* importance
* recency
* retrieval frequency
* access count
* last accessed
* confidence
* memory strength

Use these values when ranking retrieval results.

A possible conceptual score is:

```text
memory_score =
    semantic_relevance
    × importance
    × recency_factor
    × reinforcement_factor
```

The exact formula can evolve later.

Low-value memories should not necessarily be immediately deleted.

Use a lifecycle such as:

Raw interaction
→ Episode
→ Compressed summary
→ Archived
→ Optional deletion

Important and frequently recalled memories should remain easier to retrieve.

---

## 10. Memory Reinforcement

Whenever a stored memory is successfully used, reinforce it.

For example:

* Increase access count
* Update last accessed
* Slightly increase memory strength
* Optionally record that the memory contributed to a successful response

This should make frequently useful knowledge easier to retrieve over time.

---

## 11. Memory Consolidation

Implement a consolidation system.

The purpose is to convert repeated experiences into higher-level knowledge.

For example, multiple episodic memories might show that the user repeatedly prefers:

* Reversible system changes
* Modular configurations
* Easy rollback
* Isolated environments

The consolidation system may eventually create a semantic preference such as:

"The user prefers system configurations that are modular, reversible, and isolated."

Consolidation should:

1. Find related episodic memories
2. Look for repeated patterns
3. Determine whether a stable fact, preference, relationship, or procedure can be inferred
4. Store the derived memory with appropriate confidence
5. Preserve links back to the source episodes

Do not delete the original episodes just because a consolidated fact was created.

---

## 12. Contradiction Handling

Memory must support changing information.

Never assume an existing fact is permanently correct.

When a new fact contradicts an existing active fact:

1. Compare confidence and source
2. Determine whether the information represents a change over time
3. Mark the old fact as no longer current if appropriate
4. Add the new fact
5. Preserve both historically

Each memory should maintain provenance.

CIEL should know whether information came from:

* Explicit user statement
* CIEL inference
* Tool output
* Project files
* LifeOS
* External API
* Previous conversation
* Another trusted source

Explicit user statements and authoritative live sources should generally have higher confidence than inferred memories.

---

## 13. LifeOS and External Sources

Do not copy all LifeOS data into CIEL's permanent memory.

LifeOS should remain an external authoritative source for information that changes frequently.

Examples:

* Current tasks
* Current habits
* Current project state
* Finance data
* Journal entries
* Current goals

CIEL may remember that the information exists and where to retrieve it, but should query LifeOS when current truth is required.

Distinguish between:

Memory = what CIEL has learned

Source = where CIEL can retrieve authoritative current information

For example:

CIEL may remember:

"The user's habit tracking is stored in LifeOS."

But should query LifeOS rather than permanently remembering:

"The user's current gym streak is 8 days."

This prevents stale memory.

---

## 14. Storage Technology

For the initial implementation use:

### SQLite

Use SQLite as the canonical persistent database.

Suggested responsibilities:

* Raw conversations
* Sessions
* Facts
* Preferences
* Projects
* Entities
* Relationships
* Procedures
* Episodic memory metadata
* Provenance
* Memory scores
* Source references

Use either Python's built-in `sqlite3` module or SQLAlchemy if the additional abstraction is useful.

Do not require a network database server.

### Vector Database

Initially use Chroma or another local vector database.

Its role is semantic retrieval, primarily for episodic memory and optionally document/project memory.

It should not be the canonical source of truth.

All vector records should reference persistent SQLite memory IDs.

If the vector database is deleted or corrupted, CIEL should eventually be capable of rebuilding it from SQLite.

### Embeddings

Use a local embedding model where possible.

Abstract embedding generation behind an interface so the model can be changed later.

Example:

```python
class EmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        ...
```

Do not couple the rest of the memory system directly to one embedding model.

---

## 15. Suggested Code Structure

Use a modular structure similar to:

```text
src/
└── memory/
    ├── manager.py
    ├── working.py
    ├── episodic.py
    ├── semantic.py
    ├── entities.py
    ├── procedural.py
    ├── retrieval.py
    ├── consolidation.py
    ├── scoring.py
    ├── classifier.py
    ├── schemas.py
    │
    ├── database/
    │   ├── sqlite.py
    │   ├── models.py
    │   └── migrations/
    │
    └── vector/
        ├── store.py
        └── embeddings.py
```

Avoid giant classes.

Each module should have one clear responsibility.

---

## 16. Router Integration

CIEL's existing router currently has memory-related decisions.

Do not make the router responsible for deciding every memory detail.

The router should make high-level decisions such as:

* Does this task require memory retrieval?
* Could this interaction contain durable information?
* Which broad memory scopes may be relevant?

Then delegate detailed classification and storage to the MemoryManager.

Instead of treating memory as only:

```json
{
    "doRemember": true
}
```

move toward something conceptually similar to:

```json
{
    "memory": {
        "retrieve": true,
        "evaluate_for_storage": true,
        "scopes": [
            "episodic",
            "semantic",
            "project"
        ]
    }
}
```

Do not necessarily implement this exact schema immediately if it would break the existing router. Preserve compatibility where useful and migrate incrementally.

---

## 17. Implementation Order

Do not attempt to build the complete advanced system at once.

Implement it incrementally.

### Stage 1

Create SQLite-backed conversation/session persistence.

### Stage 2

Add episodic memory and vector retrieval.

### Stage 3

Add structured semantic facts and preferences.

### Stage 4

Add entities and relationships.

### Stage 5

Add automatic memory classification and extraction.

### Stage 6

Add multi-source retrieval and context assembly.

### Stage 7

Add scoring, reinforcement, and memory decay.

### Stage 8

Add consolidation of episodes into stable facts/preferences.

### Stage 9

Add procedural memory.

### Stage 10

Add more advanced contradiction resolution and temporal reasoning.

Prioritise a clean foundation over implementing every advanced feature immediately.

---

## Core Design Principles

Follow these rules throughout the implementation:

1. SQLite is the persistent source of truth.
2. Vector search is a retrieval mechanism, not truth storage.
3. Raw conversation history and durable memory are separate concepts.
4. Not every message deserves permanent memory.
5. Memory should preserve provenance.
6. Facts must be able to change over time.
7. Relevant memories should be retrieved selectively.
8. Frequently useful memories should become stronger.
9. Low-value memories should gradually compress or decay.
10. Repeated experiences should eventually form semantic knowledge.
11. Live external systems such as LifeOS should remain authoritative for rapidly changing data.
12. Storage implementations should be replaceable behind clean interfaces.
13. Avoid introducing unnecessary infrastructure such as PostgreSQL, Redis, Neo4j, or distributed vector databases at the current scale.
14. Build the memory system in small, testable stages.
15. Existing CIEL functionality should continue working while memory is introduced.

The end goal is a memory system where CIEL can distinguish between:

* What is happening right now
* What happened previously
* What it knows as a fact
* How known entities relate to each other
* How to perform learned tasks
* Which information is current
* Which information is historical
* Which memories are important
* Which memories are unreliable
* Where each memory originally came from

Do not start implementation by creating everything at once. First inspect the existing CIEL repository and architecture, identify where the memory system integrates with the router/coordinator/conversation flow, and propose the minimal Stage 1 and Stage 2 changes before making large architectural modifications.