"""Small, fast integration tests for benchmark and dashboard generation."""

from __future__ import annotations

import json
import tempfile
import unittest
import weakref
from pathlib import Path
from unittest.mock import patch

import benchmark as benchmark_module
from benchmark import (
    ALGORITHMS,
    SCENARIOS,
    AlgorithmSpec,
    _build_fixed_inputs,
    _measure_fixed_inputs,
    _measure_memory,
    run_benchmarks,
    write_results,
)
from dashboard import build_dashboard


class BenchmarkPipelineTests(unittest.TestCase):
    def test_fixed_case_matrix_is_shared_by_every_algorithm(self) -> None:
        sizes = [4]
        query_counts = [1, 3]
        run = run_benchmarks(
            sizes,
            query_counts,
            scenarios=SCENARIOS,
            repeats=2,
            base_seed=12,
        )

        expected_cases = len(sizes) * len(query_counts) * len(SCENARIOS)
        self.assertEqual(len(run.cases), expected_cases)
        self.assertEqual(len(run.raw_results), expected_cases * len(ALGORITHMS) * 2)
        self.assertEqual(len(run.summary), expected_cases * len(ALGORITHMS))
        self.assertEqual(len(run.memory_results), expected_cases * len(ALGORITHMS))

        for case in run.cases:
            case_rows = [row for row in run.raw_results if row.case_id == case.case_id]
            self.assertEqual(
                {row.algorithm for row in case_rows},
                {algorithm.name for algorithm in ALGORITHMS},
            )
            self.assertEqual({row.input_sha256 for row in case_rows}, {case.input_sha256})
            # Each metric is an independently batched timing sample. Total
            # brackets both operations, but noise means its average is not a
            # mathematical sum of the other two independently sampled values.
            self.assertTrue(all(row.preparation_ns > 0 for row in case_rows))
            self.assertTrue(all(row.query_batch_ns > 0 for row in case_rows))
            self.assertTrue(all(row.combined_ns > 0 for row in case_rows))
            self.assertTrue(all(row.preparation_calls >= 1 for row in case_rows))
            self.assertTrue(all(row.query_batch_calls >= 1 for row in case_rows))
            self.assertTrue(all(row.combined_calls >= 1 for row in case_rows))

        self.assertEqual(
            run.metadata["units"]["raw_timings"],
            "nanoseconds per call",
        )
        self.assertEqual(run.metadata["units"]["traced_memory"], "bytes")
        self.assertIn("python_version", run.metadata["environment"])
        self.assertIn("machine", run.metadata["environment"])
        self.assertIn("git_commit", run.metadata["code_version"])

        for memory_result in run.memory_results:
            self.assertGreaterEqual(
                memory_result.peak_traced_bytes,
                memory_result.current_traced_bytes,
            )
            self.assertFalse(memory_result.input_included)
            self.assertTrue(memory_result.preparation_included)
            self.assertTrue(memory_result.output_included)

    def test_results_and_dashboard_are_reproducible_artifacts(self) -> None:
        run = run_benchmarks(
            [3],
            [1],
            scenarios=("mixed",),
            repeats=1,
            base_seed=7,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            artifacts = write_results(run, output_directory)
            dashboard_path = build_dashboard(
                artifacts["results_json"],
                output_directory / "runtime_dashboard.html",
            )

            payload = json.loads(
                artifacts["results_json"].read_text(encoding="utf-8")
            )
            dashboard = dashboard_path.read_text(encoding="utf-8")

            self.assertEqual(len(payload["summary"]), len(ALGORITHMS))
            self.assertTrue(artifacts["raw_csv"].is_file())
            self.assertTrue(artifacts["summary_csv"].is_file())
            self.assertTrue(artifacts["memory_csv"].is_file())
            self.assertTrue(artifacts["input_manifest_json"].is_file())
            self.assertIn("Search runtime dashboard", dashboard)
            self.assertIn("Binary search iterative v2", dashboard)
            self.assertIn("Preparation median", dashboard)
            self.assertIn("Peak traced memory", dashboard)
            self.assertIn('id="query-count"', dashboard)
            self.assertIn('id="scenario"', dashboard)
            self.assertIn("Preparation time", dashboard)
            self.assertIn("Query-batch time", dashboard)
            self.assertIn("Total time", dashboard)
            self.assertIn("Original vs revised", dashboard)
            self.assertIn("Raw repeats", dashboard)
            self.assertIn("Environment details", dashboard)
            self.assertIn("const benchmarkData =", dashboard)
            self.assertIn("Input length (log scale)", dashboard)
            self.assertIn("Preparation calls", dashboard)
            self.assertIn("Clock resolution", dashboard)

    def test_previous_algorithm_state_is_released_before_next_prepare(self) -> None:
        """Regression test for audit finding B1 (destruction charged to next method)."""

        class State:
            pass

        previous_state: weakref.ReferenceType[State] | None = None

        def prepare_first(_ids: object) -> State:
            nonlocal previous_state
            state = State()
            previous_state = weakref.ref(state)
            return state

        def prepare_second(_ids: object) -> State:
            self.assertIsNotNone(previous_state)
            self.assertIsNone(previous_state())
            return State()

        algorithms = (
            AlgorithmSpec("first", "v1", prepare_first, lambda _state, _q: [False]),
            AlgorithmSpec("second", "v1", prepare_second, lambda _state, _q: [False]),
        )
        fixed_inputs = _build_fixed_inputs(
            [1],
            [1],
            ("all_absent",),
            base_seed=1,
        )

        with patch.object(benchmark_module, "ALGORITHMS", algorithms):
            _measure_fixed_inputs(
                fixed_inputs,
                repeats=1,
                min_timing_window_ns=1_000,
                max_timing_calls=10,
            )

    def test_duplicate_dimensions_are_rejected_before_case_ids_collide(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate array sizes"):
            _build_fixed_inputs([10, 10], [1], ("mixed",), base_seed=1)
        with self.assertRaisesRegex(ValueError, "duplicate query counts"):
            _build_fixed_inputs([10], [1, 1], ("mixed",), base_seed=1)
        with self.assertRaisesRegex(ValueError, "duplicate scenarios"):
            _build_fixed_inputs(
                [10],
                [1],
                ("mixed", "mixed"),
                base_seed=1,
            )

    def test_short_operations_are_batched_and_clock_resolution_is_recorded(self) -> None:
        run = run_benchmarks(
            [1],
            [1],
            scenarios=("all_absent",),
            repeats=1,
            base_seed=2,
            min_timing_window_ns=100_000,
            max_timing_calls=10_000,
        )

        hash_row = next(
            row for row in run.raw_results if row.algorithm == "Hash set membership"
        )
        self.assertGreater(hash_row.preparation_calls, 1)
        self.assertGreater(hash_row.query_batch_calls, 1)
        self.assertGreater(hash_row.combined_calls, 1)
        clock = run.metadata["benchmark_settings"]["clock"]
        self.assertEqual(clock["name"], "time.perf_counter_ns")
        self.assertGreater(clock["resolution_ns"], 0)
        self.assertGreaterEqual(clock["timer_overhead_ns_median"], 0)

    def test_memory_scope_excludes_prebuilt_input_and_includes_known_allocation(self) -> None:
        allocation_size = 20_000

        def prepare(ids: object) -> tuple[object, bytearray]:
            return ids, bytearray(allocation_size)

        algorithms = (
            AlgorithmSpec(
                "allocation probe",
                "v1",
                prepare,
                lambda _state, queries: [False for _ in queries],
            ),
        )
        fixed_inputs = _build_fixed_inputs(
            [100],
            [1],
            ("all_absent",),
            base_seed=9,
        )

        with patch.object(benchmark_module, "ALGORITHMS", algorithms):
            result = _measure_memory(fixed_inputs)[0]

        self.assertFalse(result.input_included)
        self.assertTrue(result.preparation_included)
        self.assertTrue(result.output_included)
        self.assertGreaterEqual(result.current_traced_bytes, allocation_size)
        self.assertGreaterEqual(result.peak_traced_bytes, result.current_traced_bytes)


if __name__ == "__main__":
    unittest.main()
