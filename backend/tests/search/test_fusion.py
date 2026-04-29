import unittest

from app.services.search.fusion import fuse_and_filter


class FuseAndFilterTest(unittest.TestCase):
    def test_alpha_zero_returns_text_only_ranking(self) -> None:
        image_scores = {"P1": 1.0, "P2": 0.0}      # would dominate at α>0
        text_scores = {"P1": 0.1, "P2": 0.9}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.0, tau=0.0)
        self.assertEqual([pid for pid, _ in ranked], ["P2", "P1"])

    def test_alpha_one_returns_image_only_ranking(self) -> None:
        image_scores = {"P1": 0.9, "P2": 0.1}
        text_scores = {"P1": 0.1, "P2": 0.9}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=1.0, tau=0.0)
        self.assertEqual([pid for pid, _ in ranked], ["P1", "P2"])

    def test_union_with_missing_side_filled_with_zero(self) -> None:
        image_scores = {"P1": 0.8}
        text_scores = {"P2": 0.8}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.0)
        ids = [pid for pid, _ in ranked]
        self.assertEqual(set(ids), {"P1", "P2"})

    def test_outlier_cut_at_tau_times_top1(self) -> None:
        # post-fusion finals should be 1.0, 0.7, 0.5, 0.0 (top-1 = 1.0)
        # tau=0.6 → cut at 0.6 → keep 1.0 and 0.7
        image_scores = {"A": 1.0, "B": 0.7, "C": 0.5, "D": 0.0}
        text_scores = {"A": 1.0, "B": 0.7, "C": 0.5, "D": 0.0}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.6)
        ids = [pid for pid, _ in ranked]
        self.assertEqual(ids, ["A", "B"])

    def test_all_equal_scores_does_not_div_by_zero(self) -> None:
        image_scores = {"A": 0.5, "B": 0.5, "C": 0.5}
        text_scores = {"A": 0.5, "B": 0.5, "C": 0.5}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.0)
        # all equal → all kept, finite numbers
        self.assertEqual(len(ranked), 3)
        for _pid, score in ranked:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_empty_inputs_returns_empty(self) -> None:
        self.assertEqual(fuse_and_filter({}, {}, alpha=0.5, tau=0.6), [])

    def test_top1_zero_skips_outlier_cut(self) -> None:
        # Pathological: all candidates have final score 0.
        image_scores = {"A": 0.0, "B": 0.0}
        text_scores = {"A": 0.0, "B": 0.0}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.6)
        self.assertEqual(len(ranked), 2)


if __name__ == "__main__":
    unittest.main()
