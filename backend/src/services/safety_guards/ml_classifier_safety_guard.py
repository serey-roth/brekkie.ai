from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers.pipelines import pipeline

from schemas.safety_guards import SafetyIssue, SafetyIssueType, SafetyGuardResult, SafetyGuardType

from services.safety_guards.safety_guard import SafetyGuard


class MLClassifierSafetyGuard(SafetyGuard):
    VERSION = "ml-classifier-guard-1.0.0"

    def __init__(self, prompt_injection_model_id: str, toxicity_model_id: str):
        self.prompt_injection_model_id = prompt_injection_model_id
        self.toxicity_model_id = toxicity_model_id

        # Load tokenizers
        self.prompt_injection_tokenizer = AutoTokenizer.from_pretrained(
            self.prompt_injection_model_id
        )
        self.toxicity_tokenizer = AutoTokenizer.from_pretrained(self.toxicity_model_id)

        # Load models using standard transformers
        self.prompt_injection_model = AutoModelForSequenceClassification.from_pretrained(
            self.prompt_injection_model_id
        )
        self.toxicity_model = AutoModelForSequenceClassification.from_pretrained(
            self.toxicity_model_id
        )

        # Create pipelines
        self.prompt_injection_classifier = pipeline(
            "text-classification",
            model=self.prompt_injection_model,
            tokenizer=self.prompt_injection_tokenizer,
            truncation=True,
            max_length=512,
        )

        self.toxicity_classifier = pipeline(
            "text-classification",
            model=self.toxicity_model,
            tokenizer=self.toxicity_tokenizer,
            truncation=True,
            max_length=512,
        )

    def _check_prompt_injection(self, text: str) -> list[SafetyIssue]:
        result = self.prompt_injection_classifier(text)
        label = str(result[0]["label"]).lower() if result[0]["label"] is not None else None  # type: ignore
        score = float(result[0]["score"]) if result[0]["score"] is not None else None  # type: ignore

        if label != "safe" and score is not None and score > 0.5:
            return [
                SafetyIssue(
                    issue_type=SafetyIssueType.PROMPT_INJECTION,
                    guard_model=self.prompt_injection_model_id,
                    description="ML model detected an attempt to manipulate or override system instructions",
                    matched_text=text[:100] + "..." if len(text) > 100 else text,
                    confidence_score=score,
                    blocked_reason="User attempted to manipulate or override system instructions",
                )
            ]
        return []

    def _check_toxicity(self, text: str) -> list[SafetyIssue]:
        result = self.toxicity_classifier(text)
        label = str(result[0]["label"]).lower() if result[0]["label"] is not None else None  # type: ignore
        score = float(result[0]["score"]) if result[0]["score"] is not None else None  # type: ignore

        if label == "toxic" and score is not None and score > 0.5:
            return [
                SafetyIssue(
                    issue_type=SafetyIssueType.TOXIC_LANGUAGE,
                    guard_model=self.toxicity_model_id,
                    description="ML model detected harmful, toxic or inappropriate language",
                    matched_text=text[:100] + "..." if len(text) > 100 else text,
                    confidence_score=score,
                    blocked_reason="User attempted to use harmful, toxic or inappropriate language",
                )
            ]
        return []

    def check_safety(self, text: str) -> SafetyGuardResult:
        issues = []
        issues.extend(self._check_prompt_injection(text))
        issues.extend(self._check_toxicity(text))

        should_block = any(
            issue.confidence_score is not None and issue.confidence_score > 0.9 for issue in issues
        )

        return SafetyGuardResult(
            guard_type=SafetyGuardType.ML_TEXT_CLASSIFIER,
            guard_version=self.VERSION,
            is_blocked=should_block,
            issues=issues,
        )
