import os
from pathlib import Path

# Load variables from .env file if present in the project root
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    try:
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip().strip('"').strip("'"))
    except Exception:
        pass

# SMTP Server configuration (defaults to Gmail)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # 465 for SSL, 587 for TLS

# Sender credentials:
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "sindhuautomation12@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "ekdd pfme qnic ghld")

# Default recipient for revenue reports
DEFAULT_RECIPIENT = os.getenv("DEFAULT_RECIPIENT", "sindhu.bindhya@gmail.com")
