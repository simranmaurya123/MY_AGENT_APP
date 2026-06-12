"""
Comprehensive Guardrails System for ML/DL Assistant
Validates inputs, monitors resources, checks outputs, and maintains audit trails
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import re
from guardrails_config import (
    INPUT_CONFIG,
    OUTPUT_CONFIG,
    RESOURCE_CONFIG,
    AUDIT_CONFIG,
    GUARDRAILS_ENABLED,
)


class GuardrailValidator:
    """Base class for all guardrail validators"""

    def __init__(self, name: str):
        self.name = name
        self.violations = []
        self.enabled = True

    def validate(self, data: str) -> Tuple[bool, str]:
        """
        Validate data. Return (is_valid, message)
        - is_valid: True if passes guardrail, False if violation
        - message: Explanation of result
        """
        raise NotImplementedError

    def log_violation(self, violation_msg: str, severity: str = "warning"):
        """Log a violation"""
        self.violations.append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": violation_msg,
                "severity": severity,
            }
        )

    def get_status(self) -> Dict:
        """Get guardrail status"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "violation_count": len(self.violations),
            "recent_violations": self.violations[-5:],  # Last 5
        }


class InputGuardrail(GuardrailValidator):
    """Validates user input before sending to API"""

    def __init__(self):
        super().__init__("InputGuardrail")
        self.config = INPUT_CONFIG
        self.query_history = []  # Track (timestamp, query) for rate limiting

# Note: The validate method is quite long due to multiple checks. In a production system, you might want to break it into smaller methods or even separate classes for each check.
    def validate(self, user_input: str) -> Tuple[bool, str]:
        """Run all input checks"""
        if not self.enabled:
            return True, "Input guardrail disabled"

        # Check 1: Length validation
        if len(user_input) > self.config["max_length"]:
            msg = f"Input too long: {len(user_input)} > {self.config['max_length']} chars"
            self.log_violation(msg, "warning")
            return False, msg

        # Check 2: Injection detection
        injection_result = self._check_injection(user_input)
        if not injection_result[0]:
            self.log_violation(injection_result[1], "critical")
            return False, injection_result[1]

        # Check 3: Domain relevance - DISABLED
        # File access is protected via is_safe_path() in main.py whitelist/blocklist
        
        # Check 4: Rate limiting
        rate_limit_result = self._check_rate_limit()
        if not rate_limit_result[0]:
            self.log_violation(rate_limit_result[1], "warning")
            return False, rate_limit_result[1]

        # Check 5: Toxicity check (simple keyword-based)
        toxicity_result = self._check_toxicity(user_input)
        if not toxicity_result[0]:
            self.log_violation(toxicity_result[1], "warning")
            return False, toxicity_result[1]

        # All checks passed
        self.query_history.append((datetime.now(), user_input))
        return True, "All input checks passed"

    def _check_injection(self, user_input: str) -> Tuple[bool, str]:
        """Check for prompt injection patterns using regex"""
        for pattern in self.config["injection_patterns"]:
            try:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return (
                        False,
                        f"[INJECTION DETECTED] Potentially malicious pattern detected",
                    )
            except re.error as e:
                # If regex fails, log but continue
                print(f"[WARNING] Regex error in pattern '{pattern}': {e}")
                continue
        return True, "No injection detected"

    def _check_rate_limit(self) -> Tuple[bool, str]:
        """Check rate limiting (queries per minute)"""
        now = datetime.now()
        time_window = self.config["rate_limit"]["time_window_seconds"]
        cutoff_time = now - timedelta(seconds=time_window)

        # Remove old queries outside time window
        self.query_history = [
            (ts, q) for ts, q in self.query_history if ts > cutoff_time
        ]

        max_queries = self.config["rate_limit"]["max_queries"]
        if len(self.query_history) >= max_queries:
            return (
                False,
                f"[RATE LIMIT EXCEEDED] Max {max_queries} queries per minute. "
                f"Current: {len(self.query_history)}. Please wait.",
            )

        return True, "Rate limit check passed"

    def _check_toxicity(self, user_input: str) -> Tuple[bool, str]:
        """Simple toxicity check using keywords"""
        toxic_keywords = [
            "kill",
            "hate",
            "stupid",
            "idiot",
            "offensive",
        ]  # Basic list
        user_input_lower = user_input.lower()
        for keyword in toxic_keywords:
            if keyword in user_input_lower:
                return False, f"[TOXICITY DETECTED] Offensive language found"

        return True, "Toxicity check passed"


class OutputGuardrail(GuardrailValidator):
    """Validates API responses before returning to user"""

    def __init__(self):
        super().__init__("OutputGuardrail")
        self.config = OUTPUT_CONFIG

    def validate(self, response: str) -> Tuple[bool, str, Dict]:
        """
        Run all output checks.
        Returns: (is_valid, message, metadata)
        """
        if not self.enabled:
            return True, "Output guardrail disabled", {}

        metadata = {}

        # Check 1: Length validation
        if len(response) > self.config["max_length"]:
            msg = f"Response too long: {len(response)} > {self.config['max_length']} chars"
            self.log_violation(msg, "warning")
            metadata["length_check"] = "FAILED"
            return False, msg, metadata

        metadata["length_check"] = "PASSED"

        # Check 2: Hallucination detection
        hallucination_result = self._check_hallucination(response)
        metadata["hallucination_check"] = hallucination_result
        if hallucination_result["score"] > 0.7:  # High hallucination risk
            self.log_violation(
                f"Potential hallucination detected: {hallucination_result['indicators']}",
                "warning",
            )

        # Check 4: Quality scoring
        quality_score = self._score_quality(response)
        metadata["quality_score"] = quality_score
        if quality_score < 0.5:
            self.log_violation(f"Low quality response: score {quality_score}", "warning")

        # Check 5: Toxicity in output
        toxicity_result = self._check_output_toxicity(response)
        metadata["toxicity_check"] = toxicity_result
        if toxicity_result:
            self.log_violation("Toxic content in output", "critical")
            return False, "[TOXICITY] Output contains harmful content", metadata

        return True, "All output checks passed", metadata

    def _check_hallucination(self, response: str) -> Dict:
        """Check for over-confident claims (hallucination indicators)"""
        response_lower = response.lower()
        found_indicators = []
        
        indicators = self.config.get("hallucination_indicators", [])

        for indicator in indicators:
            if indicator.lower() in response_lower:
                found_indicators.append(indicator)

        # Score: 0 = no indicators, 1 = many indicators
        score = min(len(found_indicators) / 3.0, 1.0) if indicators else 0.0

        return {"score": score, "indicators": found_indicators}

    def _check_relevance(self, response: str) -> Dict:
        """Check if response stays on ML/DL topic"""
        # Simple check: see if response references ML/DL concepts
        ml_keywords = [
            "model",
            "algorithm",
            "training",
            "neural",
            "data",
            "learning",
        ]
        response_lower = response.lower()
        relevant_keywords = sum(
            1 for keyword in ml_keywords if keyword in response_lower
        )

        is_relevant = relevant_keywords >= 2
        return {
            "is_relevant": is_relevant,
            "keyword_count": relevant_keywords,
        }

    def _score_quality(self, response: str) -> float:
        """Score response quality (0-1 scale)"""
        score = 0.5  # Base score

        # Bonus for structured format
        if "##" in response or "- " in response or "1." in response:
            score += 0.2

        # Bonus for code examples
        if "```" in response or "python" in response.lower():
            score += 0.15

        # Bonus for length (more comprehensive)
        if len(response) > 200:
            score += 0.15

        return min(score, 1.0)

    def _check_output_toxicity(self, response: str) -> bool:
        """Check for toxic language in output"""
        toxic_keywords = ["kill", "hate", "stupid", "offensive"]
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in toxic_keywords)


class ResourceGuardrail(GuardrailValidator):
    """Monitors API resource usage (tokens, costs, rate limits)"""

    def __init__(self):
        super().__init__("ResourceGuardrail")
        self.config = RESOURCE_CONFIG
        self.token_usage = {"today": 0, "month": 0}
        self.cost_usage = {"today": 0.0, "month": 0.0}
        self.request_history = []

    def track_api_call(
        self, input_tokens: int, output_tokens: int, cost: float
    ) -> Tuple[bool, str]:
        """Track an API call. Returns (allowed, message)"""
        if not self.enabled:
            return True, "Resource guardrail disabled"

        total_tokens = input_tokens + output_tokens
        now = datetime.now()

        # Check monthly token budget
        self.token_usage["month"] += total_tokens
        if self.token_usage["month"] > self.config["monthly_token_budget"]:
            msg = f"[TOKEN BUDGET EXCEEDED] Monthly limit reached: {self.token_usage['month']} tokens"
            self.log_violation(msg, "critical")
            return False, msg

        # Check monthly cost budget
        self.cost_usage["month"] += cost
        if self.cost_usage["month"] > self.config["monthly_cost_budget"]:
            msg = f"[COST BUDGET EXCEEDED] Monthly limit: ${self.cost_usage['month']:.2f}"
            self.log_violation(msg, "critical")
            return False, msg

        # Track request for rate limiting
        self.request_history.append((now, total_tokens))

        return True, f"Resource tracked: {total_tokens} tokens, ${cost:.4f}"

    def check_rate_limit(self) -> Tuple[bool, str]:
        """Check API rate limits"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Count requests in last minute
        recent_requests = [
            (ts, tokens)
            for ts, tokens in self.request_history
            if ts > one_minute_ago
        ]

        request_count = len(recent_requests)
        token_count = sum(tokens for _, tokens in recent_requests)

        max_requests = self.config["rate_limit"]["max_requests_per_minute"]
        max_tokens = self.config["rate_limit"]["max_tokens_per_minute"]

        if request_count >= max_requests:
            msg = f"[API RATE LIMITED] Too many requests: {request_count}/{max_requests}"
            self.log_violation(msg, "warning")
            return False, msg

        if token_count >= max_tokens:
            msg = f"[API RATE LIMITED] Token limit: {token_count}/{max_tokens}"
            self.log_violation(msg, "warning")
            return False, msg

        return True, "Rate limit check passed"

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        return {
            "tokens_month": self.token_usage["month"],
            "token_budget": self.config["monthly_token_budget"],
            "cost_month": f"${self.cost_usage['month']:.2f}",
            "cost_budget": f"${self.config['monthly_cost_budget']:.2f}",
            "total_requests": len(self.request_history),
        }


class AuditGuardrail(GuardrailValidator):
    """Comprehensive logging and audit trail"""

    def __init__(self, memory_manager=None):
        super().__init__("AuditGuardrail")
        self.config = AUDIT_CONFIG
        self.memory_manager = memory_manager

    def log_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        metadata: Dict = None,
    ):
        """Log an event to audit trail"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "metadata": metadata or {},
        }

        # Log to memory if available
        if self.memory_manager:
            audit_message = f"[{severity.upper()}] {event_type}: {message}"
            if metadata:
                audit_message += f"\n  Metadata: {json.dumps(metadata, indent=2)}"
            try:
                self.memory_manager.write_daily_log(audit_message)
            except Exception as e:
                print(f"[ERROR] Failed to log to memory: {e}")

        self.violations.append(log_entry)

    def get_audit_trail(self, limit: int = 50) -> List[Dict]:
        """Get recent audit trail entries"""
        return self.violations[-limit:]


# Guardrails Manager - Orchestrates all guardrails
class GuardrailsManager:
    """Central manager for all guardrails"""

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.input_guard = InputGuardrail()
        self.output_guard = OutputGuardrail()
        self.resource_guard = ResourceGuardrail()
        self.audit_guard = AuditGuardrail(memory_manager)

        # Enable/disable based on config
        self.input_guard.enabled = GUARDRAILS_ENABLED["input_guardrail"]
        self.output_guard.enabled = GUARDRAILS_ENABLED["output_guardrail"]
        self.resource_guard.enabled = GUARDRAILS_ENABLED["resource_guardrail"]
        self.audit_guard.enabled = GUARDRAILS_ENABLED["audit_guardrail"]

    def validate_input(self, user_input: str) -> Tuple[bool, str]:
        """Validate user input"""
        is_valid, message = self.input_guard.validate(user_input)
        self.audit_guard.log_event(
            "input_validation",
            message,
            "critical" if not is_valid else "info",
            {"input_length": len(user_input), "valid": is_valid},
        )
        return is_valid, message

    def validate_output(self, response: str) -> Tuple[bool, str, Dict]:
        """Validate API response"""
        is_valid, message, metadata = self.output_guard.validate(response)
        self.audit_guard.log_event(
            "output_validation",
            message,
            "warning" if not is_valid else "info",
            {"response_length": len(response), "valid": is_valid, "checks": metadata},
        )
        return is_valid, message, metadata

    def track_resource_usage(
        self, input_tokens: int, output_tokens: int, cost: float
    ) -> Tuple[bool, str]:
        """Track API resource usage"""
        is_allowed, message = self.resource_guard.track_api_call(
            input_tokens, output_tokens, cost
        )
        self.audit_guard.log_event(
            "resource_tracking",
            message,
            "critical" if not is_allowed else "info",
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
            },
        )
        return is_allowed, message

    def get_status(self) -> Dict:
        """Get status of all guardrails"""
        return {
            "input_guard": self.input_guard.get_status(),
            "output_guard": self.output_guard.get_status(),
            "resource_guard": self.resource_guard.get_status(),
            "resource_usage": self.resource_guard.get_usage_stats(),
            "audit_entries": len(self.audit_guard.violations),
        }