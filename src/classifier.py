import os
import re
import json
import joblib
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_DOMAINS = ["AI", "ML", "DL", "NLP", "RL", "CV"]
DOMAIN_ALIASES = {
    "ARTIFICIAL INTELLIGENCE": "AI",
    "MACHINE LEARNING": "ML",
    "DEEP LEARNING": "DL",
    "NATURAL LANGUAGE PROCESSING": "NLP",
    "REINFORCEMENT LEARNING": "RL",
    "COMPUTER VISION": "CV",
}

DEFAULT_MODEL_DIR = Path("workspace/models/distilbert_model")

class DistilBertClassifier:
    """Wrapper class for loading and performing inference with the fine-tuned DistilBERT model."""

    def __init__(self, model_dir: Optional[str] = None, min_confidence: float = 0.45):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self.min_confidence = min_confidence
        self.backend = "llm"  # Fallback backend default
        
        self.model = None
        self.tokenizer = None
        self.label_encoder = None
        self.device = "cpu"
        self.load_error = None
        
        self._load_resources()

    def _load_resources(self):
        """Load tokenizer, sequence classification model, and label encoder from local disk."""
        if not self.model_dir.exists():
            self.load_error = f"Model directory does not exist: {self.model_dir}"
            print(f"[CLASSIFIER-WARN] {self.load_error}. Falling back to LLM classifier.")
            return

        try:
            import torch
            from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast
            
            print(f"[CLASSIFIER] Loading DistilBERT model from {self.model_dir}...")
            self.tokenizer = DistilBertTokenizerFast.from_pretrained(str(self.model_dir))
            self.model = DistilBertForSequenceClassification.from_pretrained(str(self.model_dir))
            
            # Load label encoder
            encoder_path = self.model_dir / "label_encoder.pkl"
            if encoder_path.exists():
                self.label_encoder = joblib.load(str(encoder_path))
            
            # Set to GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.model.eval()
            
            self.backend = "distilbert"
            self.load_error = None
            print(f"[CLASSIFIER] Model loaded successfully on device: {self.device}")
        except ImportError as e:
            self.load_error = f"Missing dependency for local classification: {str(e)}"
            self.model = None
            self.tokenizer = None
            self.label_encoder = None
            self.backend = "llm"
            print(f"[CLASSIFIER-WARN] Local classification dependencies missing ({e}). Falling back to LLM classifier.")
        except Exception as e:
            self.load_error = str(e)
            self.model = None
            self.tokenizer = None
            self.label_encoder = None
            self.backend = "llm"
            print(f"[CLASSIFIER-ERROR] Error loading local model: {e}. Falling back to LLM classifier.")

    def classify(self, query: str) -> Tuple[str, float, str]:
        """
        Classifies a user query into one of the domains: AI, ML, DL, NLP, RL, CV, or UNKNOWN.
        Returns:
            Tuple[domain_name (str), confidence_score (float), backend_used (str)]
        """
        query = query.strip()
        if not query:
            return "UNKNOWN", 0.0, "error"

        # Try local DistilBERT first
        if self.backend == "distilbert" and self.model is not None and self.tokenizer is not None:
            try:
                import torch
                inputs = self.tokenizer(
                    query,
                    truncation=True,
                    padding=True,
                    max_length=128,
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.softmax(logits, dim=-1)[0]
                
                best_idx = int(torch.argmax(probabilities).item())
                confidence = float(probabilities[best_idx].item())
                
                # Fetch domain label using label encoder or config ID map
                if self.label_encoder is not None:
                    raw_label = self.label_encoder.inverse_transform([best_idx])[0]
                else:
                    id2label = getattr(self.model.config, "id2label", {}) or {}
                    raw_label = id2label.get(best_idx, str(best_idx))
                
                domain = self._normalize_label(str(raw_label))
                if domain in SUPPORTED_DOMAINS and confidence >= self.min_confidence:
                    return domain, confidence, "distilbert"
                else:
                    # Low confidence classification falls back to general classification
                    return "UNKNOWN", confidence, "distilbert"
            except Exception as e:
                print(f"[CLASSIFIER-WARN] DistilBERT classification failed: {e}. Falling back to LLM.")
                # Pass through to LLM fallback
        
        return self._llm_classify(query)

    def _llm_classify(self, query: str) -> Tuple[str, float, str]:
        """Fallback classifier utilizing OpenAI's Chat Completions API."""
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return "UNKNOWN", 0.0, "unavailable"

        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        prompt = (
            "Classify the user question into exactly one of these domain labels:\n"
            "- AI: Artificial Intelligence (general search, planning, agents, logic, expert systems, heuristics)\n"
            "- ML: Traditional Machine Learning (regression, classification, clustering, SVMs, decision trees)\n"
            "- DL: Deep Learning (neural networks, activation functions, CNNs, GANs, autoencoders, transformers)\n"
            "- NLP: Natural Language Processing (lemmatization, tf-idf, sentiment analysis, word embeddings, NER)\n"
            "- RL: Reinforcement Learning (Q-learning, actor-critic, MDPs, reward shaping, exploration vs exploitation)\n"
            "- CV: Computer Vision (image segmentation, object detection like YOLO, edge detection, optical flow)\n"
            "- UNKNOWN: Out-of-scope or unrelated topics (cooking, weather, general facts, coding unrelated to AI/ML)\n\n"
            "Return JSON only with keys 'domain' and 'confidence'.\n"
            "Confidence must be a number between 0.0 and 1.0.\n\n"
            f"Question: {query}"
        )

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a strict domain classifier that outputs valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = (response.choices[0].message.content or "").strip()
            payload = json.loads(content)
            
            domain = self._normalize_label(str(payload.get("domain", "UNKNOWN")))
            confidence = float(payload.get("confidence", 0.0))
            
            if domain not in SUPPORTED_DOMAINS:
                return "UNKNOWN", 0.0, "llm"
            return domain, max(0.0, min(confidence, 1.0)), "llm"
        except Exception as e:
            print(f"[CLASSIFIER-ERROR] LLM classification error: {e}")
            return "UNKNOWN", 0.0, "llm"

    @staticmethod
    def _normalize_label(label: str) -> str:
        """Clean and map label string to standard domain code (e.g. Machine Learning -> ML)."""
        cleaned = re.sub(r"[^A-Za-z ]+", " ", label).strip().upper()
        return DOMAIN_ALIASES.get(cleaned, cleaned)
