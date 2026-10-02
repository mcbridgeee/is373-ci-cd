"""Production lifecycle on the host: deploy, verify, roll back, resume, and update checks.

Called by the Makefile. Every docker compose call goes through compose(), so a
persisted rollback selection in .state/release.env always wins over an exported
PROD_IMAGE, and Compose still loads .env and compose.override.yaml on its own.
"""

import base64
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".state"
REPOSITORY = "mcbridgeee/is373-ci-cd"
PROD_HEALTH = "http://127.0.0.1:8090/health"


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, text=True, **kwargs)


def output(args):
    return run(args, capture_output=True).stdout.strip()


def release_reference(value):
    """Turn RELEASE=sha-<40 hex> or sha256:<64 hex> into a pullable reference."""
    if re.fullmatch(r"sha-[0-9a-f]{40}", value):
        return f"{REPOSITORY}:{value}"
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        return f"{REPOSITORY}@{value}"
    raise ValueError("Use RELEASE=sha-<full 40-character commit> or RELEASE=sha256:<digest>")


def compose_environment(environ, state=STATE):
    """The environment for docker compose: a persisted selection beats the shell."""
    environment = dict(environ)
    selected = state / "release.env"
    if selected.exists():
        values = dict(line.split("=", 1) for line in selected.read_text().splitlines()
                      if line and not line.startswith("#"))
        environment["PROD_IMAGE"] = values["PROD_IMAGE"]
    return environment


def compose(*args, capture_output=False):
    return run(["docker", "compose", *args], env=compose_environment(os.environ), capture_output=capture_output)


def wait_for_health(url=PROD_HEALTH, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.load(response)
            if data.get("status") == "ok":
                return data
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Not healthy after {timeout}s: {url}")


def updates_paused():
    return (STATE / "updates-paused").exists()


def initialize_updater():
    """Generate WUD admin credentials once, readable only by their owner."""
    STATE.mkdir(exist_ok=True)
    credentials = STATE / "wud.env"
    if not credentials.exists():
        with os.fdopen(os.open(credentials, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as handle:
            handle.write("WUD_AUTH_ADMIN_USER=admin\nWUD_AUTH_ADMIN_PASSWORD=" + secrets.token_urlsafe(24) + "\n")
        print("Created WUD credentials in .state/wud.env (mode 600).")


def select_release(reference):
    STATE.mkdir(exist_ok=True)
    temporary = STATE / "release.env.tmp"
    temporary.write_text(f"PROD_IMAGE={reference}\n")
    temporary.replace(STATE / "release.env")


def selected_reference():
    # Rendered privately: the full model includes WUD's credentials.
    model = json.loads(compose("config", "--format", "json", capture_output=True).stdout)
    return model["services"]["prod"]["image"]


def verify_production(reference=None):
    """The running prod container must be the selected image, reporting its commit."""
    reference = reference or selected_reference()
    image = json.loads(output(["docker", "image", "inspect", reference]))[0]
    container = compose("ps", "-q", "prod", capture_output=True).stdout.strip()
    if not container:
        raise SystemExit("Production container is not running")
    if output(["docker", "inspect", container, "--format", "{{.Image}}"]) != image["Id"]:
        raise SystemExit(f"Production is not running the selected image {reference}")
    expected = image["Config"]["Labels"]["org.opencontainers.image.revision"]
    health = wait_for_health()
    if health.get("commit") != expected or health.get("environment") != "production":
        raise SystemExit(f"Production health {health} does not identify release {expected}")
    print(f"Verified production: {reference}")
    print(json.dumps(health, indent=2))


def deploy(include_dev=False):
    initialize_updater()
    compose("pull", "prod")
    if include_dev:
        compose("up", "-d", "--build", "dev", "prod")
    else:
        compose("up", "-d", "--no-deps", "prod")
    verify_production()
    if updates_paused():
        print("Updates are paused (rollback in effect). Use make resume-updates deliberately.")
    else:
        compose("up", "-d", "wud")


def pause_updates():
    STATE.mkdir(exist_ok=True)
    (STATE / "updates-paused").touch()
    compose("stop", "wud")
    print("Automatic updates paused.")


def rollback(release):
    reference = release_reference(release)
    pause_updates()
    run(["docker", "pull", reference])
    select_release(reference)
    compose("up", "-d", "--no-deps", "prod")
    verify_production(reference)
    print("Rolled back. WUD stays paused until make resume-updates.")


def resume_updates():
    initialize_updater()
    pause_updates()
    reference = f"{REPOSITORY}:prod"
    run(["docker", "pull", reference])
    select_release(reference)
    compose("up", "-d", "--no-deps", "prod")
    verify_production(reference)
    compose("up", "-d", "wud")
    (STATE / "updates-paused").unlink(missing_ok=True)
    print("Back on the prod channel; automatic updates resumed.")


def check_updates():
    if updates_paused():
        raise SystemExit("Updates are paused. Use make resume-updates only when the prod channel is safe.")
    credentials = dict(line.split("=", 1) for line in (STATE / "wud.env").read_text().splitlines() if line)
    token = base64.b64encode(
        f"{credentials['WUD_AUTH_ADMIN_USER']}:{credentials['WUD_AUTH_ADMIN_PASSWORD']}".encode()
    ).decode()
    request = urllib.request.Request(
        "http://127.0.0.1:8091/api/containers/watch", data=b"", method="POST",
        headers={"Authorization": "Basic " + token},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        response.read()
    print("Registry check requested. Watch make status or WUD's logs for the update.")


def status():
    compose("ps")
    print("Updates:", "paused" if updates_paused() else "enabled")
    print("Selected prod image:", selected_reference())
    try:
        print(json.dumps(wait_for_health(timeout=3), indent=2))
    except RuntimeError:
        print("Production /health: not responding")


def main():
    command = sys.argv[1]
    actions = {
        "deploy": deploy,
        "up": lambda: deploy(include_dev=True),
        "verify-production": verify_production,
        "pause-updates": pause_updates,
        "rollback": lambda: rollback(os.environ.get("RELEASE", "")),
        "resume-updates": resume_updates,
        "check-updates": check_updates,
        "status": status,
    }
    if command not in actions:
        raise SystemExit(f"Unknown command: {command}")
    try:
        actions[command]()
    except ValueError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
