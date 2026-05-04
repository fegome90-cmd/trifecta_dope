import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Generator

import pytest

@pytest.fixture(scope="session")
def trifecta_wheel(tmp_path_factory) -> Path:
    """Build a wheel of trifecta for testing installation."""
    dist_dir = tmp_path_factory.mktemp("dist")
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)],
        check=True,
        capture_output=True
    )
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        pytest.fail("Failed to build trifecta wheel")
    return wheels[0]

@pytest.fixture
def clean_machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, trifecta_wheel: Path) -> Generator[Path, None, None]:
    """
    Simulates a clean machine by isolating HOME and PATH.
    Provides a virtual environment with trifecta installed from wheel.
    """
    # 1. Setup isolated directories
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    venv_dir = tmp_path / "venv"
    
    # 2. Isolate environment
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home)) # Windows compatibility
    
    # 3. Create virtual environment
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    
    # 4. Install trifecta from wheel
    pip_exe = venv_dir / "bin" / "pip" if os.name != "nt" else venv_dir / "Scripts" / "pip.exe"
    subprocess.run([str(pip_exe), "install", str(trifecta_wheel)], check=True)
    
    # 5. Update PATH to only include venv and basic system binaries
    # Note: On macOS/Linux, we usually need /bin, /usr/bin for basic commands
    venv_bin = venv_dir / "bin" if os.name != "nt" else venv_dir / "Scripts"
    new_path = f"{venv_bin}{os.pathsep}/usr/bin{os.pathsep}/bin"
    monkeypatch.setenv("PATH", new_path)
    
    # Yield the fake home for assertions
    yield fake_home
