import threading
import uuid

from backend.ciel.actions.router import ActionRouter
from backend.ciel.brain.brain import CIELBrain
from backend.ciel.brain.schemas import (
    ACTION_REQUIRED,
    COMPLETE,
    FAILED,
    NEED_MEMORY,
    NEED_USER,
    BrainDecision,
)
from backend.ciel.context.engine import ContextEngine
from backend.ciel.context.interaction import InteractionContext
from backend.ciel.core.events import eventBus
from backend.ciel.core.tool_dispatcher import executeToolCalls
from backend.ciel.memory.manager import MemoryManager
from backend.ciel.observations.normalizer import ObservationNormalizer
from backend.ciel.response.generator import ResponseGenerator
from backend.ciel.runtime.flags import flags
from backend.ciel.runtime.logging import log

file = "controller.py"

maxBrainIterations = 10
_controllerLock = threading.Lock()
_runtimeSessionId = f"runtime-{uuid.uuid4().hex}"


def isControllerBusy():
    return _controllerLock.locked()


def runController(userMessage, interactionId=None, sessionId=None):
    interactionId = interactionId or uuid.uuid4().hex
    with _controllerLock:
        return _runController(
            userMessage,
            interactionId,
            sessionId=sessionId or _runtimeSessionId,
        )


def _runController(userMessage, interactionId, sessionId=None):
    memoryManager = MemoryManager()
    contextEngine = ContextEngine(memoryManager)
    brain = CIELBrain()
    actionRouter = ActionRouter()
    observationNormalizer = ObservationNormalizer()
    responseGenerator = ResponseGenerator()
    context = InteractionContext.create(
        userMessage,
        interactionId,
        session_id=sessionId or _runtimeSessionId,
    )

    # Compatibility flags remain observable for the legacy UI/API but no longer
    # control the cognitive loop.
    flags.setFlagState("isLooping", False)
    flags.setFlagState("doRemember", False)
    eventBus.emit(
        "interaction.started",
        {
            "interactionId": interactionId,
            "sessionId": context.session_id,
            "message": userMessage,
        },
    )

    try:
        eventBus.emit("context.started", {"interactionId": interactionId})
        eventBus.emit(
            "memory.retrieval.started",
            {"interactionId": interactionId, "query": userMessage},
        )
        contextEngine.prepare_interaction(context)
        eventBus.emit(
            "memory.retrieval.completed",
            {
                "interactionId": interactionId,
                "memories": context.retrieved_memories,
            },
        )
        eventBus.emit(
            "context.completed",
            {
                "interactionId": interactionId,
                "conversationItems": len(context.conversation_context),
                "retrievedMemories": len(context.retrieved_memories),
            },
        )

        finalDecision = None
        for iteration in range(1, maxBrainIterations + 1):
            context.iteration = iteration
            eventData = {"interactionId": interactionId, "iteration": iteration}
            brainContext = contextEngine.build_brain_context(context)

            eventBus.emit("brain.started", eventData)
            decision = brain.think(brainContext)
            finalDecision = decision
            context.brain_decisions.append(decision.to_dict())
            if decision.plan:
                context.current_plan = decision.plan
            if decision.memory_candidates:
                context.add_memory_candidates(decision.memory_candidates)
            eventBus.emit(
                "brain.decision",
                {**eventData, "decision": decision.to_dict()},
            )

            if decision.state == ACTION_REQUIRED:
                context.add_action(decision.action)
                eventBus.emit(
                    "router.started",
                    {**eventData, "action": decision.action},
                )
                routedAction = actionRouter.route(decision.action, brainContext)
                context.routed_actions.append(routedAction)
                eventBus.emit(
                    "router.completed",
                    {**eventData, "decision": routedAction},
                )
                eventBus.emit(
                    "router.decision",
                    {**eventData, "decision": routedAction},
                )
                eventBus.emit(
                    "tools.started",
                    {**eventData, "tools": routedAction.get("tools", [])},
                )
                toolExecution = executeToolCalls(
                    routedAction,
                    interactionId=interactionId,
                    iteration=iteration,
                )
                context.tool_results.append(toolExecution)
                observation = observationNormalizer.normalize(
                    decision.action,
                    routedAction,
                    toolExecution,
                )
                context.add_observation(observation)
                eventBus.emit(
                    "observation.created",
                    {**eventData, "observation": observation},
                )
                continue

            if decision.state == NEED_MEMORY:
                request = decision.memory_request
                eventBus.emit(
                    "memory.retrieval.started",
                    {**eventData, "request": request},
                )
                memories = memoryManager.retrieve_context(request)
                before = len(context.retrieved_memories)
                context.add_retrieved_memories(memories)
                added = len(context.retrieved_memories) - before
                eventBus.emit(
                    "memory.retrieval.completed",
                    {**eventData, "memories": memories, "added": added},
                )
                if added == 0:
                    context.add_observation(
                        {
                            "success": False,
                            "summary": (
                                "The requested memory lookup returned no new information. "
                                "Do not repeat the same memory request without changing the query."
                            ),
                            "type": "memory_no_new_results",
                        }
                    )
                continue

            if decision.state == NEED_USER:
                response = responseGenerator.generate(context, decision, stream=False)
                context.finish(NEED_USER, response)
                break

            if decision.state in {COMPLETE, FAILED}:
                response = responseGenerator.generate(context, decision)
                context.finish(decision.state, response)
                break

        if context.final_response is None:
            finalDecision = finalDecision or BrainDecision(
                state=FAILED,
                response="I reached the interaction safety limit before completing the task.",
                result={"error": "safety_limit"},
            )
            safetyDecision = BrainDecision(
                state=FAILED,
                response=(
                    "I reached the interaction safety limit before completing the task. "
                    "Here is the best available state from the work so far."
                ),
                result=finalDecision.to_dict(),
            )
            response = responseGenerator.generate(context, safetyDecision, stream=False)
            context.finish(FAILED, response)
            eventBus.emit(
                "interaction.safety_limit",
                {
                    "interactionId": interactionId,
                    "iteration": maxBrainIterations,
                },
            )

        eventBus.emit(
            "memory.evaluation.started",
            {"interactionId": interactionId},
        )
        memoryManager.persist_interaction(context)
        committedMemories = (
            memoryManager.evaluate_interaction(context)
            if context.status == COMPLETE
            else []
        )
        context.working_memory.clear()
        eventBus.emit(
            "memory.committed",
            {
                "interactionId": interactionId,
                "memoryIds": committedMemories,
            },
        )
        eventBus.emit("history.saved", {"interactionId": interactionId})
        log(
            "info",
            f"{file}: interaction completed after {context.iteration} iteration(s)",
        )
        eventBus.emit(
            "interaction.completed",
            {
                "interactionId": interactionId,
                "iteration": context.iteration,
                "response": context.final_response,
                "status": context.status,
                "sessionId": context.session_id,
            },
        )
        return context.final_response
    except Exception as error:
        context.finish(FAILED, context.final_response)
        try:
            memoryManager.persist_interaction(context)
        except Exception as persistError:
            log("error", f"{file}: failed to persist failed interaction: {persistError}")
        eventBus.emit(
            "interaction.failed",
            {"interactionId": interactionId, "error": str(error)},
        )
        raise
