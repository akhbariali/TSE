"""Create/replace one login account; restart the app to apply the change."""
import argparse
import getpass
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app_auth import password_record

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='admin')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'data/auth.json')
    args = parser.parse_args()
    password = getpass.getpass('Password (at least 12 characters): ')
    if password != getpass.getpass('Confirm password: '):
        raise SystemExit('Passwords do not match.')
    record = password_record(args.username, password)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Restrictive permissions apply before credentials are written.
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as target:
        json.dump(record, target)
    print(f'Login saved to {args.output}. Restart the application to apply it.')
