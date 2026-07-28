import unittest

from scripts.render_video import fit_narration


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


if __name__ == "__main__":
    unittest.main()
