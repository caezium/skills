"""Tests for models module."""

import sys
import unittest
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import models


class TestParseVersion(unittest.TestCase):
    def test_simple_version(self):
        result = models.parse_version("gpt-5")
        self.assertEqual(result, (5,))

    def test_minor_version(self):
        result = models.parse_version("gpt-5.2")
        self.assertEqual(result, (5, 2))

    def test_patch_version(self):
        result = models.parse_version("gpt-5.2.1")
        self.assertEqual(result, (5, 2, 1))

    def test_no_version(self):
        result = models.parse_version("custom-model")
        self.assertIsNone(result)


class TestIsSearchCapableModel(unittest.TestCase):
    def test_gpt5_is_capable(self):
        """gpt-5 supports web_search when reasoning is not set to 'minimal'.

        Per OpenAI docs, gpt-5 with reasoning effort="minimal" does NOT
        support web_search. We never set reasoning params (our usage is
        tool invocation + JSON extraction only), so gpt-5 is safe here.
        """
        self.assertTrue(models.is_search_capable_model("gpt-5"))

    def test_gpt52_is_capable(self):
        self.assertTrue(models.is_search_capable_model("gpt-5.2"))

    def test_gpt5_mini_is_capable(self):
        self.assertTrue(models.is_search_capable_model("gpt-5-mini"))

    def test_gpt41_mini_is_capable(self):
        self.assertTrue(models.is_search_capable_model("gpt-4.1-mini"))

    def test_gpt4o_is_capable(self):
        self.assertTrue(models.is_search_capable_model("gpt-4o"))

    def test_gpt4o_mini_not_capable(self):
        """gpt-4o-mini does not support web_search with domain filtering."""
        self.assertFalse(models.is_search_capable_model("gpt-4o-mini"))

    def test_nano_not_capable(self):
        """nano models don't support web_search."""
        self.assertFalse(models.is_search_capable_model("gpt-4.1-nano"))
        self.assertFalse(models.is_search_capable_model("gpt-5-nano"))

    def test_gpt4_not_capable(self):
        self.assertFalse(models.is_search_capable_model("gpt-4"))

    def test_codex_not_capable(self):
        self.assertFalse(models.is_search_capable_model("gpt-5.1-codex"))

    def test_backward_compat_alias(self):
        """is_mainline_openai_model still works as alias."""
        self.assertTrue(models.is_mainline_openai_model("gpt-5"))


class TestSelectOpenAIModel(unittest.TestCase):
    def setUp(self):
        from lib import cache
        cache.MODEL_CACHE_FILE.unlink(missing_ok=True)

    def test_pinned_policy(self):
        result = models.select_openai_model(
            "fake-key",
            policy="pinned",
            pin="gpt-5.1"
        )
        self.assertEqual(result, "gpt-5.1")

    def test_prefers_mini_over_mainline(self):
        """Mini models should be preferred for cost-efficiency."""
        mock_models = [
            {"id": "gpt-5.2", "created": 1704067200},
            {"id": "gpt-5-mini", "created": 1704067200},
            {"id": "gpt-5.1", "created": 1701388800},
        ]
        result = models.select_openai_model(
            "fake-key",
            policy="auto",
            mock_models=mock_models
        )
        self.assertEqual(result, "gpt-5-mini")

    def test_prefers_newer_generation_mini(self):
        """gpt-5-mini should beat gpt-4.1-mini (newer generation)."""
        mock_models = [
            {"id": "gpt-4.1-mini", "created": 1701388800},
            {"id": "gpt-5-mini", "created": 1704067200},
            {"id": "gpt-4.1", "created": 1698710400},
        ]
        result = models.select_openai_model(
            "fake-key",
            policy="auto",
            mock_models=mock_models
        )
        self.assertEqual(result, "gpt-5-mini")

    def test_falls_back_to_mainline_when_no_mini(self):
        """Without mini models, mainline models are selected."""
        mock_models = [
            {"id": "gpt-5.2", "created": 1704067200},
            {"id": "gpt-4.1", "created": 1698710400},
        ]
        result = models.select_openai_model(
            "fake-key",
            policy="auto",
            mock_models=mock_models
        )
        self.assertEqual(result, "gpt-5.2")

    def test_filters_unsupported_variants(self):
        """Nano, codex, preview models should be excluded."""
        mock_models = [
            {"id": "gpt-5-nano", "created": 1704067200},
            {"id": "gpt-5.1-codex", "created": 1704067200},
            {"id": "gpt-4o-mini", "created": 1704067200},
            {"id": "gpt-4.1-mini", "created": 1698710400},
        ]
        result = models.select_openai_model(
            "fake-key",
            policy="auto",
            mock_models=mock_models
        )
        self.assertEqual(result, "gpt-4.1-mini")


class TestSelectOpenAIModelErrorPaths(unittest.TestCase):
    def setUp(self):
        from lib import cache
        cache.MODEL_CACHE_FILE.unlink(missing_ok=True)

    def test_http_error_returns_fallback(self):
        """HTTPError during model fetch should return fallback, not crash."""
        from unittest.mock import patch
        from lib import http
        with patch('lib.http.get', side_effect=http.HTTPError("Unauthorized", status_code=401)):
            result = models.select_openai_model("bad-key", policy="auto")
        self.assertEqual(result, models.OPENAI_FALLBACK_MODELS[0])

    def test_http_403_returns_fallback(self):
        from unittest.mock import patch
        from lib import http
        with patch('lib.http.get', side_effect=http.HTTPError("Forbidden", status_code=403)):
            result = models.select_openai_model("bad-key", policy="auto")
        self.assertEqual(result, models.OPENAI_FALLBACK_MODELS[0])


class TestSelectXAIModel(unittest.TestCase):
    def test_latest_policy(self):
        result = models.select_xai_model(
            "fake-key",
            policy="latest"
        )
        self.assertEqual(result, "grok-4-1-fast-non-reasoning")

    def test_stable_policy(self):
        # Clear cache first to avoid interference
        from lib import cache
        cache.MODEL_CACHE_FILE.unlink(missing_ok=True)
        result = models.select_xai_model(
            "fake-key",
            policy="stable"
        )
        self.assertEqual(result, "grok-4-1-fast-non-reasoning")

    def test_pinned_policy(self):
        result = models.select_xai_model(
            "fake-key",
            policy="pinned",
            pin="grok-3"
        )
        self.assertEqual(result, "grok-3")


class TestGetModels(unittest.TestCase):
    def setUp(self):
        from lib import cache
        cache.MODEL_CACHE_FILE.unlink(missing_ok=True)

    def test_no_keys_returns_none(self):
        config = {}
        result = models.get_models(config)
        self.assertIsNone(result["openai"])
        self.assertIsNone(result["xai"])

    def test_openai_key_only(self):
        config = {"OPENAI_API_KEY": "sk-test"}
        mock_models = [
            {"id": "gpt-5.2", "created": 1704067200},
            {"id": "gpt-5-mini", "created": 1704067200},
        ]
        result = models.get_models(config, mock_openai_models=mock_models)
        self.assertEqual(result["openai"], "gpt-5-mini")
        self.assertIsNone(result["xai"])

    def test_both_keys(self):
        config = {
            "OPENAI_API_KEY": "sk-test",
            "XAI_API_KEY": "xai-test",
        }
        mock_openai = [
            {"id": "gpt-5.2", "created": 1704067200},
            {"id": "gpt-5-mini", "created": 1704067200},
        ]
        mock_xai = [{"id": "grok-4-1-fast-non-reasoning", "created": 1704067200}]
        result = models.get_models(config, mock_openai, mock_xai)
        self.assertEqual(result["openai"], "gpt-5-mini")
        self.assertEqual(result["xai"], "grok-4-1-fast-non-reasoning")


if __name__ == "__main__":
    unittest.main()
