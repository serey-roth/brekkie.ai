from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from services.safety_guards.regex_safety_guard import RegexSafetyGuard
from services.safety_guards.ml_classifier_safety_guard import MLClassifierSafetyGuard

from schemas.safety_guards import SafetyGuardResult, SafetyIssue

class ChatSessionMessageGuard:
    def __init__(
        self, 
        regex_safety_guard: RegexSafetyGuard,
        ml_classifier_safety_guard: MLClassifierSafetyGuard,
        response_llm: BaseChatModel,
    ):
        self.regex_safety_guard = regex_safety_guard
        self.ml_classifier_safety_guard = ml_classifier_safety_guard
        self.response_llm = response_llm
        
    def check_message_safety(self, user_message_content: str) -> SafetyGuardResult | None:
        regex_result = self.regex_safety_guard.check_safety(user_message_content)
        if regex_result.is_blocked:
            return regex_result
        
        ml_result = self.ml_classifier_safety_guard.check_safety(user_message_content)
        if ml_result.is_blocked:
            return ml_result
        
        return None
    
    async def get_rejection_message(self, user_message_content: str, issues: List[SafetyIssue]) -> str:
        if len(issues) == 0:
            raise ValueError("Expected at least one issue: {issues}")
        
        safety_reasons = "\n".join([f"• {issue.blocked_reason}" for issue in issues])
        
        # TODO: Move this to a prompt folder?
        human_message_content = (
            f"The user message was blocked due to the following safety reasons:\n\n"
            f"{safety_reasons}\n\n"
            f"You are Milo, a mindful AI companion who's casual, conversational, and authentic. "
            f"Respond as Milo would - firm but kind, no AI formalities, no overly polite language. "
            f"Keep it under 50 words. Don't explain the specific reasons or offer alternatives. "
            f"Just be direct and authentic in Milo's voice."
            f"IMPORTANT: Return ONLY the message text. No markdown, no explanations, no quotes."
            f"Here is the user message:\n\n"
            f"{user_message_content}"
        )
        
        response = await self.response_llm.ainvoke([HumanMessage(content=human_message_content)])
        return response.content