import importlib
import io
import sys
import types
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError


settings = types.ModuleType("backend.ciel.runtime.settings")
settings.ollamaRouterModel = "test-router"
settings.lifeOSAPIKey = "test-key"
settings.lifeOSBaseURL = "http://lifeos.test"
settings.lifeOSMaxRetries = 1
settings.lifeOSRetryBackoffSeconds = 0
settings.lifeOSTimeoutSeconds = 1

logger = types.ModuleType("backend.ciel.runtime.logging")
logger.log = Mock()

events = types.ModuleType("backend.ciel.core.events")
events.eventBus = Mock()

flagManager = types.ModuleType("backend.ciel.runtime.flags")


class TestFlags:
    isLooping = False
    doRemember = False

    def setFlagState(self, flag, state):
        setattr(self, flag, state)


flagManager.flags = TestFlags()

jsonTools = types.ModuleType("backend.ciel.runtime.json_repair")
jsonTools.fixJson = Mock(side_effect=ValueError("invalid JSON"))

runBashCommands = types.ModuleType("backend.ciel.agent_tools.shell")
runBashCommands.runCommands = Mock()

with patch.dict(
    sys.modules,
    {
        "backend.ciel.runtime.settings": settings,
        "backend.ciel.runtime.logging": logger,
        "backend.ciel.core.events": events,
        "backend.ciel.runtime.flags": flagManager,
        "backend.ciel.runtime.json_repair": jsonTools,
        "backend.ciel.agent_tools.shell": runBashCommands,
    },
):
    sys.modules.pop("backend.ciel.providers.ollama", None)
    sys.modules.pop("backend.ciel.agent_tools.lifeos.client", None)
    sys.modules.pop("backend.ciel.core.tool_dispatcher", None)
    ollamaProv = importlib.import_module("backend.ciel.providers.ollama")
    lifeosClient = importlib.import_module("backend.ciel.agent_tools.lifeos.client")
    sys.modules["backend.ciel.agent_tools.lifeos.client"] = lifeosClient
    toolManager = importlib.import_module("backend.ciel.core.tool_dispatcher")


class OllamaOOMRecoveryTests(unittest.TestCase):
    def test_oom_restarts_service_and_retries_once(self):
        ollama = Mock()
        expected = {"message": {"content": "ok"}}
        ollama.chat.side_effect = [RuntimeError("CUDA out of memory"), expected]
        restart = Mock(returncode=0, stdout="", stderr="")

        with patch.object(ollamaProv.subprocess, "run", return_value=restart) as run:
            response = ollamaProv._chatWithOOMRecovery(ollama, {"model": "router"})

        self.assertEqual(response, expected)
        self.assertEqual(ollama.chat.call_count, 2)
        run.assert_called_once_with(
            ["sudo", "-n", "systemctl", "restart", "ollama"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_non_oom_error_is_not_restarted(self):
        ollama = Mock()
        ollama.chat.side_effect = RuntimeError("connection refused")

        with patch.object(ollamaProv.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "connection refused"):
                ollamaProv._chatWithOOMRecovery(ollama, {"model": "router"})

        run.assert_not_called()
        self.assertEqual(ollama.chat.call_count, 1)

    def test_failed_restart_returns_an_actionable_error(self):
        ollama = Mock()
        ollama.chat.side_effect = RuntimeError("runner failed: out of memory")
        restart = Mock(returncode=1, stdout="", stderr="a password is required")

        with patch.object(ollamaProv.subprocess, "run", return_value=restart):
            with self.assertRaisesRegex(RuntimeError, "could not be restarted"):
                ollamaProv._chatWithOOMRecovery(ollama, {"model": "router"})

        self.assertEqual(ollama.chat.call_count, 1)


class LifeOSPermissionHandlingTests(unittest.TestCase):
    def setUp(self):
        toolManager.flags.setFlagState("isLooping", False)
        toolManager.flags.setFlagState("doRemember", False)

    def test_permission_statuses_are_classified(self):
        self.assertTrue(
            lifeosClient.isLifeOSPermissionError({"success": False, "statusCode": 401})
        )
        self.assertTrue(
            lifeosClient.isLifeOSPermissionError({"success": False, "statusCode": 403})
        )
        self.assertTrue(
            lifeosClient.isLifeOSPermissionError(
                {
                    "success": False,
                    "statusCode": 400,
                    "data": {"code": "permission_denied"},
                }
            )
        )
        self.assertFalse(
            lifeosClient.isLifeOSPermissionError(
                {"success": False, "statusCode": 500}
            )
        )

    def test_http_403_result_is_marked_non_retryable(self):
        forbidden = HTTPError(
            "http://lifeos.test/api/v1/assistant/context/today",
            403,
            "Forbidden",
            {},
            io.BytesIO(b'{"message": "Not allowed"}'),
        )
        self.addCleanup(forbidden.close)

        with patch.object(lifeosClient, "urlopen", side_effect=forbidden) as request:
            result = lifeosClient.runLifeOSAction("get_today", {})

        self.assertEqual(request.call_count, 1)
        self.assertEqual(result["statusCode"], 403)
        self.assertEqual(result["errorType"], "permission_denied")
        self.assertFalse(result["retryable"])

    def test_lifeos_permission_failure_ends_loop(self):
        decision = {
            "flags": {"isLooping": True, "doRemember": True},
            "tools": [
                {"tool": "lifeOS", "action": "get_today", "arguments": {}}
            ],
        }
        denied = {
            "success": False,
            "statusCode": 403,
            "error": "Not allowed",
            "errorType": "permission_denied",
            "retryable": False,
        }

        with patch.object(toolManager, "runLifeOSAction", return_value=denied):
            execution = toolManager.toolRouter(decision)

        self.assertEqual(
            execution["flags"], {"isLooping": False, "doRemember": False}
        )
        self.assertFalse(toolManager.flags.isLooping)
        self.assertFalse(toolManager.flags.doRemember)

    def test_regular_failure_still_requests_a_recovery_cycle(self):
        decision = {
            "flags": {"isLooping": False, "doRemember": False},
            "tools": [
                {"tool": "lifeOS", "action": "get_today", "arguments": {}}
            ],
        }
        unavailable = {"success": False, "statusCode": 503, "error": "Unavailable"}

        with patch.object(toolManager, "runLifeOSAction", return_value=unavailable):
            execution = toolManager.toolRouter(decision)

        self.assertEqual(
            execution["flags"], {"isLooping": True, "doRemember": True}
        )


class ControllerDialogueTests(unittest.TestCase):
    def test_brain_controls_action_loop_and_final_persistence(self):
        sys.modules.pop("backend.ciel.core.controller", None)
        controller = importlib.import_module("backend.ciel.core.controller")
        schemas = importlib.import_module("backend.ciel.brain.schemas")

        memoryManager = Mock()
        memoryManager.recent_conversation.return_value = []
        memoryManager.retrieve_context.return_value = []
        memoryManager.evaluate_interaction.return_value = ["memory-1"]

        brain = Mock()
        brain.think.side_effect = [
            schemas.BrainDecision(
                state=schemas.ACTION_REQUIRED,
                action={"intent": "inspect_file", "target": "README.md"},
            ),
            schemas.BrainDecision(
                state=schemas.COMPLETE,
                response="final answer",
            ),
        ]

        actionRouter = Mock()
        actionRouter.route.return_value = {
            "flags": {"isLooping": False, "doRemember": False},
            "tools": [{"tool": "runBash", "action": "pwd", "arguments": {}}],
        }

        toolExecution = {
            "flags": {"isLooping": False, "doRemember": False},
            "tools": [{"tool": "runBash", "action": "pwd", "arguments": {}}],
            "results": [{"tool": "runBash", "action": "pwd", "success": True, "output": "/tmp"}],
        }
        normalizer = Mock()
        normalizer.normalize.return_value = {"success": True, "summary": "pwd succeeded"}
        responseGenerator = Mock()
        responseGenerator.generate.return_value = "final answer"

        with (
            patch.object(controller, "MemoryManager", return_value=memoryManager),
            patch.object(controller, "CIELBrain", return_value=brain),
            patch.object(controller, "ActionRouter", return_value=actionRouter),
            patch.object(controller, "ObservationNormalizer", return_value=normalizer),
            patch.object(controller, "ResponseGenerator", return_value=responseGenerator),
            patch.object(controller, "executeToolCalls", return_value=toolExecution) as execute,
        ):
            response = controller._runController("hello", "interaction-1")

        self.assertEqual(response, "final answer")
        self.assertEqual(brain.think.call_count, 2)
        actionRouter.route.assert_called_once()
        execute.assert_called_once()
        memoryManager.persist_interaction.assert_called_once()
        memoryManager.evaluate_interaction.assert_called_once()


if __name__ == "__main__":
    unittest.main()
