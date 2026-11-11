"""Download every archive page, then index any new/revised workbooks."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
result = subprocess.run([sys.executable, str(root/'scripts/download_reports.py')], cwd=root)
# Always index the successful downloads, even after a partial network failure.
index = subprocess.run([sys.executable, str(root/'scripts/index_reports.py')], cwd=root)
# An existing watch indexer owns the indexing lock and will catch new files.
raise SystemExit(result.returncode or (index.returncode if index.returncode != 2 else 0))
