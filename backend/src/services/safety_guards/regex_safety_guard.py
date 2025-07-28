import re

from schemas.safety_guards import SafetyGuardResult, SafetyGuardType, SafetyIssue, SafetyRiskLevel
from services.safety_guards.regex_safety_guard_patterns import SAFETY_REGEX_GUARD_PATTERNS
from services.safety_guards.safety_guard import SafetyGuard


class RegexSafetyGuard(SafetyGuard):
    VERSION = "regex-guard-1.0.0"

    def __init__(self):
        """Initialize the regex safety guard with pre-compiled patterns."""
        self.compiled_patterns = {}
        # Sort patterns by risk level (HIGH first) for early exit optimization
        sorted_patterns = sorted(
            SAFETY_REGEX_GUARD_PATTERNS.items(),
            key=lambda x: (x[1].risk_level != SafetyRiskLevel.HIGH, x[0].value)
        )
        for issue_type, safety_guard_pattern in sorted_patterns:
            compiled_pattern = re.compile(
                safety_guard_pattern.pattern,
                re.IGNORECASE | re.DOTALL | re.VERBOSE
            )
            self.compiled_patterns[issue_type] = {
                'pattern': compiled_pattern,
                'guard_pattern': safety_guard_pattern
            }

    def _check_single_pattern(self, text: str, issue_type: str, pattern_data: dict) -> SafetyIssue | None:
        match = pattern_data['pattern'].search(text)
        if match:
            safety_guard_pattern = pattern_data['guard_pattern']
            return SafetyIssue(
                issue_type=safety_guard_pattern.type,
                issue_version=safety_guard_pattern.version,
                description=safety_guard_pattern.description,
                matched_text=match.group(),
                blocked_reason=safety_guard_pattern.blocked_reason,
                risk_level=safety_guard_pattern.risk_level,
                confidence_score=None,
            )
        return None

    def check_safety(self, text: str) -> SafetyGuardResult:
        issues = []
        for issue_type, pattern_data in self.compiled_patterns.items():
            result = self._check_single_pattern(text, issue_type, pattern_data)
            if result is not None:
                issues.append(result)
                if result.risk_level == SafetyRiskLevel.HIGH:
                    break
        should_block = any(issue.risk_level == SafetyRiskLevel.HIGH for issue in issues)
        return SafetyGuardResult(
            guard_type=SafetyGuardType.REGEX,
            guard_version=self.VERSION,
            is_blocked=should_block,
            issues=issues,
        )
