import torch
from transformers import AutoTokenizer, pipeline
from optimum.onnxruntime import ORTModelForSequenceClassification
import os

from schemas.safety_guards import SafetyIssue, SafetyIssueType, SafetyGuardResult, SafetyGuardType

from services.safety_guards.safety_guard import SafetyGuard


class MLClassifierSafetyGuard(SafetyGuard):
    VERSION = "ml-classifier-guard-1.0.0"
    
    def __init__(self, prompt_injection_model_id: str, toxicity_model_id: str):
        self.prompt_injection_model_id = prompt_injection_model_id
        self.toxicity_model_id = toxicity_model_id
        
        # Load tokenizers
        self.prompt_injection_tokenizer = AutoTokenizer.from_pretrained(self.prompt_injection_model_id)
        self.toxicity_tokenizer = AutoTokenizer.from_pretrained(self.toxicity_model_id)
        
        # Load optimized models using Optimum - only export if not already converted
        prompt_injection_onnx_path = f"src/ml_models/{self.prompt_injection_model_id}-onnx"
        toxicity_onnx_path = f"src/ml_models/{self.toxicity_model_id}-onnx"
        
        # Check if ONNX models already exist
        if os.path.exists(prompt_injection_onnx_path):
            print(f"Loading existing ONNX model from {prompt_injection_onnx_path}")
            self.prompt_injection_model = ORTModelForSequenceClassification.from_pretrained(
                prompt_injection_onnx_path,
                provider="CPUExecutionProvider"
            )
        else:
            print(f"Converting {self.prompt_injection_model_id} to ONNX...")
            self.prompt_injection_model = ORTModelForSequenceClassification.from_pretrained(
                self.prompt_injection_model_id,
                export=True,
                provider="CPUExecutionProvider"
            )
            # Save the model to the filesystem
            self.prompt_injection_model.save_pretrained(prompt_injection_onnx_path)
        
        if os.path.exists(toxicity_onnx_path):
            print(f"Loading existing ONNX model from {toxicity_onnx_path}")
            self.toxicity_model = ORTModelForSequenceClassification.from_pretrained(
                toxicity_onnx_path,
                provider="CPUExecutionProvider"
            )
        else:
            print(f"Converting {self.toxicity_model_id} to ONNX...")
            self.toxicity_model = ORTModelForSequenceClassification.from_pretrained(
                self.toxicity_model_id,
                export=True,
                provider="CPUExecutionProvider"
            )
            # Save the model to the filesystem
            self.toxicity_model.save_pretrained(toxicity_onnx_path)
        
        # Create optimized pipelines
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
        label = result[0]["label"].lower()
        score = result[0]["score"]
        
        if label != "safe" and score > 0.5:
            return [
                SafetyIssue(
                    issue_type=SafetyIssueType.PROMPT_INJECTION, 
                    guard_model=self.prompt_injection_model_id,
                    description="ML model detected an attempt to manipulate or override system instructions", 
                    matched_text=text[:100] + "..." if len(text) > 100 else text, 
                    confidence_score=score,
                    blocked_reason="User attempted to manipulate or override system instructions"
                )]
        return []
    
    def _check_toxicity(self, text: str) -> list[SafetyIssue]:
        result = self.toxicity_classifier(text)
        label = result[0]["label"].lower()
        score = result[0]["score"]
        
        if label == "toxic" and score > 0.5:
            return [
                SafetyIssue(
                    issue_type=SafetyIssueType.TOXIC_LANGUAGE, 
                    guard_model=self.toxicity_model_id,
                    description="ML model detected harmful, toxic or inappropriate language",
                    matched_text=text[:100] + "..." if len(text) > 100 else text, 
                    confidence_score=score,
                    blocked_reason="User attempted to use harmful, toxic or inappropriate language"
                )]
        return []
    
    def check_safety(self, text: str) -> SafetyGuardResult:
        issues = []
        issues.extend(self._check_prompt_injection(text))
        issues.extend(self._check_toxicity(text))
        
        should_block = any(issue.confidence_score is not None and issue.confidence_score > 0.9 for issue in issues)
        
        return SafetyGuardResult(
            guard_type=SafetyGuardType.ML_TEXT_CLASSIFIER,
            guard_version=self.VERSION,
            is_blocked=should_block,
            issues=issues,
        )
