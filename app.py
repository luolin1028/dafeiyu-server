# AstrBot entrypoint v5 for the Pterodactyl / Nodaroo Python egg.
# Installs AstrBot into a local venv (never touches the read-only system pip).
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ.setdefault("TZ", "Asia/Shanghai")
if hasattr(time, "tzset"):
    time.tzset()

VENV = ROOT / ".venv"
VENV_PY = VENV / "bin" / "python"
LOCAL = ROOT / ".local"


def tmp_env():
    tmp = ROOT / ".tmp"
    tmp.mkdir(exist_ok=True)
    return dict(os.environ, TMPDIR=str(tmp), PIP_NO_CACHE_DIR="1"), tmp


def add_local_paths():
    p = LOCAL / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    for path in (p, LOCAL):
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def in_venv():
    try:
        return Path(sys.prefix).resolve() == VENV.resolve()
    except OSError:
        return False


def ensure_venv():
    if not VENV_PY.exists():
        print("[dafeiyu] creating venv", flush=True)
        if subprocess.call([sys.executable, "-m", "venv", str(VENV)]) != 0:
            return False
    env, tmp = tmp_env()
    if subprocess.call([str(VENV_PY), "-c", "import astrbot"], env=env) != 0:
        print("[dafeiyu] installing astrbot into venv", flush=True)
        rc = subprocess.call(
            [str(VENV_PY), "-m", "pip", "install", "--no-cache-dir", "astrbot==4.29.4"],
            env=env,
        )
        shutil.rmtree(tmp, ignore_errors=True)
        if rc != 0:
            return False
    return True


def ensure_local():
    print("[dafeiyu] installing astrbot into .local", flush=True)
    env, tmp = tmp_env()
    rc = subprocess.call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--ignore-installed",
            "--no-cache-dir",
            "--prefix",
            str(LOCAL),
            "astrbot==4.29.4",
        ],
        env=env,
    )
    shutil.rmtree(tmp, ignore_errors=True)
    if rc != 0:
        raise SystemExit("[dafeiyu] pip install failed, see the log above")
    add_local_paths()


print("[dafeiyu] app.py v5", flush=True)

if not in_venv():
    if ensure_venv():
        print("[dafeiyu] re-exec into venv", flush=True)
        os.execv(str(VENV_PY), [str(VENV_PY), str(ROOT / "app.py")])
    print("[dafeiyu] venv failed, falling back to .local", flush=True)
    add_local_paths()
    try:
        import astrbot  # noqa: F401
    except ModuleNotFoundError:
        ensure_local()

try:
    import astrbot  # noqa: F401
except ModuleNotFoundError as exc:
    raise SystemExit(f"[dafeiyu] astrbot still missing: {exc}")

for d in ("data", "data/config", "data/plugins", "data/temp"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
(ROOT / ".astrbot").touch(exist_ok=True)

for p in ("/tmp", str(ROOT)):
    try:
        total, used, free = shutil.disk_usage(p)
        print(f"[dafeiyu] {p}: total={total / 2**30:.2f}G free={free / 2**30:.2f}G", flush=True)
    except OSError as exc:
        print(f"[dafeiyu] {p}: {exc}", flush=True)

port = os.environ.get("SERVER_PORT") or os.environ.get("PORT") or "6185"
os.environ["DASHBOARD_PORT"] = port
print(f"[dafeiyu] starting AstrBot WebUI on 0.0.0.0:{port}", flush=True)

sys.argv = ["astrbot", "run", "--port", str(port)]

from astrbot.cli.__main__ import cli  # noqa: E402

cli()
