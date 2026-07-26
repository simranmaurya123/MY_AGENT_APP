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

    def _check_keyword_domain(self, query: str) -> Optional[str]:
        """Check for explicit domain keywords to guarantee accurate domain classification."""
        q = query.lower()
        
        keywords = {
            "NLP": ["natural language", "nlp", "tokenization", "lemmatization", "tf-idf", "word2vec", "glove", "bert", "transformer", "transformers", "llm", "llms", "sentiment analysis", "named entity", "bleu score"],
            "RL": ["reinforcement", "rl", "q-learning", "actor-critic", "mdp", "policy gradient", "reward shaping", "exploration vs exploitation", "deep q"],
            "CV": ["computer vision", "cv", "image segmentation", "object detection", "yolo", "canny", "optical flow", "sift", "resnet", "depth estimation", "edge detection"],
            "DL": ["deep learning", "dl", "neural network", "backpropagation", "activation function", "relu", "sigmoid", "cnn", "convolutional", "gan", "autoencoder", "batch norm", "dropout"],
            "ML": ["machine learning", "ml", "supervised learning", "unsupervised learning", "decision tree", "gradient descent", "support vector", "svm", "k-means", "random forest", "bias-variance", "cross validation", "pca"],
            "AI": ["artificial intelligence", "ai", "heuristic", "pathfinding", "turing test", "expert system", "expert systems", "symbolic ai", "a* algorithm", "a* search"]
        }
        
        for domain, terms in keywords.items():
            for term in terms:
                if re.search(r'\b' + re.escape(term) + r'\b', q):
                    return domain
        return None

    def classify(self, query: str) -> Tuple[str, float, str]:
        """
        Classifies a user query into one of the domains: AI, ML, DL, NLP, RL, CV, or UNKNOWN.
        Returns:
            Tuple[domain_name (str), confidence_score (float), backend_used (str)]
        """
        query = query.strip()
        if not query:
            return "UNKNOWN", 0.0, "error"

        # 1. Quick Keyword Domain Match
        kw_domain = self._check_keyword_domain(query)
        if kw_domain in SUPPORTED_DOMAINS:
            return kw_domain, 0.95, "keyword"

        # 2. Try LLM Classifier first for non-keyword text if API key is present
        if os.getenv("OPENAI_API_KEY"):
            llm_domain, llm_conf, llm_backend = self._llm_classify(query)
            if llm_domain != "UNKNOWN":
                return llm_domain, llm_conf, llm_backend

        # 3. Offline DistilBERT Inference (Requires high confidence >= 0.85 when no keywords match)
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
                
                if self.label_encoder is not None:
                    raw_label = self.label_encoder.inverse_transform([best_idx])[0]
                else:
                    id2label = getattr(self.model.config, "id2label", {}) or {}
                    raw_label = id2label.get(best_idx, str(best_idx))
                
                domain = self._normalize_label(str(raw_label))
                if domain in SUPPORTED_DOMAINS and confidence >= 0.85:
                    return domain, confidence, "distilbert"
            except Exception as e:
                print(f"[CLASSIFIER-WARN] DistilBERT classification failed: {e}.")

        return "UNKNOWN", 0.0, "classifier"

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
