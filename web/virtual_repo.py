"""
web.virtual_repo
~~~~~~~~~~~~~~~~
Complex, multi-repository virtual sandbox for autonomous coding agents.
Simulates multiple authentic production codebases:
1. 'auth-service': FinTech Payment & JWT Authentication Service (HMAC vs RS256 algorithm bug)
2. 'order-engine': E-Commerce Order & Inventory State Machine (Uncommitted DB transaction race condition)
3. 'gateway-proxy': Distributed API Gateway & Token Bucket Rate Limiter (Cold-start burst packet drop)
"""

import re
from typing import Dict, Any, Tuple, Optional, List


# ============================================================================
# 1. REPOSITORY 1: FINTECH PAYMENT & AUTH SERVICE
# ============================================================================
AUTH_SERVICE_FILES: Dict[str, str] = {
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
from typing import Dict, Any

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


# ============================================================================
# 2. REPOSITORY 2: E-COMMERCE ORDER & INVENTORY ENGINE
# ============================================================================
ORDER_ENGINE_FILES: Dict[str, str] = {
    "orders/inventory.py": '''"""
orders.inventory
~~~~~~~~~~~~~~~~
High-throughput stock deduction and reservation handler.
"""
from typing import Dict, Any
from database.session import get_db_session

def deduct_inventory(product_id: str, quantity: int) -> Dict[str, Any]:
    """Deducts stock from database inside a transactional session."""
    db = get_db_session()
    item = db.find_item(product_id)
    if not item:
        raise ValueError(f"Product {product_id} not found in catalog")
    
    if item["stock"] < quantity:
        raise ValueError("Insufficient stock for reservation")

    # Deduct item stock
    item["stock"] -= quantity
    db.update_item(product_id, item)

    # BUG: Transaction is left uncommitted before returning response!
    # db.commit()  # <-- Missing commit creates dirty uncommitted session
    
    return {
        "product_id": product_id,
        "remaining_stock": item["stock"],
        "status": "reserved"
    }
''',

    "orders/state_machine.py": '''"""
orders.state_machine
~~~~~~~~~~~~~~~~~~~~
Order status transition state machine.
"""
from typing import Dict, Any

VALID_TRANSITIONS = {
    "PENDING": ["RESERVED", "CANCELLED"],
    "RESERVED": ["PAID", "CANCELLED"],
    "PAID": ["FULFILLED", "REFUNDED"],
    "CANCELLED": []
}

def transition_order_state(current_state: str, next_state: str) -> bool:
    allowed = VALID_TRANSITIONS.get(current_state, [])
    if next_state not in allowed:
        raise ValueError(f"Illegal transition from {current_state} to {next_state}")
    return True
''',

    "database/session.py": '''"""
database.session
~~~~~~~~~~~~~~~~
Thread-local mock database session manager.
"""
from typing import Dict, Any, Optional

_DATABASE_STORE: Dict[str, Dict[str, Any]] = {
    "prod_sku_99": {"id": "prod_sku_99", "name": "Mechanical Keyboard", "stock": 50, "price": 129.99}
}

class MockSession:
    def __init__(self):
        self.dirty: bool = False
        self.committed: bool = False

    def find_item(self, product_id: str) -> Optional[Dict[str, Any]]:
        return dict(_DATABASE_STORE.get(product_id, {}))

    def update_item(self, product_id: str, data: Dict[str, Any]):
        _DATABASE_STORE[product_id] = data
        self.dirty = True

    def commit(self):
        self.committed = True
        self.dirty = False

    def is_clean(self) -> bool:
        return not self.dirty

_CURRENT_SESSION = MockSession()

def get_db_session() -> MockSession:
    return _CURRENT_SESSION
''',

    "tests/test_orders.py": '''"""
tests.test_orders
~~~~~~~~~~~~~~~~~
Unit test suite for order inventory persistence and transactional integrity.
"""
import pytest
from orders.inventory import deduct_inventory
from database.session import get_db_session

def test_inventory_deduction_persists():
    db = get_db_session()
    res = deduct_inventory("prod_sku_99", 5)
    assert res["status"] == "reserved"
    assert db.is_clean(), "RollbackException: Database session was left uncommitted before returning response"

def test_inventory_stock_balance():
    db = get_db_session()
    item = db.find_item("prod_sku_99")
    assert item["stock"] <= 50
''',

    "config/database.py": '''"""
config.database
~~~~~~~~~~~~~~~
Connection pool and persistence settings.
"""
DB_HOST = "postgresql://cluster-prod.internal:5432/ecommerce"
POOL_SIZE = 25
ISOLATION_LEVEL = "REPEATABLE_READ"
''',

    "requirements.txt": '''SQLAlchemy>=2.0.0
pytest>=8.0.0
pydantic>=2.5.0
fastapi>=0.110.0
'''
}


# ============================================================================
# 3. REPOSITORY 3: DISTRIBUTED API GATEWAY & TOKEN BUCKET LIMITER
# ============================================================================
GATEWAY_PROXY_FILES: Dict[str, str] = {
    "gateway/rate_limiter.py": '''"""
gateway.rate_limiter
~~~~~~~~~~~~~~~~~~~~
Sliding-window token bucket algorithm for API burst throttling.
"""
import time
from typing import Tuple

class SlidingTokenBucket:
    def __init__(self, capacity: int = 100, refill_rate_per_sec: float = 10.0):
        self.capacity = capacity
        # BUG: Initialized with 0 tokens instead of capacity, causing immediate 429 on cold-start burst traffic
        self.tokens = 0
        self.last_update = time.time()
        self.refill_rate = refill_rate_per_sec

    def allow_request(self, tokens_needed: int = 1) -> Tuple[bool, int]:
        now = time.time()
        elapsed = max(0.0, now - self.last_update)
        self.tokens = min(float(self.capacity), self.tokens + (elapsed * self.refill_rate))
        self.last_update = now

        if self.tokens >= tokens_needed:
            self.tokens -= tokens_needed
            return True, int(self.tokens)
        return False, int(self.tokens)
''',

    "gateway/token_bucket.py": '''"""
gateway.token_bucket
~~~~~~~~~~~~~~~~~~~~
Token bucket metrics and sliding window state synchronization.
"""
from typing import Dict, Any

def get_bucket_metrics(bucket) -> Dict[str, Any]:
    return {
        "capacity": bucket.capacity,
        "current_tokens": int(bucket.tokens),
        "refill_rate": bucket.refill_rate
    }
''',

    "middleware/auth_proxy.py": '''"""
middleware.auth_proxy
~~~~~~~~~~~~~~~~~~~~~
Reverse proxy middleware applying rate limits before upstream dispatch.
"""
from gateway.rate_limiter import SlidingTokenBucket

_GLOBAL_BUCKET = SlidingTokenBucket(capacity=100)

def handle_incoming_request(client_ip: str) -> int:
    allowed, remaining = _GLOBAL_BUCKET.allow_request(1)
    if not allowed:
        return 429  # Too Many Requests
    return 200  # OK
''',

    "tests/test_gateway.py": '''"""
tests.test_gateway
~~~~~~~~~~~~~~~~~~
Unit test suite validating token bucket rate limiting on cold start burst packets.
"""
import pytest
from gateway.rate_limiter import SlidingTokenBucket

def test_burst_packet_allowed_on_start():
    bucket = SlidingTokenBucket(capacity=100)
    # On start with capacity=100, initial burst of 10 requests should succeed (HTTP 200)
    for _ in range(10):
        allowed, remaining = bucket.allow_request(1)
        assert allowed is True, "AssertionError: Expected HTTP 200 on initial burst packet, got 429 Too Many Requests"

def test_rate_limit_capacity_ceiling():
    bucket = SlidingTokenBucket(capacity=100)
    assert bucket.capacity == 100
''',

    "config/redis.py": '''"""
config.redis
~~~~~~~~~~~~
Distributed Redis synchronization cluster settings.
"""
REDIS_CLUSTER_URL = "redis://redis-cluster.internal:6379/0"
KEY_PREFIX = "rate_limit:v1:"
TTL_SECONDS = 3600
''',

    "requirements.txt": '''redis>=5.0.0
pytest>=8.0.0
httpx>=0.27.0
uvicorn>=0.28.0
'''
}


# ============================================================================
# MULTI-REPOSITORY REGISTRY
# ============================================================================
REPOSITORIES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "auth-service": {
        "id": "auth-service",
        "name": "FinTech Payment & Auth Service",
        "badge": "JWT Algorithm Mismatch",
        "description": "Production JWT Token handler configured with asymmetric RS256 instead of symmetric HS256 HMAC.",
        "default_issue": "tests/test_auth.py fails with InvalidKeyError: HMAC key requires HS256, but algorithm is RS256. Inspect files and fix the issue.",
        "bug_file": "auth/jwt_handler.py",
        "test_file": "tests/test_auth.py",
        "tags": ["FastAPI", "PyJWT", "Security", "SWE-bench"],
        "files": AUTH_SERVICE_FILES
    },
    "order-engine": {
        "id": "order-engine",
        "name": "E-Commerce Inventory & Order State Machine",
        "badge": "Uncommitted DB Transaction",
        "description": "High-throughput inventory checkout fails under concurrent requests due to missing session.commit() before response.",
        "default_issue": "tests/test_orders.py fails with RollbackException: Database session uncommitted before return. Inspect orders/inventory.py and fix.",
        "bug_file": "orders/inventory.py",
        "test_file": "tests/test_orders.py",
        "tags": ["SQLAlchemy", "PostgreSQL", "Concurrency", "Transactions"],
        "files": ORDER_ENGINE_FILES
    },
    "gateway-proxy": {
        "id": "gateway-proxy",
        "name": "Distributed API Gateway & Rate Limiter",
        "badge": "Token Bucket Cold-Start 429",
        "description": "Distributed rate limiter prematurely drops burst HTTP traffic with 429 due to token bucket initialized at 0.",
        "default_issue": "tests/test_gateway.py fails with AssertionError: 429 != 200 on cold start burst. Inspect gateway/rate_limiter.py and fix.",
        "bug_file": "gateway/rate_limiter.py",
        "test_file": "tests/test_gateway.py",
        "tags": ["Redis", "Rate Limiter", "Networking", "Microservices"],
        "files": GATEWAY_PROXY_FILES
    }
}


def get_available_repositories() -> List[Dict[str, Any]]:
    """Returns metadata for all available repositories for the frontend selector."""
    results = []
    for repo_id, data in REPOSITORIES_REGISTRY.items():
        results.append({
            "id": repo_id,
            "name": data["name"],
            "badge": data["badge"],
            "description": data["description"],
            "default_issue": data["default_issue"],
            "bug_file": data["bug_file"],
            "test_file": data["test_file"],
            "tags": data["tags"],
            "file_count": len(data["files"])
        })
    return results


class VirtualRepository:
    """
    In-memory virtual repository engine that executes bash commands (cat, grep, find, pytest, sed)
    against a realistic multi-file codebase. Supports multiple production scenarios.
    """

    def __init__(self, repo_id: str = "auth-service"):
        self.repo_id = repo_id if repo_id in REPOSITORIES_REGISTRY else "auth-service"
        self.meta = REPOSITORIES_REGISTRY[self.repo_id]
        self.files: Dict[str, str] = dict(self.meta["files"])
        self.history: List[str] = []

    def get_file(self, path: str) -> Optional[str]:
        clean_path = path.strip().lstrip("./")
        return self.files.get(clean_path)

    def write_file(self, path: str, content: str):
        clean_path = path.strip().lstrip("./")
        self.files[clean_path] = content

    def execute_command(self, cmd: str) -> Tuple[int, str]:
        """
        Executes a shell command (or chained commands with && or ;) against the virtual repository.
        """
        cmd_clean = cmd.strip()
        self.history.append(cmd_clean)

        # Handle chained commands (e.g. sed ... && pytest ...)
        if "&&" in cmd_clean:
            parts = [p.strip() for p in cmd_clean.split("&&") if p.strip()]
            logs = []
            for p in parts:
                code, out = self._execute_single(p)
                logs.append(out)
                if code != 0:
                    return code, "\n".join(logs)
            return 0, "\n".join(logs)

        return self._execute_single(cmd_clean)

    def _execute_single(self, cmd_clean: str) -> Tuple[int, str]:
        # -------------------------------------------------------------
        # 1. SED / MUTATION / PATCH COMMAND
        # -------------------------------------------------------------
        # Repo 1: Auth Service (RS256 -> HS256)
        if self.repo_id == "auth-service":
            if ("sed -i" in cmd_clean or "s/RS256/HS256" in cmd_clean) and ("auth/jwt_handler.py" in cmd_clean or "jwt_handler" in cmd_clean):
                jwt_code = self.files.get("auth/jwt_handler.py", "")
                if "RS256" in jwt_code:
                    self.files["auth/jwt_handler.py"] = jwt_code.replace("RS256", "HS256")
                    return (0, "File patched: Replaced 'RS256' with 'HS256' in auth/jwt_handler.py.")
                return (0, "File already up to date: 'HS256' active.")

        # Repo 2: Order Engine (Uncomment db.commit())
        elif self.repo_id == "order-engine":
            if ("sed -i" in cmd_clean or "commit" in cmd_clean) and ("orders/inventory.py" in cmd_clean or "inventory" in cmd_clean):
                inv_code = self.files.get("orders/inventory.py", "")
                if "# db.commit()" in inv_code:
                    self.files["orders/inventory.py"] = inv_code.replace("# db.commit()", "db.commit()")
                    return (0, "File patched: Enabled 'db.commit()' in orders/inventory.py.")
                return (0, "File already up to date: transaction commit enabled.")

        # Repo 3: Gateway Proxy (tokens = capacity)
        elif self.repo_id == "gateway-proxy":
            if ("sed -i" in cmd_clean or "capacity" in cmd_clean or "tokens" in cmd_clean) and ("gateway/rate_limiter.py" in cmd_clean or "rate_limiter" in cmd_clean):
                gw_code = self.files.get("gateway/rate_limiter.py", "")
                if "self.tokens = 0" in gw_code:
                    self.files["gateway/rate_limiter.py"] = gw_code.replace("self.tokens = 0", "self.tokens = float(capacity)")
                    return (0, "File patched: Initialized token bucket with full capacity in gateway/rate_limiter.py.")
                return (0, "File already up to date: token bucket initialized with full capacity.")

        # -------------------------------------------------------------
        # 2. PYTEST EXECUTION
        # -------------------------------------------------------------
        if "pytest" in cmd_clean:
            return self._run_pytest()

        # -------------------------------------------------------------
        # 3. CAT / VIEW COMMAND
        # -------------------------------------------------------------
        m_cat = re.search(r"cat\s+([^\s\|;]+)", cmd_clean)
        if m_cat:
            target = m_cat.group(1).strip().rstrip(";")
            content = self.get_file(target)
            if content:
                return (0, content)
            return (1, f"cat: {target}: No such file or directory")

        # -------------------------------------------------------------
        # 4. SED -N (READ/PRINT SPECIFIC LINES, NOT MODIFY)
        # -------------------------------------------------------------
        if "sed -n" in cmd_clean or "sed '" in cmd_clean and "p'" in cmd_clean:
            m_target = re.search(r"([a-zA-Z0-9_\-\./]+\.py)", cmd_clean)
            if m_target:
                content = self.get_file(m_target.group(1))
                if content:
                    lines = content.splitlines()
                    m_range = re.search(r"(\d+),(\d+)p", cmd_clean)
                    if m_range:
                        start_l = max(0, int(m_range.group(1)) - 1)
                        end_l = min(len(lines), int(m_range.group(2)))
                        return (0, "\n".join(lines[start_l:end_l]))
                    return (0, "\n".join(lines[:20]))
            return (0, "sed: printed slice")

        # -------------------------------------------------------------
        # 5. GREP COMMAND
        # -------------------------------------------------------------
        if "grep" in cmd_clean:
            clean_grep = re.sub(r"grep\s+(?:-[a-zA-Z]+\s+)*", "", cmd_clean)
            m_pattern = re.search(r"['\"]?([^'\"\|\s]+)['\"]?", clean_grep)
            query = m_pattern.group(1).strip() if m_pattern else ""
            query_clean = query.replace("\\|", "|").split("|")[0].lower()
            
            matches = []
            for path, code in self.files.items():
                for idx, line in enumerate(code.splitlines(), start=1):
                    if query_clean and query_clean in line.lower():
                        matches.append(f"{path}:{idx}:{line.strip()}")
            if matches:
                return (0, "\n".join(matches[:15]))
            return (1, f"grep: 0 matching symbols found across repository for '{query}'")

        # -------------------------------------------------------------
        # 6. FIND COMMAND
        # -------------------------------------------------------------
        if "find " in cmd_clean:
            m_find = re.search(r"-name\s+['\"]?([^'\"\|\s]+)['\"]?", cmd_clean)
            if m_find:
                pattern = m_find.group(1).replace("*", "")
                results = [p for p in self.files.keys() if pattern in p]
                return (0, "\n".join(results) if results else "find: 0 matching files found")
            return (0, "\n".join(self.files.keys()))

        # -------------------------------------------------------------
        # 7. GIT STATUS / GIT DIFF
        # -------------------------------------------------------------
        if "git status" in cmd_clean:
            is_fixed, _ = self.is_issue_resolved()
            if is_fixed:
                return (0, f"On branch main\nChanges to be committed:\n\tmodified:   {self.meta['bug_file']}\n")
            return (0, "On branch main\nnothing to commit, working tree clean")

        # Fallback
        return (0, f"Command executed cleanly: {cmd_clean} (exit code 0)")

    def is_issue_resolved(self) -> Tuple[bool, str]:
        """Checks whether the bug in the active repository is resolved."""
        if self.repo_id == "auth-service":
            jwt_content = self.files.get("auth/jwt_handler.py", "")
            is_fixed = 'DEFAULT_ALGORITHM = "HS256"' in jwt_content or "DEFAULT_ALGORITHM = 'HS256'" in jwt_content or ("HS256" in jwt_content and "RS256" not in jwt_content)
            return is_fixed, "auth/jwt_handler.py"

        elif self.repo_id == "order-engine":
            inv_content = self.files.get("orders/inventory.py", "")
            is_fixed = "db.commit()" in inv_content and "# db.commit()" not in inv_content
            return is_fixed, "orders/inventory.py"

        elif self.repo_id == "gateway-proxy":
            gw_content = self.files.get("gateway/rate_limiter.py", "")
            is_fixed = "self.tokens = 0" not in gw_content and ("capacity" in gw_content or "100" in gw_content)
            return is_fixed, "gateway/rate_limiter.py"

        return False, ""

    def _run_pytest(self) -> Tuple[int, str]:
        is_fixed, _ = self.is_issue_resolved()

        if is_fixed:
            return (
                0,
                f"============================= test session starts ==============================\n"
                f"platform linux -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0\n"
                f"rootdir: /workspace/{self.repo_id}\n"
                f"collected 2 items\n\n"
                f"{self.meta['test_file']} ..                                                    [100%]\n\n"
                f"============================== 2 passed in 0.08s ==============================="
            )

        # Failure outputs tailored per repository
        if self.repo_id == "auth-service":
            return (
                1,
                "============================= test session starts ==============================\n"
                "platform linux -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0\n"
                "rootdir: /workspace/auth-service\n"
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

        elif self.repo_id == "order-engine":
            return (
                1,
                "============================= test session starts ==============================\n"
                "platform linux -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0\n"
                "rootdir: /workspace/order-engine\n"
                "collected 2 items\n\n"
                "tests/test_orders.py F.                                                   [100%]\n\n"
                "=================================== FAILURES ===================================\n"
                "______________________ test_inventory_deduction_persists ______________________\n"
                "tests/test_orders.py:12: in test_inventory_deduction_persists\n"
                "    assert db.is_clean(), 'RollbackException: Database session was left uncommitted before returning response'\n"
                "E   AssertionError: RollbackException: Database session was left uncommitted before returning response. Active dirty transaction detected.\n"
                "=========================== 1 failed, 1 passed in 0.14s ==========================="
            )

        elif self.repo_id == "gateway-proxy":
            return (
                1,
                "============================= test session starts ==============================\n"
                "platform linux -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0\n"
                "rootdir: /workspace/gateway-proxy\n"
                "collected 2 items\n\n"
                "tests/test_gateway.py F.                                                  [100%]\n\n"
                "=================================== FAILURES ===================================\n"
                "______________________ test_burst_packet_allowed_on_start ______________________\n"
                "tests/test_gateway.py:11: in test_burst_packet_allowed_on_start\n"
                "    assert allowed is True, 'AssertionError: Expected HTTP 200 on initial burst packet, got 429 Too Many Requests'\n"
                "E   AssertionError: AssertionError: Expected HTTP 200 on initial burst packet, got 429 Too Many Requests (Rate limit exceeded on cold start)\n"
                "=========================== 1 failed, 1 passed in 0.09s ==========================="
            )

        return (1, "Pytest execution failed.")

    def get_tree(self) -> Dict[str, Any]:
        """Returns file structure metadata and contents for frontend interactive explorer."""
        return {
            path: {
                "path": path,
                "size": len(content),
                "lines": len(content.splitlines()),
                "content": content
            }
            for path, content in self.files.items()
        }
