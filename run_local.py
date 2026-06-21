import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNTIME_SITE = ROOT / ".runtime_site"

sys.path.insert(0, str(ROOT))

if RUNTIME_SITE.exists():
    sys.path.insert(0, str(RUNTIME_SITE))

from app import create_app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
