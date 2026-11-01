"""
web.virtual_repo
~~~~~~~~~~~~~~~~
Complex, multi-file virtual repository sandbox for autonomous coding agents.
Simulates a production Payment & Authentication Service with realistic files,
failing unit tests, and terminal command execution (cat, grep, find, pytest, git).
"""

import re
from typing import Dict, Any, Tuple, Optional

REPO_FILES: Dict[str, str] = {
    "auth/jwt_handler.py": '''"""
auth.jwt_handler
~~~~~~~~~~~~~~~~
Production JWT Token verification & decoding handler.
"""
import jwt
from typing import Dict, Any

# Secret key configured for HMAC signing
SECRET_KEY = "prod-super-secret-hmac-key-2026"
DEFAULT_ALGORITHM = "RS256"  # BUG: Configured as RS256 (asymmetric) instead of HS256 (symmetric HMAC)

def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and verifies a JWT token payload."""
    try:
        # Fails with InvalidKeyError when algorithm='RS256' is passed with HMAC key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[DEFAULT_ALGORITHM])
        return payload
    except Exception as e:
        raise e

def encode_token(payload: Dict[str, Any]) -> str:
    """Signs a new JWT token payload."""
    return jwt.encode(payload, SECRET_KEY, algorithm=DEFAULT_ALGORITHM)
''',

    "auth/tokens.py": '''"""
auth.tokens
~~~~~~~~~~~
Token refresh and payload claims validation.
"""
import time
from typing import Dict, Any
from .jwt_handler import encode_token, decode_token

def create_access_token(user_id: str, role: str = "engineer") -> str:
    claims = {
        "sub": user_id,
        "role": role,
        "exp": int(time.time()) + 3600,
        "iss": "capybala-auth-service"
    }
    return encode_token(claims)

def verify_access_token(token: str) -> Dict[str, Any]:
    return decode_token(token)
''',

    "api/routes.py": '''"""
api.routes
~~~~~~~~~~
Authentication and user profile endpoints.
"""
from auth.tokens import verify_access_token

def profile_endpoint(auth_header: str) -> Dict[str, Any]:
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"error": "Missing or malformed Authorization header", "status": 401}
    token = auth_header.split(" ", 1)[1]
    claims = verify_access_token(token)
    return {"user_id": claims["sub"], "role": claims["role"], "status": 200}
''',

    "tests/test_auth.py": '''"""
tests.test_auth
~~~~~~~~~~~~~~~
Unit test suite verifying token signing, algorithm consistency, and decoding.
"""
import pytest
from auth.jwt_handler import encode_token, decode_token

def test_token_encode_and_decode():
    payload = {"sub": "user_42", "role": "admin"}
    token = encode_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user_42"
    assert decoded["role"] == "admin"

def test_valid_signature_verification():
    payload = {"sub": "system_bot", "role": "service"}
    token = encode_token(payload)
    decoded = decode_token(token)
    assert "sub" in decoded
''',

    "config/settings.py": '''"""
config.settings
~~~~~~~~~~~~~~~
Global application settings & environment variables.
"""
SERVICE_NAME = "Capybala Auth Service"
VERSION = "2.4.0"
DEBUG = False
SECRET_KEY = "prod-super-secret-hmac-key-2026"
''',

    "requirements.txt": '''PyJWT==2.8.0
cryptography>=41.0.0
pytest>=8.0.0
fastapi>=0.110.0
uvicorn>=0.28.0
'''
}


class VirtualRepository:
    """
    In-memory virtual repository engine that executes bash commands (cat, grep, find, pytest, sed)
    against a realistic multi-file codebase.
    """

    def __init__(self):
        self.files: Dict[str, str] = dict(REPO_FILES)
        self.history: list = []

    def get_file(self, path: str) -> Optional[str]:
        clean_path = path.strip().lstrip("./")
        return self.files.get(clean_path)

    def write_file(self, path: str, content: str):
        clean_path = path.strip().lstrip("./")
        self.files[clean_path] = content

    def execute_command(self, cmd: str) -> Tuple[int, str]:
        """
        Executes a shell command against the virtual repository and returns (exit_code, stdout).
        """
        cmd_clean = cmd.strip()
        self.history.append(cmd_clean)

        # 1. pytest execution
        if "pytest" in cmd_clean:
            jwt_content = self.files.get("auth/jwt_handler.py", "")
            is_fixed = 'DEFAULT_ALGORITHM = "HS256"' in jwt_content or "DEFAULT_ALGORITHM = 'HS256'" in jwt_content or ("HS256" in jwt_content and "RS256" not in jwt_content)
            if is_fixed:
                return (
                    0,
                    "============================= test session starts ==============================\n"
                    "platform linux -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0\n"
                    "rootdir: /workspace/repo\n"
                    "collected 2 items\n\n"
                    "tests/test_auth.py ..                                                    [100%]\n\n"
                    "============================== 2 passed in 0.08s ==============================="
                )
            else:
                return (
                    1,
                    "============================= test session starts ==============================\n"
                    "platform linux -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0\n"
                    "rootdir: /workspace/repo\n"
                    "collected 2 items\n\n"
                    "tests/test_auth.py FF                                                    [100%]\n\n"
                    "=================================== FAILURES ===================================\n"
                    "_________________________ test_token_encode_and_decode _________________________\n"
                    "tests/test_auth.py:11: in test_token_encode_and_decode\n"
                    "    decoded = decode_token(token)\n"
                    "auth/jwt_handler.py:18: in decode_token\n"
                    "    payload = jwt.decode(token, SECRET_KEY, algorithms=[DEFAULT_ALGORITHM])\n"
                    "jwt/api_jwt.py:195: in decode\n"
                    "    raise InvalidKeyError('The specified key is an HMAC key but algorithm is RS256')\n"
                    "E   jwt.exceptions.InvalidKeyError: The specified key is an HMAC key (symmetric), but algorithm 'RS256' requires an RSA key (asymmetric). Did you mean 'HS256'?\n"
                    "=========================== 2 failed in 0.12s ==========================="
                )

        # 2. cat / view command
        m_cat = re.search(r"cat\s+([^\s\|]+)", cmd_clean)
        if m_cat:
            target = m_cat.group(1).strip()
            content = self.get_file(target)
            if content:
                return (0, content)
            return (1, f"cat: {target}: No such file or directory")

        # 3. grep command
        m_grep = re.search(r"grep\s+(?:-[a-zA-Z]+\s+)?['\"]?([^'\"\|]+)['\"]?\s+([^\s\|]+)?", cmd_clean)
        if m_grep:
            query = m_grep.group(1).strip()
            matches = []
            for path, code in self.files.items():
                for idx, line in enumerate(code.splitlines(), start=1):
                    if query.lower() in line.lower():
                        matches.append(f"{path}:{idx}:{line}")
            if matches:
                return (0, "\n".join(matches[:15]))
            return (1, f"grep: 0 matching symbols found across repository for '{query}'")

        # 4. find command
        if "find " in cmd_clean:
            m_find = re.search(r"-name\s+['\"]?([^'\"\|\s]+)['\"]?", cmd_clean)
            if m_find:
                pattern = m_find.group(1).replace("*", "")
                results = [p for p in self.files.keys() if pattern in p]
                return (0, "\n".join(results) if results else "find: 0 matching files found")
            return (0, "\n".join(self.files.keys()))

        # 5. sed / patch file replacement
        if "sed " in cmd_clean or "replace" in cmd_clean or "HS256" in cmd_clean:
            jwt_code = self.files.get("auth/jwt_handler.py", "")
            if "RS256" in jwt_code:
                self.files["auth/jwt_handler.py"] = jwt_code.replace("RS256", "HS256")
                return (0, "File patched: Replaced 'RS256' with 'HS256' in auth/jwt_handler.py.")
            return (0, "File already up to date: 'HS256' active.")

        # 6. git status / git diff
        if "git status" in cmd_clean:
            is_fixed = "HS256" in self.files.get("auth/jwt_handler.py", "")
            if is_fixed:
                return (0, "On branch main\nChanges to be committed:\n\tmodified:   auth/jwt_handler.py\n")
            return (0, "On branch main\nnothing to commit, working tree clean")

        # Fallback
        return (0, f"Command executed cleanly: {cmd_clean} (exit code 0)")

    def get_tree(self) -> Dict[str, Any]:
        """Returns file structure metadata and contents for the frontend interactive explorer."""
        return {
            path: {
                "path": path,
                "size": len(content),
                "lines": len(content.splitlines()),
                "content": content
            }
            for path, content in self.files.items()
        }
