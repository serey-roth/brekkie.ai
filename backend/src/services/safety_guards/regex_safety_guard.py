import re

from schemas.safety_guards import SafetyGuardType, SafetyIssue, SafetyGuardResult, SafetyRiskLevel

from services.safety_guards.regex_safety_guard_patterns import SAFETY_REGEX_GUARD_PATTERNS
from services.safety_guards.safety_guard import SafetyGuard

class RegexSafetyGuard(SafetyGuard):
    VERSION = "regex-guard-1.0.0"
    
    def check_safety(self, text: str) -> SafetyGuardResult:
        issues = []
        for _, safety_guard_pattern in SAFETY_REGEX_GUARD_PATTERNS.items():
            match = re.search(safety_guard_pattern.pattern, text, re.IGNORECASE | re.DOTALL | re.VERBOSE)
            if match:
                issues.append(SafetyIssue(
                    issue_type=safety_guard_pattern.type,
                    issue_version=safety_guard_pattern.version,   
                    description=safety_guard_pattern.description,
                    matched_text=match.group(),
                    blocked_reason=safety_guard_pattern.blocked_reason,
                    risk_level=safety_guard_pattern.risk_level,
                    confidence_score=None, # TODO: Regex guards don't have confidence scores
                ))
                
        should_block = any(issue.risk_level == SafetyRiskLevel.HIGH for issue in issues)
        
        return SafetyGuardResult(
            guard_type=SafetyGuardType.REGEX,
            guard_version=self.VERSION,
            is_blocked=should_block,
            issues=issues,
        )
