import unittest

from app.services.search.aggregator import aggregate_image_scores


class AggregateImageScoresTest(unittest.TestCase):
    def test_top_k_mean_with_more_than_k_images(self) -> None:
        # product P has 5 image scores; top-3 mean = mean(0.9, 0.8, 0.7) = 0.8
        rows = [
            ("img1", "P", 0.5),
            ("img2", "P", 0.9),
            ("img3", "P", 0.7),
            ("img4", "P", 0.3),
            ("img5", "P", 0.8),
        ]
        result = aggregate_image_scores(rows, top_k=3)
        self.assertAlmostEqual(result["P"], 0.8, places=6)

    def test_top_k_mean_with_fewer_than_k_images(self) -> None:
        # only 2 images for P → mean of those 2
        rows = [("img1", "P", 0.6), ("img2", "P", 0.4)]
        result = aggregate_image_scores(rows, top_k=3)
        self.assertAlmostEqual(result["P"], 0.5, places=6)

    def test_multiple_products_independent(self) -> None:
        rows = [
            ("a", "P1", 0.9),
            ("b", "P1", 0.1),
            ("c", "P2", 0.4),
            ("d", "P2", 0.6),
        ]
        result = aggregate_image_scores(rows, top_k=1)
        self.assertAlmostEqual(result["P1"], 0.9, places=6)
        self.assertAlmostEqual(result["P2"], 0.6, places=6)

    def test_empty_rows_returns_empty_dict(self) -> None:
        self.assertEqual(aggregate_image_scores([], top_k=3), {})

    def test_input_order_does_not_matter(self) -> None:
        rows_a = [("x", "P", 0.1), ("y", "P", 0.9), ("z", "P", 0.5)]
        rows_b = [("y", "P", 0.9), ("z", "P", 0.5), ("x", "P", 0.1)]
        self.assertEqual(
            aggregate_image_scores(rows_a, top_k=2),
            aggregate_image_scores(rows_b, top_k=2),
        )

    def test_top_k_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            aggregate_image_scores([("a", "P", 0.5)], top_k=0)


if __name__ == "__main__":
    unittest.main()
