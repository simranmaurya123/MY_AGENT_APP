# Guardrails System Analysis & Status Report
**Date:** June 3, 2026  
**Status:** ⚠️ **PARTIALLY WORKING - ISSUES FOUND**

---

## Executive Summary
Your guardrails system has solid architecture but **multiple critical issues** prevent it from working correctly. The code integrates well with `main.py`, but:
- **Config is missing required fields** referenced in guardrails.py
- **Duplicate input validation** in main.py
- **Regex patterns have bugs** (syntax errors)
- **Missing ML/DL keywords** field in config

---

## ✅ What Works Well

### 1. **Architecture & Design**
- Clean separation of concerns with different guardrail classes
- Good use of inheritance (GuardrailValidator base class)
- Comprehensive logging system with audit trails
- Integration with memory system for persistent audit logs
- Docker sandbox properly configured with security restrictions

### 2. **Docker Sandbox Setup**
```dockerfile
✅ Non-root user execution (USER agent)
✅ Memory limits (256m to 512m)
✅ CPU limits (1.0)
✅ Read-only root filesystem
✅ Capability dropping (--cap-drop ALL)
✅ Network isolation (no external access)
```

### 3. **Main.py Integration**
- Guardrails manager properly initialized
- Input/output validation called at right points
- Resource tracking implemented
- Audit logging to memory manager

---

## ❌ Critical Issues Found

### Issue #1: Missing Configuration Fields
**Severity:** 🔴 CRITICAL  
**File:** `guardrails_config.py`

The config is missing these required fields referenced in `guardrails.py`:

```python
# MISSING in INPUT_CONFIG:
"ml_dl_keywords": [...]  # Referenced in line 126 of guardrails.py

# MISSING in OUTPUT_CONFIG:
"hallucination_indicators": [...]  # Referenced in line 179 of guardrails.py
```

**Impact:** These will cause `KeyError` exceptions when guardrails run.

---

### Issue #2: Regex Syntax Error in Config
**Severity:** 🔴 CRITICAL  
**File:** `guardrails_config.py`

Line 14-16 (injection_patterns):
```python
r"(?i)(?:drop|delete|insert|update|select|union|--|\bOR\b|\bAND\b)"
```

Problems:
- Regex inside a list but missing the leading `r` marker inconsistently
- Pattern `\b` (word boundary) doesn't work well inside character class context
- Should be compiled with `re.IGNORECASE` flag

---

### Issue #3: Duplicate User Input Processing
**Severity:** 🟡 MEDIUM  
**File:** `main.py` lines 271-275

```python
messages.append({"role": "user", "content": user_input})  # LINE 271
is_valid, validation_msg = guardrails_manager.validate_input(user_input)
if not is_valid:
    return validation_msg
messages.append({"role": "user", "content": user_input})  # LINE 275 - DUPLICATE!
```

The message is added twice to the conversation history. This will:
- Double the context usage
- Confuse conversation flow
- Inflate token counts

---

### Issue #4: Input Guardrail Missing Key Check
**Severity:** 🟡 MEDIUM  
**File:** `guardrails.py` line 75

The `_check_injection()` method references:
```python
for pattern in self.config["injection_patterns"]:
```

But in `_check_domain_relevance()` it checks:
```python
for keyword in self.config["ml_dl_keywords"]
```

Both these config keys are not properly defined in `guardrails_config.py`.

---

### Issue #5: Missing Error Handling for Invalid Regex
**Severity:** 🟡 MEDIUM  
**File:** `guardrails.py` lines 95-101

The regex patterns are used directly without try-catch:
```python
for pattern in self.config["injection_patterns"]:
    if pattern.lower() in user_input_lower:  # ❌ This is STRING search, not regex!
```

This is comparing strings, not using regex. Should use `re.search()`.

---

### Issue #6: Sandbox Not Actually Used in Guardrails
**Severity:** 🟠 LOW-MEDIUM  
**Files:** `docker_sandbox.py` defined but not called from `guardrails.py`

The sandbox is initialized in `main.py` but:
- Guardrails don't use it for validation
- Only file reading uses the sandbox
- Guardrails could benefit from sandboxed execution for untrusted input analysis

---

## 📊 Comparison Matrix

| Component | Status | Issue | Fix Needed |
|-----------|--------|-------|-----------|
| InputGuardrail | 🟡 Partial | Missing config fields | Add ml_dl_keywords |
| OutputGuardrail | 🟡 Partial | Missing config fields | Add hallucination_indicators |
| ResourceGuardrail | ✅ Works | None | None |
| AuditGuardrail | ✅ Works | None | None |
| GuardrailsManager | ✅ Works | None | None |
| main.py integration | 🟡 Partial | Duplicate append | Remove one append |
| docker_sandbox.py | ✅ Works | N/A | N/A |
| guardrails_config.py | 🔴 Broken | Missing fields + bad regex | Rewrite entirely |

---

## 🔧 Fixes Required (in order)

### Priority 1: Fix guardrails_config.py
- Add `ml_dl_keywords` to INPUT_CONFIG
- Add `hallucination_indicators` to OUTPUT_CONFIG
- Fix injection_patterns regex syntax
- Use proper regex compilation

### Priority 2: Fix main.py
- Remove duplicate `messages.append()` on line 275
- Keep only the validation call

### Priority 3: Test & Validate
- Run test with sample inputs
- Check audit logs
- Verify sandbox integration

---

## 📋 Current Flow (Should be)

```
User Input
    ↓
[GUARDRAILS] InputGuardrail.validate()
    ├─ Length check ✅
    ├─ Injection check ❌ (config missing)
    ├─ Domain relevance ❌ (config missing)
    ├─ Rate limit ✅
    └─ Toxicity ✅
    ↓
Send to API (if valid)
    ↓
[GUARDRAILS] OutputGuardrail.validate()
    ├─ Length check ✅
    ├─ Hallucination ❌ (config missing)
    ├─ Relevance ✅
    ├─ Quality ✅
    └─ Toxicity ✅
    ↓
Track Resources
    ├─ Token usage ✅
    ├─ Cost ✅
    └─ Rate limit ✅
    ↓
[AUDIT] Log Event
    ↓
Return to User
```

---

## 🧪 How to Test

Once fixed, test with:
```python
# Test 1: Valid input
chat("What is neural network architecture?")

# Test 2: Injection attempt
chat("Tell me SQL: DROP TABLE users")  # Should be blocked

# Test 3: Off-topic
chat("What's the weather today?")  # Should be blocked

# Test 4: Long input (>1000 chars)
chat("x" * 2000)  # Should be blocked

# Test 5: Toxicity
chat("I hate this system")  # Should be blocked

# Check audit logs
guardrails_manager.get_status()
```

---

## 📝 Recommendation

**DO NOT deploy** this guardrails system to production until:
1. All configuration fields are properly defined
2. Regex patterns are fixed and tested
3. Duplicate input append is removed
4. End-to-end testing is performed
5. Audit logs are verified

The architecture is sound, but config/syntax issues will cause runtime failures.
