import os
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
    """Where the browser tests point.

    If E2E_BASE_URL is set (by scripts/test-e2e.sh / `make test-e2e`), the
    tests run against that already-running container image. Otherwise they
    fall back to starting the app with uvicorn, which is handy for a quick
    local check but does not prove the built image works.
    """
    external = os.environ.get("E2E_BASE_URL")
    if external:
        yield external.rstrip("/")
        return

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
