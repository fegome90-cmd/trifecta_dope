from types import SimpleNamespace

from src.application.daemon_use_case import DaemonUseCase


def make_use_case(stop_result: bool) -> DaemonUseCase:
    use_case = object.__new__(DaemonUseCase)
    use_case._manager = SimpleNamespace(stop=lambda: stop_result)
    use_case._health = SimpleNamespace(check=lambda: None)
    return use_case


def test_stop_reports_error_when_manager_stop_fails() -> None:
    use_case = make_use_case(stop_result=False)

    response = use_case.stop()

    assert response == {"status": "error", "running": True}
