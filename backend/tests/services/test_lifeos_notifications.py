from __future__ import annotations

"""Regression tests for the non-blocking LifeOS notification poller."""

import importlib
import sys
import types
import unittest
from unittest.mock import Mock, call, patch


class LifeOSNotificationPollingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = types.ModuleType("backend.ciel.agent_tools.lifeos.client")
        cls.client.runLifeOSAction = Mock()

        cls.events = types.ModuleType("backend.ciel.core.events")
        cls.events.eventBus = Mock()

        cls.logger = types.ModuleType("backend.ciel.runtime.logging")
        cls.logger.log = Mock()

        cls.settings = types.ModuleType("backend.ciel.runtime.settings")
        cls.settings.lifeOSAPIKey = "test-key"
        cls.settings.lifeOSNotificationPollSeconds = 5.0
        cls.settings.lifeOSNotificationsEnabled = True

        cls.module_patches = patch.dict(
            sys.modules,
            {
                "backend.ciel.agent_tools.lifeos.client": cls.client,
                "backend.ciel.core.events": cls.events,
                "backend.ciel.runtime.logging": cls.logger,
                "backend.ciel.runtime.settings": cls.settings,
            },
        )
        cls.module_patches.start()
        sys.modules.pop("backend.ciel.services.lifeos_notifications", None)
        cls.notifications = importlib.import_module(
            "backend.ciel.services.lifeos_notifications"
        )

    @classmethod
    def tearDownClass(cls):
        cls.module_patches.stop()

    def setUp(self):
        self.client.runLifeOSAction.reset_mock()
        self.client.runLifeOSAction.side_effect = None
        self.events.eventBus.reset_mock()
        self.logger.log.reset_mock()

    def test_poll_fetches_displays_and_acknowledges_events(self):
        self.client.runLifeOSAction.side_effect = [
            {
                "success": True,
                "data": {
                    "events": [
                        {"id": 4, "title": "First"},
                        {"id": 7, "title": "Second"},
                    ]
                },
            },
            {"success": True},
            {"success": True},
        ]

        last_event_id = self.notifications._poll_once(3)

        self.assertEqual(last_event_id, 7)
        self.assertEqual(
            self.client.runLifeOSAction.call_args_list,
            [
                call("list_events", {"after": 3, "limit": 100}),
                call(
                    "acknowledge_event",
                    {"event_id": 4, "idempotency_key": "ciel-notification-4"},
                ),
                call(
                    "acknowledge_event",
                    {"event_id": 7, "idempotency_key": "ciel-notification-7"},
                ),
            ],
        )
        self.assertEqual(self.events.eventBus.emit.call_count, 2)

    def test_poll_does_not_advance_past_failed_acknowledgement(self):
        self.client.runLifeOSAction.side_effect = [
            {
                "success": True,
                "data": {
                    "events": [
                        {"id": 4, "title": "Retry me"},
                        {"id": 5, "title": "Do not skip me"},
                    ]
                },
            },
            {"success": False, "error": "temporary failure"},
        ]

        last_event_id = self.notifications._poll_once(3)

        self.assertEqual(last_event_id, 3)
        self.assertEqual(self.events.eventBus.emit.call_count, 1)
        self.assertEqual(self.client.runLifeOSAction.call_count, 2)

    def test_poll_failure_preserves_cursor(self):
        self.client.runLifeOSAction.return_value = {
            "success": False,
            "error": "timed out",
        }

        self.assertEqual(self.notifications._poll_once(11), 11)
        self.logger.log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
