import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


settings = types.ModuleType("backend.ciel.runtime.settings")
settings.groqApiKey = "test-key"
settings.groqBaseUrl = "https://api.groq.test/openai/v1"
settings.groqMaxRetries = 2
settings.groqRetryBackoffSeconds = 0
settings.groqRouterModel = "test-router"
settings.groqTimeoutSeconds = 12

logger = types.ModuleType("backend.ciel.runtime.logging")
logger.log = Mock()

with patch.dict(
    sys.modules,
    {
        "backend.ciel.runtime.settings": settings,
        "backend.ciel.runtime.logging": logger,
    },
):
    sys.modules.pop("backend.ciel.providers.groq", None)
    groqProv = importlib.import_module("backend.ciel.providers.groq")


class GroqResponseFormatTests(unittest.TestCase):
    def test_raw_ollama_schema_is_wrapped_for_supported_groq_model(self):
        schema = {
            "type": "object",
            "properties": {"tools": {"type": "array"}},
            "required": ["tools"],
        }

        result = groqProv._responseFormat(schema, model="openai/gpt-oss-20b")

        self.assertEqual(result["type"], "json_schema")
        self.assertEqual(result["json_schema"]["name"], "ciel_router_decision")
        self.assertFalse(result["json_schema"]["strict"])
        self.assertIs(result["json_schema"]["schema"], schema)

    def test_raw_schema_uses_json_object_mode_for_other_models(self):
        schema = {"type": "object"}

        result = groqProv._responseFormat(schema, model="qwen/qwen3.6-27b")

        self.assertEqual(result, {"type": "json_object"})

    def test_preformatted_response_format_is_preserved(self):
        responseFormat = {"type": "json_object"}

        self.assertIs(groqProv._responseFormat(responseFormat), responseFormat)

    def test_unknown_string_format_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported Groq response format"):
            groqProv._responseFormat("yaml")


class GroqRecoveryTests(unittest.TestCase):
    def setUp(self):
        logger.log.reset_mock()

    def test_transient_status_is_retried(self):
        client = Mock()
        transientError = RuntimeError("busy")
        transientError.status_code = 503
        expected = object()
        client.chat.completions.create.side_effect = [transientError, expected]

        result = groqProv._chatWithGroqRecovery(
            client,
            {"model": "router"},
            maxRetries=1,
            retryBackoffSeconds=0,
        )

        self.assertIs(result, expected)
        self.assertEqual(client.chat.completions.create.call_count, 2)
        logger.log.assert_called_once()

    def test_non_retryable_error_is_wrapped_without_retry(self):
        client = Mock()
        invalidRequest = RuntimeError("invalid schema")
        invalidRequest.status_code = 400
        client.chat.completions.create.side_effect = invalidRequest

        with self.assertRaisesRegex(RuntimeError, "Groq request failed: invalid schema"):
            groqProv._chatWithGroqRecovery(
                client,
                {"model": "router"},
                maxRetries=2,
                retryBackoffSeconds=0,
            )

        self.assertEqual(client.chat.completions.create.call_count, 1)


class GroqCommunicationTests(unittest.TestCase):
    def test_non_streaming_request_uses_config_and_schema(self):
        completion = types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content='{"tools": []}')
                )
            ]
        )
        client = Mock()
        client.chat.completions.create.return_value = completion
        openAI = Mock(return_value=client)
        openAIModule = types.ModuleType("openai")
        openAIModule.OpenAI = openAI
        schema = {"type": "object"}

        with (
            patch.dict(sys.modules, {"openai": openAIModule}),
            patch.object(groqProv, "groqRouterModel", "openai/gpt-oss-20b"),
        ):
            result = groqProv.groqComm("system", "user", False, schema)

        self.assertEqual(result, '{"tools": []}')
        openAI.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.groq.test/openai/v1",
            max_retries=0,
            timeout=12,
        )
        arguments = client.chat.completions.create.call_args.kwargs
        self.assertEqual(arguments["model"], "openai/gpt-oss-20b")
        self.assertFalse(arguments["stream"])
        self.assertEqual(arguments["response_format"]["type"], "json_schema")
        self.assertIs(arguments["response_format"]["json_schema"]["schema"], schema)

    def test_missing_configuration_fails_before_a_request(self):
        with patch.object(groqProv, "groqApiKey", None):
            with self.assertRaisesRegex(RuntimeError, "GROQ_API_KEY"):
                groqProv._validateConfiguration()

    def test_retired_model_returns_actionable_error(self):
        with patch.object(groqProv, "groqRouterModel", "llama-3.3-70b-specdec"):
            with self.assertRaisesRegex(RuntimeError, "has been retired"):
                groqProv._validateConfiguration()


if __name__ == "__main__":
    unittest.main()
