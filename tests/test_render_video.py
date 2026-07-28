import unittest

from scripts.render_video import fit_narration, tracked_box_position


class FitNarrationTests(unittest.TestCase):
    def test_keeps_narration_that_already_fits(self) -> None:
        duration, tempo = fit_narration(160.0, 162.0, 177.0)

        self.assertEqual(duration, 163.0)
        self.assertEqual(tempo, 1.0)

    def test_corrects_small_tts_duration_variation(self) -> None:
        duration, tempo = fit_narration(181.7, 162.0, 177.0)

        self.assertAlmostEqual(duration, 177.0)
        self.assertAlmostEqual(tempo, 181.7 / 174.0)

    def test_rejects_excessive_speedup(self) -> None:
        with self.assertRaisesRegex(SystemExit, "Shorten assets/audio/narration.txt"):
            fit_narration(200.0, 162.0, 177.0)

    def test_rejects_scene_plan_over_limit(self) -> None:
        with self.assertRaisesRegex(SystemExit, "Shorten data/scenes.json"):
            fit_narration(160.0, 180.0, 177.0)


class TrackedBoxTests(unittest.TestCase):
    def test_detection_box_moves_during_scene(self) -> None:
        box = {"x": 100, "y": 120, "w": 200, "h": 150}

        self.assertNotEqual(
            tracked_box_position(box, 0.0, 10.0),
            tracked_box_position(box, 2.0, 10.0),
        )

    def test_detection_box_stays_inside_frame(self) -> None:
        box = {
            "x": 1270, "y": 710, "w": 100, "h": 100,
            "motion": {"x": 200, "y": 200},
        }

        x, y, w, h = tracked_box_position(box, 2.0, 10.0)
        self.assertLessEqual(x + w, 1280)
        self.assertLessEqual(y + h, 720)


if __name__ == "__main__":
    unittest.main()
