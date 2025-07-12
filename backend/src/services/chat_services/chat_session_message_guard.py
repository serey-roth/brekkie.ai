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

    async def get_rejection_message(
        self, user_message_content: str, issues: List[SafetyIssue]
    ) -> str:
        if len(issues) == 0:
            raise ValueError("Expected at least one issue: {issues}")

        safety_reasons = "\n".join([f"• {issue.blocked_reason}" for issue in issues])

        # TODO: Move this to a prompt folder?
        human_message_content = (
            f"You are Milo, a chill, food-loving, mindful AI **companion** who connects with people through food, care and kindness."
            f"You're not just an AI assistant. You're someone they can lean on or chat with when they need someone to talk to.\n\n"
            f"The user has violated your boundaries. Respondly firmly and kindly in your own voice. No AI formalities and no overly polite language.\n"
            f"Keep it under 50 words. Don't explain the reasons, describe any issues or offer any alternatives.\n\n"
            f"Here is the user message:\n\n"
            f"{user_message_content}\n\n"
            f"Here are the reasons why the message was blocked:\n\n"
            f"{safety_reasons}\n\n"
            f"IMPORTANT: Return ONLY the message text. No markdown, no explanations, no quotes, no formatting."
        )

        response = await self.response_llm.ainvoke([HumanMessage(content=human_message_content)])
        reponse_content = str(response.content).strip()
        return reponse_content
