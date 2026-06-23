from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load_benchmark_module():
    module_path = ROOT / "scripts" / "benchmark_vague_prompts.py"
    spec = importlib.util.spec_from_file_location("benchmark_vague_prompts", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BenchmarkVaguePromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.benchmark = _load_benchmark_module()

    def test_benchmark_has_100_unique_prompts(self) -> None:
        prompts = self.benchmark.VAGUE_PROMPTS
        self.assertEqual(len(prompts), 100)
        self.assertEqual(len(set(prompts)), 100)

    def test_vague_prompt_benchmark_catches_at_least_90_percent(self) -> None:
        summary = self.benchmark.run_benchmark()
        self.assertGreaterEqual(
            summary["block_rate"],
            0.90,
            f"Missed prompts: {[row['prompt'] for row in summary['missed']]}",
        )


if __name__ == "__main__":
    unittest.main()
