"""Tests for bird_x module."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import bird_x


class TestExtractCoreSubject(unittest.TestCase):
    def tearDown(self):
        bird_x._credentials.clear()

    def test_strips_trending_noise(self):
        result = bird_x._extract_core_subject("trendiest Claude Code skills")
        self.assertNotIn("trendiest", result)
        self.assertIn("claude", result.lower())

    def test_strips_tool_noise(self):
        result = bird_x._extract_core_subject("best AI tools for coding")
        self.assertNotIn("tools", result)
        self.assertNotIn("best", result)

    def test_strips_skill_noise(self):
        result = bird_x._extract_core_subject("top claude code skills")
        self.assertNotIn("skills", result)
        self.assertNotIn("top", result)


class TestBirdSearchRetries(unittest.TestCase):
    def tearDown(self):
        bird_x._credentials.clear()

    def test_last_chance_retry_uses_strongest_token(self):
        """When shorter retry also returns 0, uses longest non-noise token."""
        empty = {"items": []}
        with mock.patch.object(bird_x, "_extract_core_subject", return_value="best codex skill plugin"), \
             mock.patch.object(bird_x, "parse_bird_response", return_value=[]), \
             mock.patch.object(bird_x, "_run_bird_search", return_value=empty) as run_mock:
            bird_x.search_x("best codex skill plugin", "2026-01-01", "2026-01-31", depth="quick")

        # Should try: original, shorter (2-word), last-chance (strongest token)
        self.assertEqual(run_mock.call_count, 3)
        queries = [call.args[0] for call in run_mock.call_args_list]
        # Last call should use "codex" (longest non-noise word)
        self.assertIn("codex", queries[2])

    def test_no_retry_when_first_query_has_results(self):
        """No retry when first query succeeds."""
        result = {"items": [{"id": "1"}]}
        with mock.patch.object(bird_x, "_extract_core_subject", return_value="nano banana"), \
             mock.patch.object(bird_x, "parse_bird_response", return_value=[{"id": "1"}]), \
             mock.patch.object(bird_x, "_run_bird_search", return_value=result) as run_mock:
            bird_x.search_x("nano banana prompting", "2026-01-01", "2026-01-31")

        self.assertEqual(run_mock.call_count, 1)


class TestBirdAuthEnvironment(unittest.TestCase):
    def tearDown(self):
        bird_x._credentials.clear()

    def test_subprocess_env_disables_browser_cookie_fallback_when_injected(self):
        bird_x.set_credentials("auth-token", "ct0-token")

        env = bird_x._subprocess_env()

        self.assertEqual(env["AUTH_TOKEN"], "auth-token")
        self.assertEqual(env["CT0"], "ct0-token")
        self.assertEqual(env["BIRD_DISABLE_BROWSER_COOKIES"], "1")

    def test_is_bird_authenticated_short_circuits_when_credentials_injected(self):
        bird_x.set_credentials("auth-token", "ct0-token")

        with mock.patch.object(bird_x, "is_bird_installed", return_value=True), \
             mock.patch.object(bird_x.subprocess, "run") as run_mock:
            result = bird_x.is_bird_authenticated()

        self.assertEqual(result, "env AUTH_TOKEN")
        run_mock.assert_not_called()

    def test_search_handles_passes_injected_credentials_to_subprocess(self):
        bird_x.set_credentials("auth-token", "ct0-token")

        proc = mock.Mock()
        proc.communicate.return_value = ("[]", "")
        proc.returncode = 0

        with mock.patch.object(bird_x.subprocess, "Popen", return_value=proc) as popen_mock:
            bird_x.search_handles(["openai"], "codex vs claude code", "2026-01-01", count_per=1)

        env = popen_mock.call_args.kwargs["env"]
        self.assertEqual(env["AUTH_TOKEN"], "auth-token")
        self.assertEqual(env["CT0"], "ct0-token")
        self.assertEqual(env["BIRD_DISABLE_BROWSER_COOKIES"], "1")


if __name__ == "__main__":
    unittest.main()
