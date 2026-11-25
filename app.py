# AstrBot entrypoint v3 for the Pterodactyl / Nodaroo Python egg.
# One file, no requirements.txt, no docstring: safe to upload as-is.
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


def site_dir():
    return ROOT / ".local" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"


def add_paths():
    for p in (site_dir(), ROOT / ".local"):
        if p.is_dir() and str(p) not in sys.path:
            sys.path.insert(0, str(p))


print("[dafeiyu] app.py v3", flush=True)
add_paths()

try:
    import astrbot  # noqa: F401
except ModuleNotFoundError:
    tmp = ROOT / ".tmp"
    tmp.mkdir(exist_ok=True)
    env = dict(os.environ, TMPDIR=str(tmp), PIP_NO_CACHE_DIR="1")
    print(f"[dafeiyu] installing astrbot, TMPDIR={tmp}", flush=True)
    rc = subprocess.call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--prefix",
            str(ROOT / ".local"),
            "astrbot==4.29.4",
        ],
        env=env,
    )
    shutil.rmtree(tmp, ignore_errors=True)
    if rc != 0:
        raise SystemExit("[dafeiyu] pip install failed, see the log above")
    add_paths()

for d in ("data", "data/config", "data/plugins", "data/temp"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)

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
