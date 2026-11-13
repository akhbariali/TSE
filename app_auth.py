"""Single-account password verification and revocable, in-memory sessions."""
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import threading
import time

ITERATIONS = 600_000
SESSION_SECONDS = 12 * 60 * 60
COOKIE = 'tse_session'


def password_record(username, password):
    if not username.strip() or len(password) < 12:
        raise ValueError('Choose a username and a password of at least 12 characters.')
    salt = secrets.token_bytes(32)
    return {'username': username.strip(), 'salt': salt.hex(), 'iterations': ITERATIONS,
            'password_hash': hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS).hex()}


class SingleUserAuth:
    def __init__(self, record):
        self.username = record['username']
        self.salt = bytes.fromhex(record['salt'])
        self.iterations = int(record['iterations'])
        self.password_hash = bytes.fromhex(record['password_hash'])
        if not self.username or self.iterations < 100_000 or len(self.password_hash) != 32:
            raise ValueError('Invalid login configuration')
        self.sessions = {}
        self.attempts = {}
        self.lock = threading.Lock()

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text()))

    def login(self, username, password, address):
        now = time.time()
        with self.lock:
            self.attempts = {key: [t for t in times if t > now-900]
                             for key, times in self.attempts.items() if any(t > now-900 for t in times)}
            attempts = self.attempts.setdefault(address, [])
            if len(attempts) >= 10 or sum(len(v) for v in self.attempts.values()) >= 200:
                return None, True
            attempts.append(now)
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), self.salt, self.iterations)
        valid_password = hmac.compare_digest(candidate, self.password_hash)
        valid_username = hmac.compare_digest(username.encode(), self.username.encode())
        if not (valid_password and valid_username):
            return None, False
        token = secrets.token_urlsafe(48)
        with self.lock:
            self.attempts.pop(address, None)
            self.sessions = {key: expiry for key, expiry in self.sessions.items() if expiry > now}
            if len(self.sessions) >= 100:
                self.sessions.pop(next(iter(self.sessions)))
            self.sessions[hashlib.sha256(token.encode()).digest()] = now + SESSION_SECONDS
        return token, False

    def authenticated(self, token):
        if not token or len(token) > 200:
            return False
        key = hashlib.sha256(token.encode()).digest()
        with self.lock:
            expiry = self.sessions.get(key, 0)
            if expiry <= time.time():
                self.sessions.pop(key, None)
                return False
            return True

    def logout(self, token):
        with self.lock:
            self.sessions.pop(hashlib.sha256(token.encode()).digest(), None)
