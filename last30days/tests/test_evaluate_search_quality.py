"""Tests for the local search-quality evaluation harness."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import evaluate_search_quality as evalsq


class TestMetrics(unittest.TestCase):
    def test_jaccard(self):
        self.assertAlmostEqual(evalsq.jaccard({"a", "b"}, {"b", "c"}), 1 / 3)

    def test_retention(self):
        self.assertAlmostEqual(evalsq.retention({"a", "b"}, {"b", "c"}), 0.5)

    def test_precision_at_k(self):
        ranking = [
            {"key": "a", "source": "reddit"},
            {"key": "b", "source": "x"},
            {"key": "c", "source": "youtube"},
        ]
        judgments = {"a": 3, "b": 1, "c": 2}
        self.assertAlmostEqual(evalsq.precision_at_k(ranking, judgments, 2), 0.5)

    def test_ndcg_at_k(self):
        ranking = [
            {"key": "a", "source": "reddit"},
            {"key": "b", "source": "x"},
            {"key": "c", "source": "youtube"},
        ]
        judgments = {"a": 3, "b": 0, "c": 2}
        self.assertGreater(evalsq.ndcg_at_k(ranking, judgments, 3), 0.8)

    def test_ndcg_at_k_uses_best_items_from_judged_pool(self):
        ranking = [
            {"key": "a", "source": "reddit"},
            {"key": "b", "source": "x"},
            {"key": "c", "source": "youtube"},
        ]
        judged_pool = ranking + [
            {"key": "d", "source": "reddit"},
            {"key": "e", "source": "x"},
        ]
        judgments = {"a": 3, "b": 0, "c": 0, "d": 3, "e": 2}
        self.assertLess(
            evalsq.ndcg_at_k(ranking, judgments, 3, judged_pool),
            1.0,
        )

    def test_source_coverage_recall_uses_union_pool(self):
        judged_pool = [
            {"key": "a", "source": "reddit"},
            {"key": "b", "source": "x"},
            {"key": "c", "source": "youtube"},
        ]
        ranking = [
            {"key": "a", "source": "reddit"},
            {"key": "b", "source": "x"},
        ]
        judgments = {"a": 3, "b": 0, "c": 2}
        self.assertAlmostEqual(evalsq.source_coverage_recall(ranking, judged_pool, judgments), 0.5)


class TestRankedItems(unittest.TestCase):
    def test_build_ranked_items_sorts_by_score(self):
        report = {
            "reddit": [{"id": "R1", "title": "Low", "url": "r1", "score": 20}],
            "x": [{"id": "X1", "text": "High", "url": "x1", "score": 90}],
            "youtube": [],
            "tiktok": [],
            "instagram": [],
            "hackernews": [],
            "bluesky": [],
            "truthsocial": [],
            "polymarket": [],
            "websearch": [],
        }
        ranked = evalsq.build_ranked_items(report, per_source_limit=5)
        self.assertEqual(ranked[0]["key"], "x1")


class TestPathWithoutNode(unittest.TestCase):
    def test_removes_node_entries(self):
        path = "/usr/bin:/tmp/node-bin:/opt/homebrew/bin"

        def fake_exists(path_obj):
            return str(path_obj).endswith("/tmp/node-bin/node")

        with patch.object(evalsq.Path, "exists", fake_exists):
            filtered = evalsq.path_without_node(path)
        self.assertEqual(filtered, "/usr/bin:/opt/homebrew/bin")


class TestEvalToolPath(unittest.TestCase):
    def test_wraps_ytdlp_with_ignore_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            eval_home = Path(tmpdir)
            with patch.object(evalsq.shutil, "which", return_value="/opt/homebrew/bin/yt-dlp"):
                path_value = evalsq.create_eval_tool_path(eval_home, "/usr/bin")
            wrapper = eval_home / "bin" / "yt-dlp"
            self.assertTrue(wrapper.exists())
            text = wrapper.read_text()
            self.assertIn("--ignore-config", text)
            self.assertIn("--no-cookies-from-browser", text)
            self.assertEqual(path_value, f"{eval_home / 'bin'}:/usr/bin")


class TestJudgeKeyResolution(unittest.TestCase):
    def test_prefers_google_api_key(self):
        config = {
            "GOOGLE_API_KEY": "google-key",
            "GEMINI_API_KEY": "gem-key",
            "GOOGLE_GENAI_API_KEY": "genai-key",
        }
        self.assertEqual(evalsq.resolve_google_judge_api_key(config), "google-key")

    def test_falls_back_to_gemini_aliases(self):
        self.assertEqual(
            evalsq.resolve_google_judge_api_key({"GEMINI_API_KEY": "gem-key"}),
            "gem-key",
        )
        self.assertEqual(
            evalsq.resolve_google_judge_api_key({"GOOGLE_GENAI_API_KEY": "genai-key"}),
            "genai-key",
        )


if __name__ == "__main__":
    unittest.main()
