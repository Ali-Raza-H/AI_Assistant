# CIEL Brain Architecture Redesign

## Objective

Redesign CIEL's core runtime architecture so that CIEL itself becomes the central reasoning and decision-making component of the system.

The current implementation is effectively router-first:

```text
User Message
→ Controller
→ Router
→ Tool Manager
→ Tools
→ CIEL Response Model
→ possibly repeat
→ Final Response
```

The Router currently decides which tools to use, whether another cycle should occur, and whether controller-cycle history should be carried forward. CIEL itself only receives the request after routing and tool execution have already happened. The existing controller then repeats the Router → Tools → CIEL sequence for up to five iterations.

This architecture worked when CIEL was primarily a tool-using assistant, but it becomes restrictive as CIEL gains:

* Long-term memory
* Working memory
* Planning
* Context management
* Project awareness
* Multi-step reasoning
* More tools
* Specialist capabilities
* Better failure recovery
* More autonomous behaviour

The redesigned architecture should therefore move cognitive responsibility away from the Router and into a central **CIEL Brain**.

The primary architectural principle is:

> CIEL decides what needs to happen.
> The Controller manages execution.
> Memory provides context.
> The Router translates intentions into valid tool calls.
> The Tool Manager executes those calls.
> Tool results become observations that return to CIEL.

The Router should no longer control CIEL's reasoning loop.

---

# 1. Core Mental Model

The new architecture should revolve around a continuous cognitive cycle:

```text
THINK
→ ACT
→ OBSERVE
→ THINK
→ ACT
→ OBSERVE
→ ...
→ COMPLETE
→ RESPOND
```

CIEL owns this cycle.

The system should therefore conceptually operate as:

```text
User
↓
Controller
↓
Context Engine
↓
Memory Retrieval
↓
CIEL Brain
↓
Decision
├── Action required → Router → Tool Manager → Observation → CIEL Brain
├── More memory required → Memory Manager → CIEL Brain
├── User input required → Return clarification request
└── Complete → Response Generator
↓
Memory Evaluation
↓
Memory Commit
↓
User
```

This architecture deliberately separates **thinking** from **execution**.

---

# 2. Controller

The Controller remains the highest-level runtime orchestrator, but it should stop making cognitive decisions.

The Controller does not reason about what the user wants.

It does not decide which tool is appropriate.

It does not decide what information is important.

It does not decide what should enter long-term memory.

Its responsibility is to manage the lifecycle of an interaction.

The Controller should be responsible for:

* Creating an interaction
* Assigning an interaction ID
* Creating interaction-local state
* Maintaining iteration limits
* Calling the Context Engine
* Calling the CIEL Brain
* Dispatching requested actions
* Returning observations to the Brain
* Detecting completion states
* Handling failures
* Publishing runtime events
* Persisting the final conversation
* Triggering post-interaction memory processing
* Cleaning up temporary state

Conceptually:

```python
def run_interaction(user_message):
    context = create_interaction_context(user_message)

    retrieve_initial_context(context)

    while not context.finished:
        decision = brain.think(context)

        process_decision(decision, context)

    persist_interaction(context)
    evaluate_memory(context)

    return context.final_response
```

The Controller should be intentionally boring.

That is desirable.

Complex intelligence should live in the Brain and its supporting systems rather than becoming hard-coded into orchestration logic.

---

# 3. Interaction Context

The current system uses process-global flags such as:

```text
isLooping
doRemember
```

These should eventually be removed from the cognitive architecture.

The current report confirms that these flags are mutable global class state and are safe largely because controller executions are serialized.

Instead, every user interaction should receive its own `InteractionContext`.

This becomes the temporary state container representing everything CIEL currently knows about this interaction.

Conceptually:

```python
InteractionContext:
    interaction_id
    session_id
    user_message

    iteration
    status

    conversation_context
    working_memory
    retrieved_memories

    actions
    observations

    current_plan
    memory_candidates

    final_response

    started_at
    completed_at
```

The Context belongs to exactly one interaction.

It should not be shared globally.

This means that future concurrency becomes significantly easier because cognitive state is isolated.

---

# 4. Working Memory

Working memory represents CIEL's temporary awareness during the current task.

It should contain information required to continue solving the current problem without permanently storing everything.

Examples include:

* Current user request
* Relevant recent conversation turns
* Retrieved long-term memories
* Current task objective
* Current plan
* Actions already attempted
* Tool results
* Normalized observations
* Temporary conclusions
* Files currently being examined
* Errors encountered
* Intermediate state

For example:

```text
User objective:
Fix CIEL startup failure.

Actions:
1. Started CIEL.
2. Startup failed.
3. Inspected pyproject.toml.

Observations:
1. ImportError references package X.
2. Package X is missing from dependencies.

Current objective:
Determine the correct dependency and repair configuration.
```

This context exists while the task is being performed.

Working memory and long-term memory must remain separate concepts.

Working memory answers:

> What does CIEL need to remember right now?

Long-term memory answers:

> What should CIEL still know in future interactions?

---

# 5. Context Engine

Introduce a Context Engine responsible for constructing the information presented to the Brain.

The Brain should not independently load arbitrary history files, databases, memories and application state.

Instead:

```text
Brain
↑
Context Engine
↑
Memory + session + external sources
```

The Context Engine should assemble a compact `BrainContext`.

Sources may include:

* System identity/instructions
* Current user message
* Recent conversation messages
* Working memory
* Relevant long-term memories
* Relevant project information
* Current observations
* Current plan
* Available capabilities
* External-source metadata

The Context Engine must protect the model from excessive context.

It should not blindly insert:

* Entire chat history
* Entire project histories
* Every memory retrieved by vector search
* Every previous tool result
* Large raw terminal outputs

Instead, context should be selected and compressed according to relevance.

---

# 6. Pre-Reasoning Memory Retrieval

Long-term memory retrieval should happen before CIEL begins reasoning.

For example, suppose the user says:

```text
Can you fix that router problem we found yesterday?
```

The Brain cannot properly interpret "that router problem" using the message alone.

Before invoking the Brain:

```text
User Message
↓
Memory Manager
↓
Context Engine
↓
CIEL Brain
```

The Memory Manager might retrieve:

```text
Project:
CIEL

Recent episode:
A problem was identified where router history survives controller exceptions.

Relevant component:
backend/src/router.py

Related fact:
Router history can be loaded into a later request when doRemember is true.
```

The Context Engine then presents this relevant information to the Brain.

The Brain therefore reasons using both current input and previous experience.

This is the foundation required for natural long-term memory.

---

# 7. CIEL Brain

The CIEL Brain becomes the primary cognitive component.

Its responsibilities include:

* Understanding user intent
* Interpreting retrieved memory
* Reasoning about the problem
* Determining whether information is missing
* Planning multi-step work
* Selecting the next conceptual action
* Evaluating tool observations
* Recovering from errors
* Determining whether more work is necessary
* Determining when the task is complete
* Identifying potential memory-worthy information
* Producing or preparing the final answer

Most importantly:

> The Brain decides what should happen next.

This responsibility should no longer belong to the Router.

---

# 8. Brain Decisions

The Brain should return a structured decision rather than only unrestricted natural language.

The exact schema can evolve, but conceptually:

```json
{
    "state": "action_required",
    "action": {
        "intent": "inspect_file",
        "target": "backend/src/router.py",
        "reason": "Need to inspect router history loading behaviour"
    }
}
```

Another example:

```json
{
    "state": "need_memory",
    "memory_request": {
        "query": "previous CIEL router failures",
        "scope": ["episodic", "project"]
    }
}
```

Completion might be:

```json
{
    "state": "complete",
    "response": "..."
}
```

Possible states may include:

```text
ACTION_REQUIRED
NEED_MEMORY
NEED_USER
COMPLETE
FAILED
```

Later, additional states could be introduced without redesigning the controller.

For example:

```text
DELEGATE
WAIT
SCHEDULE
REQUEST_PERMISSION
```

This is considerably more extensible than two Boolean flags.

---

# 9. Replace `isLooping`

The current `isLooping` flag should eventually disappear.

Currently, looping essentially means:

```text
Run another Router → Tools → CIEL cycle.
```

Instead, looping should emerge naturally from the Brain's state.

For example:

```text
Brain returns ACTION_REQUIRED
↓
execute action
↓
return observation
↓
Brain runs again
```

No Boolean is required.

Likewise:

```text
Brain returns COMPLETE
↓
stop interaction
```

The Controller can still enforce a safety limit such as:

```text
MAX_BRAIN_ITERATIONS = 10
```

But the iteration counter becomes infrastructure rather than something the Router decides.

---

# 10. Replace `doRemember`

The current `doRemember` flag should also eventually disappear.

Currently, `doRemember=true` primarily controls whether completed cycle information is persisted to router history and fed into later cycles.

That behaviour is not true long-term memory.

It is better described as:

```text
preserve_iteration_context
```

The new system should always maintain the necessary interaction context in Working Memory.

Long-term memory becomes a separate process.

Therefore:

```text
Working memory:
Always maintained while interaction is active.

Long-term memory:
Evaluated independently according to memory importance and type.
```

The Router should have no responsibility for long-term memory storage.

---

# 11. Planning

The Brain should eventually support explicit planning.

A Plan represents the current strategy for achieving an objective.

Example:

```text
Objective:
Fix CIEL startup failure.

Plan:
1. Reproduce startup failure.
2. Inspect traceback.
3. Identify responsible module.
4. Inspect dependency/configuration.
5. Apply minimal fix.
6. Run tests.
7. Start CIEL again.
8. Report result.
```

The Plan should be mutable.

Tool observations may cause it to change.

For example:

```text
Expected:
Missing Python dependency.

Observed:
Dependency exists, but incompatible version is installed.

Plan changes:
Inspect installed package version and compatibility requirements.
```

Plans belong to Working Memory.

They should not automatically become permanent memory.

---

# 12. Actions

The Brain should describe **what it wants done**, preferably at a semantic level.

For example:

```json
{
    "type": "inspect_file",
    "target": "backend/src/router.py"
}
```

or:

```json
{
    "type": "run_project",
    "project": "CIEL",
    "purpose": "reproduce startup failure"
}
```

The Brain should not always need to know exactly how the underlying tool performs this operation.

This creates separation between:

```text
Intent
```

and:

```text
Implementation
```

That distinction is important.

CIEL may know:

> I need to inspect router.py.

It does not necessarily need to decide whether that happens using:

```text
cat
sed
rg
Python file reading
GitHub
an IDE integration
a dedicated file tool
```

The action system can determine the implementation.

---

# 13. Action Router

The existing Router should be transformed into an **Action Router**.

Its purpose becomes much narrower.

The Router receives a Brain action request and converts it into valid executable tool calls.

Example:

Brain:

```json
{
    "intent": "inspect_file",
    "target": "backend/src/router.py"
}
```

Router:

```json
{
    "tools": [
        {
            "tool": "runBash",
            "action": "sed -n '1,240p' backend/src/router.py",
            "arguments": {}
        }
    ]
}
```

The Router therefore performs:

* Capability matching
* Tool selection
* Argument construction
* Command construction where required
* Tool-schema compliance
* Action validation
* Possibly batching compatible actions

It does **not** decide:

* What the user ultimately wants
* Whether CIEL should continue thinking
* Whether long-term memory should be stored
* Whether the task is conceptually complete
* What conclusion should be drawn from tool results

Those belong to the Brain.

---

# 14. Router as Translation Layer

Conceptually:

```text
CIEL Brain
"I need to inspect router.py."
        ↓
Action Router
"Use runBash with this command."
        ↓
Tool Manager
        ↓
Operating System
```

This allows CIEL's cognitive logic to stay independent from individual tool implementations.

For example, today:

```text
inspect_file
→ runBash
```

Later:

```text
inspect_file
→ native filesystem tool
```

The Brain does not need to change.

This is a major architectural advantage.

---

# 15. Tool Manager

The Tool Manager should become purely an execution component.

Its responsibilities:

* Validate a routed tool call
* Invoke the correct adapter
* Capture results
* Capture errors
* Emit execution events
* Return structured execution results

It should not alter cognitive state.

Specifically, it should eventually stop doing things equivalent to:

```text
Tool failed
→ force isLooping=true
```

Instead:

```text
Tool failed
↓
Observation
↓
Brain sees failure
↓
Brain decides what to do
```

This is much more intelligent.

A failure may mean:

* Retry
* Try another approach
* Inspect another source
* Ask the user
* Stop
* Explain permission denial
* Change the plan

Only the Brain has enough context to choose correctly.

---

# 16. Tool Execution Safety

The architecture should create space for an explicit Action Policy layer between the Router and Tool Manager.

This is important because the current shell tool executes router-generated strings directly using `subprocess.run(..., shell=True)` without sandboxing, confirmation, an allowlist or timeout.

Eventually:

```text
Brain
↓
Router
↓
Action Policy
↓
Tool Manager
```

The Action Policy can classify operations such as:

```text
SAFE
CONFIRMATION_REQUIRED
DENIED
```

Example:

```text
pwd
→ SAFE
```

```text
rm -rf project/
→ CONFIRMATION_REQUIRED
```

```text
destructive system operation outside policy
→ DENIED
```

This can be introduced later without changing how the Brain reasons.

---

# 17. Tool Results

Tool results should remain structured.

For example:

```json
{
    "tool": "runBash",
    "success": false,
    "returnCode": 1,
    "output": "ModuleNotFoundError: No module named 'xyz'"
}
```

However, raw tool results and cognitive observations should become separate concepts.

---

# 18. Observation Layer

Introduce the concept of an **Observation**.

An observation is what the Brain learns from an action.

For small outputs, the raw tool result may itself be the observation.

For example:

```text
Action:
pwd

Result:
/home/aliraza/Devs/CIEL

Observation:
Current working directory is /home/aliraza/Devs/CIEL.
```

For large outputs, an observation layer becomes increasingly useful.

Example:

```text
Tool Result:
2,000 lines of application logs

Observation:
CIEL crashes during import of ttsEngine.py because dependency X cannot be imported.
```

The system should retain references to raw results where necessary so information is not destroyed.

Conceptually:

```text
Action
↓
Raw Tool Result
↓
Observation
↓
Working Memory
↓
Brain
```

This prevents huge outputs from continuously consuming the model context window.

Initially this normalization may be basic.

More advanced compression can be added later.

---

# 19. Observation Feedback Loop

After every action:

```text
Brain
↓
Action
↓
Router
↓
Tool Manager
↓
Result
↓
Observation
↓
Working Memory
↓
Brain
```

The Brain now evaluates what actually happened.

For example:

### User

```text
Fix CIEL's startup error.
```

### Brain cycle 1

```text
Need to reproduce the error.
```

### Action

```text
Run CIEL.
```

### Observation

```text
CIEL crashes with ModuleNotFoundError: xyz.
```

### Brain cycle 2

```text
Need to inspect project dependencies.
```

### Action

```text
Inspect pyproject.toml.
```

### Observation

```text
xyz is not declared.
```

### Brain cycle 3

```text
Need to determine whether xyz should be a project dependency.
```

### Action

```text
Search repository imports for xyz.
```

### Observation

```text
xyz is imported by active production code.
```

### Brain cycle 4

```text
Add dependency and test.
```

Eventually:

```text
state = COMPLETE
```

This is the core CIEL reasoning loop.

---

# 20. Memory During an Interaction

Memory should be available during reasoning, not merely before or after a conversation.

The Brain may determine:

```text
I don't have enough context about this project decision.
```

and return:

```text
NEED_MEMORY
```

The Controller then asks the Memory Manager for additional information.

Example:

```text
Brain:
I need to know why the router model was previously changed.

Memory request:
episodic search for router model migration
```

Memory Manager returns relevant episodes.

These enter Working Memory.

The Brain runs again.

Therefore memory becomes an active cognitive resource.

---

# 21. External Data Sources

Memory retrieval and external truth should remain separate.

For example:

```text
Long-term memory:
Ali tracks projects inside LifeOS.
```

But:

```text
Current LifeOS project status
```

should be retrieved from LifeOS itself.

The Brain should therefore be able to request information from:

```text
Internal memory
External tools
Authoritative data services
Files
Repositories
LifeOS
Internet
Other future integrations
```

The Context Engine should distinguish the provenance of each piece of information.

---

# 22. Response Generation

The Brain and Response Generator should be conceptually separate even if they initially use the same model/provider.

The Brain's job:

```text
Determine what is true and what should happen.
```

The Response Generator's job:

```text
Communicate the completed result to the user.
```

For example, the Brain's internal completion state may contain:

```json
{
    "status": "complete",
    "result": {
        "cause": "Missing dependency",
        "changes": ["Added xyz"],
        "verification": "CIEL starts successfully"
    }
}
```

The Response Generator converts that into natural language:

```text
Found it. CIEL was failing because xyz was imported by the
TTS module but wasn't declared as a dependency. I added it
and verified that CIEL now starts successfully.
```

This separation prevents user-facing language requirements from interfering with reasoning.

---

# 23. Initial Implementation Can Reuse the Existing Response Model

Do not immediately introduce another model unless necessary.

Initially the current CIEL response model can operate as both:

```text
Brain + Response Generator
```

but keep the code boundaries separate.

For example:

```text
brain.py
response.py
```

may initially call the same provider.

Later they can use different:

* Models
* Prompts
* Temperatures
* Token budgets
* Providers

without redesigning the controller.

---

# 24. Brain Output Must Not Be Hidden Chain-of-Thought

Do not require the Brain to generate or store lengthy private reasoning transcripts.

The system needs **structured decisions and useful state**, not free-form hidden chain-of-thought.

Store things such as:

```text
Objective
Plan
Action requested
Observation
Established facts
Remaining work
Completion result
```

Do not build the architecture around preserving unrestricted internal reasoning text.

This makes the system:

* Smaller
* Easier to debug
* Safer
* Easier to persist
* Easier to inspect in the Brain UI

---

# 25. Post-Interaction Memory Evaluation

Once the Brain reaches `COMPLETE`, the interaction should be evaluated for long-term memory.

The pipeline becomes:

```text
Completed Interaction
↓
Memory Classifier
↓
Memory Candidates
↓
Validation / contradiction handling
↓
Persistent memory
```

Possible memory candidates include:

```text
Episode
Fact
Preference
Project update
Entity
Relationship
Procedure
Nothing
```

Memory creation must not block the core reasoning architecture.

This should be handled through the Memory Manager rather than by the Router.

---

# 26. Memory Candidates During Reasoning

The Brain may optionally mark information as potentially memory-worthy while solving a task.

Example:

```json
{
    "memory_candidates": [
        {
            "type": "project_fact",
            "subject": "CIEL",
            "predicate": "dependency_manager",
            "object": "uv"
        }
    ]
}
```

However, this should be treated only as a candidate.

The Memory Manager remains responsible for:

* Deduplication
* Verification
* Contradiction detection
* Confidence
* Storage
* Provenance

The Brain should not directly write arbitrary memories into databases.

---

# 27. Session Context

Introduce a concept of sessions separate from individual messages.

A session may contain multiple interactions.

For example:

```text
Session: Debugging CIEL memory architecture

Interaction 1:
Discuss brain redesign.

Interaction 2:
Inspect controller implementation.

Interaction 3:
Implement new InteractionContext.

Interaction 4:
Test tool loop.
```

Session context can help CIEL understand what is currently being worked on without retrieving every individual event from long-term memory.

Possible hierarchy:

```text
Long-term memory
        ↑
Session memory
        ↑
Interaction working memory
```

---

# 28. Context Compression

As interactions become long, Working Memory will grow.

The Context Engine should eventually compress older portions.

For example:

```text
Actions 1-5:
raw details

Actions 6-10:
raw details

Earlier actions:
summary
```

An older working-memory segment might become:

```text
Earlier investigation established that:
- Router history survives controller exceptions.
- The global flag system causes that history to be reloaded.
- No corruption was found in routerSchema.json.
```

The raw evidence can remain referenced elsewhere.

The Brain receives only what remains relevant.

---

# 29. Failure Handling

Failures should become observations rather than automatically determining control flow.

Current behaviour can force recovery loops after tool failures.

Instead:

```text
Tool failure
↓
structured failure result
↓
Observation
↓
Brain
```

The Brain determines the appropriate response.

Examples:

### Transient failure

```text
Network timeout.
```

Brain:

```text
Retry once.
```

### Permission failure

```text
LifeOS permission denied.
```

Brain:

```text
Cannot retry productively.
Explain required permission.
```

### Incorrect command

```text
Unknown command option.
```

Brain:

```text
Inspect command documentation and try corrected syntax.
```

### Repeated failures

Brain:

```text
Stop attempting the same method and select another approach.
```

This makes recovery contextual instead of hard-coded.

---

# 30. Safety Limit

Keep a hard maximum number of cognitive cycles.

For example:

```python
MAX_BRAIN_ITERATIONS = 10
```

If exceeded:

```text
Controller
↓
force completion state
↓
Brain/Responder generates best available result
```

The response should explain if the task could not be completely resolved.

This replaces the existing fixed fifth-cycle Router safety stop with a more general interaction safety limit.

---

# 31. Human Input State

Some tasks genuinely require information from the user.

Therefore add:

```text
NEED_USER
```

Example:

```json
{
    "state": "need_user",
    "question": "Which repository should I modify?"
}
```

The interaction can then terminate or pause at a well-defined boundary.

Future versions of CIEL could support resumable interaction state.

---

# 32. Event Architecture

The current event system is valuable and should remain.

However, stages should eventually represent the new architecture.

Instead of:

```text
Router
Tools
CIEL
Voice
Control
```

consider:

```text
Context
Memory
Brain
Routing
Tools
Observation
Response
Memory Commit
Speech
```

Possible events:

```text
interaction.started

context.started
context.completed

memory.retrieval.started
memory.retrieval.completed

brain.started
brain.decision

router.started
router.completed

tools.started
tool.started
tool.completed

observation.created

response.started
response.token
response.completed

memory.evaluation.started
memory.committed

speech.started
speech.completed

interaction.completed
interaction.failed
```

This gives the Brain UI much better visibility into CIEL's actual architecture.

---

# 33. Brain UI

The existing Brain page currently exposes operational routing/tool state rather than hidden reasoning, which is a good principle.

Preserve that.

The redesigned Brain UI should display safe structural state such as:

```text
Current Objective
Current Stage
Iteration
Retrieved Memories
Current Plan
Requested Action
Tool Being Used
Latest Observation
Memory Candidates
Completion State
```

Do not display private chain-of-thought.

The UI becomes an observability interface into **what CIEL is doing**, not a transcript of hidden reasoning.

---

# 34. Full Example

Suppose the user says:

```text
Figure out why my CIEL tests are failing and fix them.
```

## Phase 1: Interaction creation

Controller creates:

```text
interaction_id = abc123
iteration = 0
status = active
```

---

## Phase 2: Context retrieval

Context Engine gathers:

```text
Current project:
CIEL

Recent project memory:
Router architecture recently changed.

Relevant files:
Known backend test structure.

User request:
Find and fix test failures.
```

---

## Phase 3: Brain

Brain determines:

```text
Need to run the test suite.
```

Returns:

```text
ACTION_REQUIRED
intent = run CIEL tests
```

---

## Phase 4: Router

Router converts intention into:

```text
cd backend && python -m unittest discover -p "test_*.py"
```

---

## Phase 5: Tool Manager

Executes command.

Result:

```text
17 tests
2 failures

test_router...
test_controller...
```

---

## Phase 6: Observation

Observation becomes:

```text
Two tests fail.
Both relate to the old isLooping/doRemember behaviour.
```

Working Memory is updated.

---

## Phase 7: Brain again

Brain determines:

```text
Need to inspect failing tests and corresponding implementation.
```

Requests relevant files.

---

## Phase 8: More actions

The cycle continues:

```text
Brain
→ Router
→ Tool
→ Observation
→ Brain
```

until the Brain determines the issue.

---

## Phase 9: Modification

Brain requests:

```text
Apply minimal code change.
```

Router chooses appropriate capability.

Tool executes it.

---

## Phase 10: Verification

Brain requests:

```text
Run tests again.
```

Observation:

```text
All tests pass.
```

Brain may additionally request:

```text
Run CIEL startup smoke test.
```

Observation:

```text
CIEL starts successfully.
```

---

## Phase 11: Completion

Brain returns:

```text
COMPLETE

Cause:
Tests expected obsolete global flag behaviour.

Changes:
Updated controller and relevant tests.

Verification:
All automated tests pass and CIEL starts.
```

---

## Phase 12: Response

Response Generator produces the user-facing answer.

---

## Phase 13: Memory

Memory Manager examines the interaction.

Possible memories:

```text
Project fact:
CIEL no longer uses router-controlled isLooping.

Episode:
CIEL brain architecture migration required updating controller tests.

Project update:
Interaction state now belongs to InteractionContext.
```

These are persisted according to the memory architecture.

---

# 35. Recommended Module Structure

The redesigned backend could gradually move toward:

```text
backend/src/
│
├── controller/
│   ├── controller.py
│   ├── interaction.py
│   └── state.py
│
├── brain/
│   ├── brain.py
│   ├── decisions.py
│   ├── planner.py
│   └── schemas.py
│
├── context/
│   ├── engine.py
│   ├── builder.py
│   └── compression.py
│
├── memory/
│   ├── manager.py
│   ├── working.py
│   ├── episodic.py
│   ├── semantic.py
│   ├── procedural.py
│   └── ...
│
├── actions/
│   ├── router.py
│   ├── schemas.py
│   └── policy.py
│
├── tools/
│   ├── manager.py
│   ├── bash.py
│   ├── lifeos.py
│   └── ...
│
├── observations/
│   ├── normalizer.py
│   └── schemas.py
│
├── response/
│   ├── generator.py
│   └── streaming.py
│
├── providers/
│   └── ...
│
└── events.py
```

Do not reorganize the entire repository immediately.

This represents the desired responsibility boundaries.

Migration can happen incrementally.

---

# 36. Responsibility Boundaries

## Controller

Knows:

```text
Where the interaction currently is.
```

Does not decide:

```text
What CIEL should think.
```

---

## Context Engine

Knows:

```text
What information should be presented to CIEL.
```

Does not decide:

```text
What action should happen.
```

---

## Memory Manager

Knows:

```text
What CIEL previously learned and what may deserve persistence.
```

Does not directly execute tools.

---

## Brain

Knows:

```text
What CIEL wants to achieve and what should happen next.
```

Does not directly execute commands.

---

## Router

Knows:

```text
How an intended action maps onto available tools.
```

Does not determine the overall objective.

---

## Tool Manager

Knows:

```text
How to execute a validated tool request.
```

Does not reason about results.

---

## Observation Layer

Knows:

```text
What useful information came back from execution.
```

Does not decide the next action.

---

## Response Generator

Knows:

```text
How to communicate completed results.
```

Does not control the task.

---

# 37. Main Architectural Rule

The central rule of the redesign is:

```text
Reasoning must always return to CIEL.
```

A tool cannot decide that another tool should execute.

A Router cannot decide that CIEL should continue thinking.

A failure handler cannot decide the user's objective.

Every significant change in direction should return through:

```text
Observation
↓
CIEL Brain
↓
Next decision
```

This gives the system one coherent cognitive authority.

---

# 38. Migration From Current CIEL

Do not rewrite everything simultaneously.

The existing implementation already has useful components:

* Controller serialization
* Event system
* Groq structured-output Router
* Tool Manager
* Bash adapter
* LifeOS adapter
* Response provider
* TTS
* Frontend observability
* Existing tests

Preserve them where possible.

The migration should change responsibility boundaries rather than destroy working infrastructure.

---

# 39. Recommended Migration Stages

## Stage 1: Interaction Context

Introduce `InteractionContext`.

Move cycle-local state out of global flags where possible.

Keep existing execution behaviour temporarily.

---

## Stage 2: Brain Decision Schema

Create a structured output contract for the CIEL Brain.

Support initially:

```text
ACTION_REQUIRED
COMPLETE
```

Do not add every future state immediately.

---

## Stage 3: Move CIEL Before Router

Change the cycle from:

```text
Router
→ Tools
→ CIEL
```

to:

```text
CIEL Brain
→ Router
→ Tools
→ CIEL Brain
```

This is the critical migration.

---

## Stage 4: Remove Router Loop Control

Stop allowing Router decisions to control `isLooping`.

The Brain state determines whether execution continues.

---

## Stage 5: Working Memory

Store:

```text
actions
results
observations
current objective
current plan
```

inside InteractionContext.

Remove dependency on routerHistory for intra-task reasoning.

---

## Stage 6: Observation Layer

Normalize tool results before repeatedly inserting them into Brain context.

---

## Stage 7: Context Engine

Move prompt/context assembly out of individual provider and response functions into a dedicated component.

---

## Stage 8: Memory Retrieval

Connect the previously designed Memory Manager before Brain reasoning.

---

## Stage 9: Memory Requests During Reasoning

Add:

```text
NEED_MEMORY
```

to the Brain state machine.

---

## Stage 10: Memory Consolidation

Run memory evaluation after successful interactions.

---

## Stage 11: Action Policy

Introduce safety/permission handling between Router and Tool Manager.

---

## Stage 12: Response Separation

Separate Brain completion data from final natural-language response generation.

---

# 40. Do Not Overengineer the First Version

The first working architecture does not need:

* Multiple autonomous agents
* A graph execution engine
* Complex workflow frameworks
* Event sourcing
* Distributed queues
* Redis
* Multiple planner models
* Separate observation models
* Persistent background cognition

The first meaningful redesign can simply be:

```text
Message
↓
InteractionContext
↓
Relevant Chat/Memory Context
↓
CIEL Brain
↓
ACTION_REQUIRED?
├── yes
│   ↓
│ Router
│   ↓
│ Tool Manager
│   ↓
│ Result
│   ↓
│ add to InteractionContext
│   ↓
│ CIEL Brain
│
└── no
    ↓
COMPLETE
↓
Final Response
↓
Memory Evaluation
```

That alone is a major improvement.

---

# 41. Final Target Architecture

The long-term CIEL architecture should conceptually become:

```text
                         USER
                          │
                          ▼
                ┌─────────────────────┐
                │     CONTROLLER      │
                │                     │
                │ Interaction lifecycle│
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   CONTEXT ENGINE    │
                │                     │
                │ Session             │
                │ Working memory      │
                │ Long-term memory    │
                │ Current state       │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │     CIEL BRAIN      │
                │                     │
                │ Understand          │
                │ Reason              │
                │ Plan                │
                │ Decide              │
                │ Evaluate            │
                └──────────┬──────────┘
                           │
            ┌──────────────┼────────────────┐
            │              │                │
            ▼              ▼                ▼
         ACTION         MEMORY          COMPLETE
            │           REQUEST             │
            ▼              │                │
      ┌────────────┐       ▼                │
      │   ROUTER   │  MEMORY MANAGER        │
      └─────┬──────┘       │                │
            │              └──────┐         │
            ▼                     │         │
      ACTION POLICY               │         │
            │                     │         │
            ▼                     │         │
      TOOL MANAGER                │         │
            │                     │         │
            ▼                     │         │
          TOOL                    │         │
            │                     │         │
            ▼                     │         │
      RAW RESULT                  │         │
            │                     │         │
            ▼                     │         │
      OBSERVATION                 │         │
            │                     │         │
            └──────────┬──────────┘         │
                       │                    │
                       ▼                    │
                   CIEL BRAIN               │
                       │                    │
                       └────────────────────┘
                                │
                                ▼
                       RESPONSE GENERATOR
                                │
                                ▼
                       MEMORY EVALUATION
                                │
                                ▼
                         MEMORY COMMIT
                                │
                                ▼
                              USER
```

---

# 42. Core Design Principles

The redesigned CIEL brain should obey the following principles:

1. **CIEL is the cognitive authority.**
   The Brain determines what should happen next.

2. **The Controller orchestrates but does not reason.**
   It manages lifecycle, state, limits and dispatch.

3. **Memory exists outside the Router.**
   Memory retrieval occurs before and during reasoning, while persistence occurs independently after useful information is identified.

4. **The Router translates actions.**
   It maps Brain intentions onto available tools.

5. **Tools execute but do not think.**
   Tool Manager behaviour should remain deterministic.

6. **Results become observations.**
   Tool output is interpreted and returned to CIEL before another strategic decision occurs.

7. **Every strategic loop returns through CIEL.**
   No subsystem should independently redirect the overall task.

8. **Working memory is interaction-local.**
   Temporary task state should not rely on global variables or router-history files.

9. **Long-term memory and loop context are separate concepts.**

10. **The Brain should communicate using structured state rather than unrestricted reasoning transcripts.**

11. **Completion is a state, not the absence of a loop flag.**

12. **Failures are information.**
    They should return to the Brain as observations rather than automatically forcing retries.

13. **Intent should be separated from implementation.**
    CIEL asks for an outcome; the Router determines the appropriate tool call.

14. **Context should be selectively assembled.**
    CIEL should receive relevant information rather than entire histories.

15. **Existing components should be migrated rather than needlessly rewritten.**

16. **The architecture must leave clean extension points for memory, planning, permissions, specialist agents and future capabilities.**

---

# End Goal

CIEL should no longer behave like:

```text
A Router that executes tools and then asks an LLM to explain what happened.
```

It should behave like:

```text
An intelligent system that understands an objective,
remembers relevant information,
decides what it needs to know,
takes actions through controlled tools,
observes the consequences,
updates its understanding,
changes its plan when necessary,
recognises when the objective has been achieved,
communicates the result,
and learns useful information from the experience.
```

That is the foundation the memory architecture should be built on.
