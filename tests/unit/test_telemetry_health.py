import json
import tempfile
from pathlib import Path

import pytest

from src.application.telemetry_health import TelemetryHealth, run_health_check


@pytest.fixture
def temp_segment(tmp_path):
    tel_dir = tmp_path / "_ctx" / "telemetry"
    tel_dir.mkdir(parents=True)

    events_file = tel_dir / "events.jsonl"
    metrics_file = tel_dir / "metrics.json"
    last_run_file = tel_dir / "last_run.json"

    events_file.write_text("")
    metrics_file.write_text("{}")
    last_run_file.write_text("{}")

    return tmp_path


class TestTelemetryHealth:
    def test_no_telemetry_data(self, temp_segment):
        health = TelemetryHealth(temp_segment)
        exit_code, results = health.check_all()
        assert exit_code == 0
        assert len(results) == 0

    def test_lsp_ready_fail_invariant_fail(self, temp_segment):
        tel_dir = temp_segment / "_ctx" / "telemetry"
        metrics_file = tel_dir / "metrics.json"
        metrics_file.write_text(json.dumps({"lsp.ready_fail_invariant": 1}))

        health = TelemetryHealth(temp_segment)
        exit_code, results = health.check_all()

        assert exit_code == 3
        assert any("FAIL" in r.status for r in results)
        assert any("lsp.ready_fail_invariant" in r.message for r in results)

    def test_lsp_thread_alive_fail(self, temp_segment):
        tel_dir = temp_segment / "_ctx" / "telemetry"
        metrics_file = tel_dir / "metrics.json"
        metrics_file.write_text(json.dumps({"lsp.thread_alive_after_join": 1}))

        health = TelemetryHealth(temp_segment)
        exit_code, results = health.check_all()

        assert exit_code == 3
        assert any("FAIL" in r.status for r in results)

    def test_zero_hit_ratio_warn(self, temp_segment):
        tel_dir = temp_segment / "_ctx" / "telemetry"
        metrics_file = tel_dir / "metrics.json"
        metrics_file.write_text(
            json.dumps({"ctx_search_count": 100, "ctx_search_zero_hits_count": 40})
        )

        health = TelemetryHealth(temp_segment)
        exit_code, results = health.check_all()

        assert exit_code == 2
        assert any("WARN" in r.status for r in results)
        assert any("zero-hit ratio" in r.message.lower() for r in results)

    def test_zero_hit_ratio_ok(self, temp_segment):
        tel_dir = temp_segment / "_ctx" / "telemetry"
        metrics_file = tel_dir / "metrics.json"
        metrics_file.write_text(
            json.dumps({"ctx_search_count": 100, "ctx_search_zero_hits_count": 10})
        )

        health = TelemetryHealth(temp_segment)
        exit_code, results = health.check_all()

        assert exit_code == 0
        assert any("OK" in r.status for r in results)

    def test_run_health_check_returns_exit_code(self, temp_segment):
        exit_code = run_health_check(temp_segment)
        assert exit_code == 0
