"""Start the Tag Network app from this App Bundle (standard library only; Python 3.12-3.14, not 3.14.1).

The first run installs the bundled wheels into a private environment inside this folder, with no package
index; later runs reuse it. It is rebuilt when the folder has moved, the Python changed or the bundle
changed. Then the app opens on the latest bundled Build (or `--build ID`) at http://127.0.0.1:<port>/, on
port 8050 or the next free one. Other arguments (`--no-browser`, `--clear-cache`) pass through to the app.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path

ENV_DIR = "environment"
MARKER = "bundle-environment.json"
FIRST_PORT = 8050


def target_name(system: str, machine: str) -> str | None:
    """The bundle target this computer is, if any."""
    machine = machine.lower()
    if system == "Windows" and machine in ("amd64", "x86_64"):
        return "windows"
    if system == "Darwin" and machine == "arm64":
        return "macos"
    if system == "Linux" and machine in ("x86_64", "amd64"):
        return "linux"
    return None


def supported_python(version: tuple[int, int, int]) -> bool:
    return (3, 12) <= version[:2] <= (3, 14) and tuple(version[:3]) != (3, 14, 1)


def inside_zip(folder: Path) -> bool:
    """Started from inside a zip (or from a single file Windows unpacked from one into a temp folder)."""
    return any(part.lower().endswith(".zip") for part in folder.parts) or not (folder / "wheels").is_dir()


def writable(folder: Path) -> bool:
    probe = folder / ".write-test"
    try:
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def can_make_environments() -> bool:
    return importlib.util.find_spec("venv") is not None and importlib.util.find_spec("ensurepip") is not None


def refusals(version: tuple[int, int, int], system: str, machine: str, folder: Path, targets: list[str],
             is_writable: bool, has_venv: bool) -> list[str]:
    """Why this bundle cannot start here, each with what to do (empty when it can start)."""
    if inside_zip(folder):
        return ["This App Bundle is still inside its zip. Extract the whole zip first (Windows: right-click it, "
                "Extract All; macOS: double-click it), then start it from the extracted folder."]
    out = []
    if not supported_python(version):
        shown = ".".join(str(v) for v in version[:3])
        out.append(f"This App Bundle needs Python 3.12, 3.13 or 3.14 (but not 3.14.1); this is Python {shown}. "
                   "Install a supported Python from python.org and start it again.")
    here = target_name(system, machine)
    if here not in targets:
        out.append(f"This App Bundle was made for {', '.join(targets)}; this computer is {system} {machine}. "
                   "Ask for a bundle made for this computer.")
    if not is_writable:
        out.append(f"This folder ({folder}) is read-only. Copy this folder to your own disk first, then start it "
                   "from there.")
    if not has_venv:
        out.append("This Python cannot create a private environment (its venv or ensurepip module is missing). "
                   "On Debian or Ubuntu, install the python3-venv package (sudo apt install python3-venv), "
                   "then start again.")
    return out


def environment_identity(folder: Path, manifest: bytes) -> dict[str, str]:
    """What the private environment was made for; any change means it is rebuilt."""
    return {"python": str(Path(sys.executable).resolve()), "version": platform.python_version(),
            "manifest": hashlib.sha256(manifest).hexdigest(), "folder": str(folder.resolve())}


def needs_rebuild(recorded: dict[str, str] | None, current: dict[str, str], env_python: Path) -> bool:
    return recorded != current or not env_python.is_file()


def env_python(env: Path) -> Path:
    return env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def build_environment(folder: Path, target: str, identity: dict[str, str]) -> Path:
    import shutil
    import venv

    env = folder / ENV_DIR
    print("Setting up the Tag Network app (first run, or the folder or Python changed). This takes a minute…",
          flush=True)
    if env.exists():
        shutil.rmtree(env)
    venv.EnvBuilder(with_pip=True, clear=True).create(env)
    python = env_python(env)
    requirements = folder / "requirements" / f"{target}-py{sys.version_info[0]}.{sys.version_info[1]}.txt"
    subprocess.run([str(python), "-m", "pip", "install", "--no-index", "--find-links", str(folder / "wheels"),
                    "--require-hashes", "--only-binary", ":all:", "--disable-pip-version-check", "--no-cache-dir",
                    "--quiet", "-r", str(requirements)], check=True)
    (env / MARKER).write_text(json.dumps(identity, indent=1), encoding="utf-8")
    return python


def free_port(first: int = FIRST_PORT, tries: int = 50) -> int:
    for port in range(first, first + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit(f"No free port between {first} and {first + tries - 1}.")


def prepare(folder: Path) -> tuple[Path, str] | list[str]:
    """The environment's Python and the target, or the reasons it cannot start."""
    manifest_path = folder / "bundle.json"
    targets = json.loads(manifest_path.read_text(encoding="utf-8"))["targets"] if manifest_path.is_file() else []
    v = sys.version_info
    problems = refusals((v[0], v[1], v[2]), platform.system(), platform.machine(), folder, targets,
                        writable(folder), can_make_environments())
    if problems:
        return problems
    target = target_name(platform.system(), platform.machine())
    assert target is not None
    identity = environment_identity(folder, manifest_path.read_bytes())
    env = folder / ENV_DIR
    marker = env / MARKER
    recorded = json.loads(marker.read_text(encoding="utf-8")) if marker.is_file() else None
    if needs_rebuild(recorded, identity, env_python(env)):
        return build_environment(folder, target, identity), target
    return env_python(env), target


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    folder = Path(__file__).resolve().parent
    prepared = prepare(folder)
    if isinstance(prepared, list):
        print("\nThe Tag Network app cannot start:\n", file=sys.stderr)
        for problem in prepared:
            print(f"- {problem}", file=sys.stderr)
        return 2
    python, _ = prepared
    if "--port" not in args:
        args += ["--port", str(free_port())]
    if "--clear-cache" not in args:
        port = args[args.index("--port") + 1]
        print(f"Opening the Tag Network app at http://127.0.0.1:{port}/ (close this window to stop it).", flush=True)
    return subprocess.call([str(python), "-m", "steamstudy.cli", "--root", str(folder), "app", *args])


if __name__ == "__main__":
    sys.exit(main())
