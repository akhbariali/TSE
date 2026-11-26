"""Refresh the CSV and optional model after collection, retaining old scores on failure."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def refresh(collect=False):
    folder=ROOT/'data/recommendations';folder.mkdir(parents=True,exist_ok=True)
    with (folder/'refresh.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('A recommendation refresh is already running')
        if collect:subprocess.run([sys.executable,str(ROOT/'scripts/tsetmc_daily.py')],check=True,cwd=ROOT)
        subprocess.run([sys.executable,str(ROOT/'scripts/export_market_csv.py')],check=True,cwd=ROOT)
        python=Path(os.environ.get('TSE_MODEL_PYTHON',str(ROOT/'.venv/bin/python')))
        if not python.is_file():
            print('Model refresh skipped: install requirements-model.txt in .venv to enable it.',flush=True)
            return
        env=os.environ.copy()
        # Support a local macOS OpenMP runtime without changing system libraries.
        if sys.platform=='darwin' and (ROOT/'.venv/lib/libomp.dylib').exists():
            env['DYLD_LIBRARY_PATH']=str(ROOT/'.venv/lib')
        subprocess.run([str(python),str(ROOT/'scripts/model_recommendations.py')],check=True,cwd=ROOT,env=env)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--collect',action='store_true')
    refresh(parser.parse_args().collect)
