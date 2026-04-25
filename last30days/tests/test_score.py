"""Tests for score module."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import schema, score


class TestLog1pSafe(unittest.TestCase):
    def test_positive_value(self):
        result = score.log1p_safe(100)
        self.assertGreater(result, 0)

    def test_zero(self):
        result = score.log1p_safe(0)
        self.assertEqual(result, 0)

    def test_none(self):
        result = score.log1p_safe(None)
        self.assertEqual(result, 0)

    def test_negative(self):
        result = score.log1p_safe(-5)
        self.assertEqual(result, 0)


class TestComputeRedditEngagementRaw(unittest.TestCase):
    def test_with_engagement(self):
        eng = schema.Engagement(score=100, num_comments=50, upvote_ratio=0.9)
        result = score.compute_reddit_engagement_raw(eng)
        self.assertIsNotNone(result)
        self.assertGreater(result, 0)

    def test_without_engagement(self):
        result = score.compute_reddit_engagement_raw(None)
        self.assertIsNone(result)

    def test_empty_engagement(self):
        eng = schema.Engagement()
        result = score.compute_reddit_engagement_raw(eng)
        self.assertIsNone(result)


class TestComputeXEngagementRaw(unittest.TestCase):
    def test_with_engagement(self):
        eng = schema.Engagement(likes=100, reposts=25, replies=15, quotes=5)
        result = score.compute_x_engagement_raw(eng)
        self.assertIsNotNone(result)
        self.assertGreater(result, 0)

    def test_without_engagement(self):
        result = score.compute_x_engagement_raw(None)
        self.assertIsNone(result)


class TestNormalizeTo100(unittest.TestCase):
    def test_normalizes_values(self):
        values = [0, 50, 100]
        result = score.normalize_to_100(values)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 50)
        self.assertEqual(result[2], 100)

    def test_handles_none(self):
        values = [0, None, 100]
        result = score.normalize_to_100(values)
        self.assertIsNone(result[1])

    def test_single_value(self):
        values = [50]
        result = score.normalize_to_100(values)
        self.assertEqual(result[0], 50)


class TestScoreRedditItems(unittest.TestCase):
    def test_scores_items(self):
        today = datetime.now(timezone.utc).date().isoformat()
        items = [
            schema.RedditItem(
                id="R1",
                title="Test",
                url="https://reddit.com/r/test/1",
                subreddit="test",
                date=today,
                date_confidence="high",
                engagement=schema.Engagement(score=100, num_comments=50, upvote_ratio=0.9),
                relevance=0.9,
            ),
            schema.RedditItem(
                id="R2",
                title="Test 2",
                url="https://reddit.com/r/test/2",
                subreddit="test",
                date=today,
                date_confidence="high",
                engagement=schema.Engagement(score=10, num_comments=5, upvote_ratio=0.8),
                relevance=0.5,
            ),
        ]

        result = score.score_reddit_items(items)

        self.assertEqual(len(result), 2)
        self.assertGreater(result[0].score, 0)
        self.assertGreater(result[1].score, 0)
        # Higher relevance and engagement should score higher
        self.assertGreater(result[0].score, result[1].score)

    def test_empty_list(self):
        result = score.score_reddit_items([])
        self.assertEqual(result, [])


class TestScoreXItems(unittest.TestCase):
    def test_scores_items(self):
        today = datetime.now(timezone.utc).date().isoformat()
        items = [
            schema.XItem(
                id="X1",
                text="Test post",
                url="https://x.com/user/1",
                author_handle="user1",
                date=today,
                date_confidence="high",
                engagement=schema.Engagement(likes=100, reposts=25, replies=15, quotes=5),
                relevance=0.9,
            ),
        ]

        result = score.score_x_items(items)

        self.assertEqual(len(result), 1)
        self.assertGreater(result[0].score, 0)


class TestSortItems(unittest.TestCase):
    def test_sorts_by_score_descending(self):
        items = [
            schema.RedditItem(id="R1", title="Low", url="", subreddit="", score=30),
            schema.RedditItem(id="R2", title="High", url="", subreddit="", score=90),
            schema.RedditItem(id="R3", title="Mid", url="", subreddit="", score=60),
        ]

        result = score.sort_items(items)

        self.assertEqual(result[0].id, "R2")
        self.assertEqual(result[1].id, "R3")
        self.assertEqual(result[2].id, "R1")

    def test_stable_sort(self):
        items = [
            schema.RedditItem(id="R1", title="A", url="", subreddit="", score=50),
            schema.RedditItem(id="R2", title="B", url="", subreddit="", score=50),
        ]

        result = score.sort_items(items)

        # Both have same score, should maintain order by title
        self.assertEqual(len(result), 2)


class TestCommentQualityWeight(unittest.TestCase):
    """Test that top comment score boosts Reddit engagement."""

    def test_comment_boosts_score(self):
        eng = schema.Engagement(score=100, num_comments=50, upvote_ratio=0.9)
        without_comment = score.compute_reddit_engagement_raw(eng, top_comment_score=None)
        with_comment = score.compute_reddit_engagement_raw(eng, top_comment_score=500)
        self.assertGreater(with_comment, without_comment)


class TestInstagramEngagement(unittest.TestCase):
    """Tests for compute_instagram_engagement_raw()."""

    def test_basic(self):
        eng = schema.Engagement(views=10000, likes=500, num_comments=50)
        raw = score.compute_instagram_engagement_raw(eng)
        self.assertIsNotNone(raw)
        self.assertGreater(raw, 0)

    def test_views_dominate(self):
        views_only = schema.Engagement(views=10000)
        likes_only = schema.Engagement(likes=10000)
        self.assertGreater(
            score.compute_instagram_engagement_raw(views_only),
            score.compute_instagram_engagement_raw(likes_only),
        )


class TestBlueskyEngagement(unittest.TestCase):
    """Tests for compute_bluesky_engagement_raw()."""

    def test_basic(self):
        eng = schema.Engagement(likes=100, reposts=25, replies=15, quotes=5)
        raw = score.compute_bluesky_engagement_raw(eng)
        self.assertIsNotNone(raw)
        self.assertGreater(raw, 0)

    def test_likes_dominate(self):
        likes_heavy = schema.Engagement(likes=1000, reposts=0, replies=0, quotes=0)
        reposts_heavy = schema.Engagement(likes=0, reposts=1000, replies=0, quotes=0)
        self.assertGreater(
            score.compute_bluesky_engagement_raw(likes_heavy),
            score.compute_bluesky_engagement_raw(reposts_heavy),
        )

    def test_none_engagement(self):
        self.assertIsNone(score.compute_bluesky_engagement_raw(None))

    def test_no_likes_no_reposts(self):
        eng = schema.Engagement(replies=10)
        self.assertIsNone(score.compute_bluesky_engagement_raw(eng))


class TestTruthSocialEngagement(unittest.TestCase):
    """Tests for compute_truthsocial_engagement_raw()."""

    def test_basic(self):
        eng = schema.Engagement(likes=100, reposts=25, replies=15)
        raw = score.compute_truthsocial_engagement_raw(eng)
        self.assertIsNotNone(raw)
        self.assertGreater(raw, 0)

    def test_likes_dominate(self):
        likes_heavy = schema.Engagement(likes=1000, reposts=0, replies=0)
        reposts_heavy = schema.Engagement(likes=0, reposts=1000, replies=0)
        self.assertGreater(
            score.compute_truthsocial_engagement_raw(likes_heavy),
            score.compute_truthsocial_engagement_raw(reposts_heavy),
        )

    def test_none_engagement(self):
        self.assertIsNone(score.compute_truthsocial_engagement_raw(None))


class TestScoreBlueskyItems(unittest.TestCase):
    """Tests for score_bluesky_items()."""

    def test_scores_items(self):
        items = [
            schema.BlueskyItem(
                id="bsky1", text="Test", url="https://bsky.app/1",
                author_handle="user.bsky.social", display_name="User",
                engagement=schema.Engagement(likes=50, reposts=10, replies=5, quotes=2),
                relevance=0.8,
            ),
        ]
        result = score.score_bluesky_items(items)
        self.assertEqual(len(result), 1)
        self.assertGreater(result[0].score, 0)

    def test_empty_list(self):
        self.assertEqual(score.score_bluesky_items([]), [])


class TestScoreTruthSocialItems(unittest.TestCase):
    """Tests for score_truthsocial_items()."""

    def test_scores_items(self):
        items = [
            schema.TruthSocialItem(
                id="ts1", text="Test", url="https://truthsocial.com/1",
                author_handle="@user", display_name="User",
                engagement=schema.Engagement(likes=50, reposts=10, replies=5),
                relevance=0.8,
            ),
        ]
        result = score.score_truthsocial_items(items)
        self.assertEqual(len(result), 1)
        self.assertGreater(result[0].score, 0)

    def test_empty_list(self):
        self.assertEqual(score.score_truthsocial_items([]), [])


class TestSortItemsMixedSources(unittest.TestCase):
    """Test sort_items with Bluesky and TruthSocial items."""

    def test_bluesky_item_sorts(self):
        items = [
            schema.RedditItem(id="R1", title="Reddit", url="", subreddit="", score=30),
            schema.BlueskyItem(id="B1", text="Bluesky", url="", author_handle="u.bsky.social", display_name="U", score=90),
        ]
        result = score.sort_items(items)
        self.assertEqual(result[0].id, "B1")

    def test_truthsocial_item_sorts(self):
        items = [
            schema.RedditItem(id="R1", title="Reddit", url="", subreddit="", score=30),
            schema.TruthSocialItem(id="T1", text="TS", url="", author_handle="@u", display_name="U", score=90),
        ]
        result = score.sort_items(items)
        self.assertEqual(result[0].id, "T1")


class TestRelevanceFilter(unittest.TestCase):
    """Tests for relevance_filter()."""

    def _make_items(self, relevances):
        """Helper: create RedditItems with given relevance values."""
        return [
            schema.RedditItem(id=f"R{i}", title=f"Item {i}", url="", subreddit="", relevance=r)
            for i, r in enumerate(relevances)
        ]

    def test_filters_below_threshold(self):
        items = self._make_items([0.8, 0.1, 0.5, 0.2])
        result = score.relevance_filter(items, "TEST", threshold=0.3)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(i.relevance >= 0.3 for i in result))

    def test_small_list_unchanged(self):
        items = self._make_items([0.1, 0.05, 0.02])
        result = score.relevance_filter(items, "TEST")
        self.assertEqual(len(result), 3)

    def test_all_below_threshold_keeps_top_3(self):
        items = self._make_items([0.1, 0.25, 0.05, 0.2, 0.15])
        result = score.relevance_filter(items, "TEST", threshold=0.3)
        self.assertEqual(len(result), 3)
        # Should be sorted by relevance: 0.25, 0.2, 0.15
        self.assertEqual(result[0].relevance, 0.25)
        self.assertEqual(result[1].relevance, 0.2)

    def test_empty_list(self):
        result = score.relevance_filter([], "TEST")
        self.assertEqual(result, [])

    def test_items_without_relevance_attr_treated_as_zero(self):
        """Objects lacking a relevance attribute get 0.0, failing the filter."""
        class BareItem:
            def __init__(self, id):
                self.id = id
        items = [
            schema.RedditItem(id="R0", title="Has relevance", url="", subreddit="", relevance=0.8),
            BareItem("B1"),
            BareItem("B2"),
            BareItem("B3"),
        ]
        result = score.relevance_filter(items, "TEST", threshold=0.3)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "R0")


if __name__ == "__main__":
    unittest.main()
