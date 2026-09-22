import socket
import subprocess
import sys
import time

import pytest
import requests


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server_url():
    """Runs the app with uvicorn directly, per the implementation plan's note
    that E2E can target a temporary process here; #5 re-points this at the
    built container image."""
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                if requests.get(f"{url}/health", timeout=1).status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                time.sleep(0.2)
        else:
            process.terminate()
            raise RuntimeError("app server did not become healthy in time")
        yield url
    finally:
        process.terminate()
        process.wait(timeout=5)
