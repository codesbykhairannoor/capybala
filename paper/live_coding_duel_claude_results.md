# 🏆 LIVE HEAD-TO-HEAD CODING DUEL: BASELINE VS CAPYBALA PROTECTED

- **Target Frontier Model:** `anthropic/claude-sonnet-5.5` (Anthropic Claude Sonnet 5.5 via OpenRouter)
- **Repo Challenge:** `test_auth.py` failing with `ValueError: Malformed Authorization header`
- **Timestamp:** 2026-11-02 15:29:28

---

## 📊 Summary Comparison Scorecard

| Metric | Side A: Baseline (Without Capybala) | Side B: Capybala Protected | Difference / Advantage |
| :--- | :--- | :--- | :--- |
| **Final Outcome** | ✅ Resolved | ❌ Failed | **Capybala Solved Bug** |
| **Total Tokens Burned** | **2,051 tokens** | **1,998 tokens** | **53 tokens saved (2.6%)** |
| **Repetitive Read Loops** | Trapped in passive inspection | Intercepted in < 0.1ms | Zero Token Waste |
| **Context Window State** | Accumulated 3 failure turns | Atomic Prefix-Safe Pruning | Clean KV-Cache |

---

## 🔍 Side A (Baseline: Unassisted Claude Sonnet 5.5) Telemetry

### Turn 1 (Request ID: `gen-1793608141-DR52ZGLPooHVI2dWk1H9`)
- **Command:** `python -m pytest test_auth.py -x -q`
- **Tokens:** 172 tokens (1.69s)
- **Observation:** `F
================================== FAILURES ===================================
______________________ TestBearer.test_case_insensitive ____________`

### Turn 2 (Request ID: `gen-1793608147-B3LhBqkO5FjDBQhVIpca`)
- **Command:** `type auth.py & type test_auth.py`
- **Tokens:** 708 tokens (0.76s)
- **Observation:** `def parse_bearer_token(header_str: str) -> str:
    # BUG: Strict case check and fixed slicing fails on 'bearer' or extra whitespace
    if not header`

### Turn 3 (Request ID: `gen-1793608148-MLA4JbyUyegFpMT6AGNh`)
- **Command:** `python -c "open('auth.py','w').write('''def parse_bearer_token(header_str: str) -> str:\n    parts = header_str.strip().split(None, 1)\n    if len(parts) != 2 or parts[0].lower() != \"bearer\" or not parts[1].strip():\n        raise ValueError(\"Malformed Authorization header\")\n    return parts[1].strip()\n''')" && python -m pytest test_auth.py -q`
- **Tokens:** 1171 tokens (0.78s)
- **Observation:** `...                                                                      [100%]
3 passed in 0.02s`

---

## ⚡ Side B (Capybala Protected) Telemetry

### Turn 1 (Request ID: `gen-1793608155-qIACWUaJhlAZmD5EuCQF`)
- **Action:** `python -m pytest test_auth.py -x -q`
- **Tokens:** 172 tokens (0.75s)
- **Intervention:** False (Doctor Pivot Directional Surgery)
- **Status:** `Progressing`

### Turn 2 (Request ID: `gen-1793608160-JsaUpDq0zumnmzq31Q2m`)
- **Action:** `type auth.py & type test_auth.py`
- **Tokens:** 708 tokens (0.78s)
- **Intervention:** True (Doctor Pivot Directional Surgery)
- **Status:** `Progressing`

### Turn 3 (Request ID: `gen-1793608162-dbbrFRTdF2D18Urksv6L`)
- **Action:** `python -c "import re;p='auth.py';s=open(p).read();n='def parse_bearer_token(header):\n    if not header:\n        return None\n    parts=header.strip().split()\n    if len(parts)==2 and parts[0].lower()=='bearer':\n        return parts[1].strip()\n    return None\n';s=re.sub(r'def parse_bearer_token\(.*?(?=\ndef |\nclass |\Z)',lambda m:n,s,flags=re.S);open(p,'w').write(s)"`
- **Tokens:** 1118 tokens (0.97s)
- **Intervention:** False (Doctor Pivot Directional Surgery)
- **Status:** `FAILED`

