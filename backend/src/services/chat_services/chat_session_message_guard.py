from typing import List

from schemas.safety_guards import SafetyGuardResult, SafetyIssue, SafetyRiskLevel
from services.safety_guards.regex_safety_guard import RegexSafetyGuard


class ChatSessionMessageGuard:
    def __init__(
        self,
        regex_safety_guard: RegexSafetyGuard,
    ):
        self.regex_safety_guard = regex_safety_guard

    def check_message_safety(self, user_message_content: str) -> SafetyGuardResult | None:
        regex_result = self.regex_safety_guard.check_safety(user_message_content)
        if regex_result.is_blocked:
            return regex_result
        return None

    async def get_rejection_message(
        self, user_message_content: str, issues: List[SafetyIssue]
    ) -> str:
        if len(issues) == 0:
            raise ValueError("Expected at least one issue: {issues}")

        # Fast template-based rejection message
        # No LLM call needed - much faster
        if any(issue.risk_level == SafetyRiskLevel.HIGH for issue in issues):
            return (
                "I can't help with that. Let's keep things friendly and focused on what I do best!"
            )
        else:
            return "That's not really my thing. How about we chat about something else?"
