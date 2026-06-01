import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
TEMPLATES_DIR = ROOT_DIR / "templates"
DIST_DIR = ROOT_DIR / "dist"


def load_env() -> None:
    env_path = ROOT_DIR / ".env"
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
        return
    except ImportError:
        pass

    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_setting(name: str, default: str = "") -> str:
    return os.getenv(name, default)
