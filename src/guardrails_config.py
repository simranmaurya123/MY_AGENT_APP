"""Guardrails configuration file.
    This file contains the configuration for the guardrails system, 
    including the rules and policies that govern the behavior of the system.
"""

import re

INPUT_CONFIG = {
    "max_length": 1000,
    "min_length": 10,
    "allowed_characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
    "disallowed_patterns": [
        r"\b(?:spam|scam|fraud)\b",
        r"\b(?:hack|crack|exploit)\b"
    ],
    
    
    # SQL injection and code injection patterns
    "injection_patterns": [
        r"(?i)\bdrop\b",
        r"(?i)\bdelete\b",
        r"(?i)\binsert\b",
        r"(?i)\bupdate\b",
        r"(?i)\bselect\b",
        r"(?i)\bunion\b",
        r"(?i)--",
        r"(?i)\bOR\s+1\b",
        r"(?i)\bAND\s+1\b",
        r"';.*--",
        r'";.*--',
    ],
    # Rate limiting config
    "rate_limit": {
        "max_queries": 10,
        "time_window_seconds": 60,
    }
}

OUTPUT_CONFIG = {
    "max_length": 3000,
    "min_length": 20,
    "allowed_characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:'\"()",
    "disallowed_patterns": [
        r"\b(?:spam|scam|fraud)\b",
        r"\b(?:hack|crack|exploit)\b"
    ],
    # Hallucination indicators (overconfident language)
    "hallucination_indicators": [
        "I am 100% certain",
        "definitely always",
        "never fails",
        "impossible to",
        "guaranteed to work",
        "without exception",
        "absolutely impossible",
    ],
    "quality_thresholds": {
        "min_relevance_score": 0.5,  # 0-1 scale
        "min_clarity_score": 0.5,
        "min_usefulness_score": 0.5,
    },
}

RESOURCE_CONFIG = {
    "monthly_token_budget": 10000,
    "monthly_cost_budget": 50.0,  # USD
    "rate_limit": {
        "max_requests_per_minute": 10,
        "max_tokens_per_minute": 8000,
    },
}

AUDIT_CONFIG = {
    "log_all_violations": True,
    "log_file": "memory/audit_log.md",
    "severity_levels": ["info", "warning", "critical"],
    "alert_on_critical": True,
}

# Guardrails Enable/Disable
GUARDRAILS_ENABLED = {
    "input_guardrail": True,
    "output_guardrail": True,
    "resource_guardrail": True,
    "audit_guardrail": True,
}



     
  
