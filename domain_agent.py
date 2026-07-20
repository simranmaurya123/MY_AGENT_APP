from __future__ import annotations

import json
import math
import os
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

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

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
DEFAULT_KNOWLEDGE_BASE_CANDIDATES = (
    Path("workspace/data/knowledge_base"),
    Path("knowledge_base"),
)
DEFAULT_MODEL_CANDIDATES = (
    Path("distilbert_model"),
    Path("workspace/output/distilbert_model"),
    Path("workspace/models/distilbert_model"),
    Path("workspace/output"),
    Path("workspace/models"),
    Path("workspace/data"),
)
MODEL_SIGNATURE_FILES = {
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
}
MODEL_WEIGHT_FILES = {
    "pytorch_model.bin",
    "model.safetensors",
}


def _is_hf_model_dir(candidate: Path) -> bool:
    if not candidate.is_dir():
        return False

    file_names = {item.name for item in candidate.iterdir() if item.is_file()}
    has_signature = "config.json" in file_names and bool(file_names & MODEL_SIGNATURE_FILES)
    has_weights = bool(file_names & MODEL_WEIGHT_FILES)
    return has_signature and has_weights


def _scan_for_hf_model_dir(base_dir: Path, depth_limit: int = 4) -> Optional[Path]:
    if not base_dir.exists():
        return None

    if _is_hf_model_dir(base_dir):
        return base_dir

    for current in base_dir.rglob("*"):
        if not current.is_dir():
            continue

        try:
            relative_depth = len(current.relative_to(base_dir).parts)
        except Exception:
            continue

        if relative_depth > depth_limit:
            continue

        if _is_hf_model_dir(current):
            return current

    return None


def _extract_model_zip_if_present() -> Optional[Path]:
    output_dir = Path("workspace/output")
    if not output_dir.exists():
        return None

    zip_files = sorted(output_dir.rglob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for zip_path in zip_files:
        try:
            target_dir = output_dir / "_extracted_models" / zip_path.stem
            marker_file = target_dir / ".extract_complete"

            if not marker_file.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(target_dir)
                marker_file.write_text("ok", encoding="utf-8")

            discovered = _scan_for_hf_model_dir(target_dir)
            if discovered is not None:
                return discovered
        except Exception:
            continue

    return None


def resolve_model_dir(explicit_dir: Optional[str] = None) -> Path:
    if explicit_dir:
        return Path(explicit_dir)

    env_dir = os.getenv("DISTILBERT_MODEL_DIR")
    if env_dir:
        return Path(env_dir)

    extracted_dir = _extract_model_zip_if_present()
    if extracted_dir is not None:
        return extracted_dir

    for candidate in DEFAULT_MODEL_CANDIDATES:
        if _is_hf_model_dir(candidate):
            return candidate

        discovered = _scan_for_hf_model_dir(candidate)
        if discovered is not None:
            return discovered

    return DEFAULT_MODEL_CANDIDATES[0]


def resolve_knowledge_base_dir(explicit_dir: Optional[str] = None) -> Path:
    if explicit_dir:
        return Path(explicit_dir)

    env_dir = os.getenv("KNOWLEDGE_BASE_DIR")
    if env_dir:
        return Path(env_dir)

    for candidate in DEFAULT_KNOWLEDGE_BASE_CANDIDATES:
        if candidate.exists():
            return candidate

    return DEFAULT_KNOWLEDGE_BASE_CANDIDATES[0]


@dataclass(frozen=True)
class KnowledgeChunk:
    domain: str
    source: str
    text: str
    tokens: Counter[str]


class DistilBertDomainClassifier:
    def __init__(self, model_dir: Optional[str] = None, min_confidence: float = 0.45):
        self.model_dir = resolve_model_dir(model_dir)
        self.min_confidence = min_confidence
        self.backend = "llm"
        self._classifier = None
        self._tokenizer = None
        self._torch = None
        self._load_error: Optional[str] = None
        self._load_model()

    def _load_model(self) -> None:
        if not self.model_dir.exists():
            self._load_error = f"Model directory not found: {self.model_dir}"
            return

        try:
            import torch
            from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast

            tokenizer = DistilBertTokenizerFast.from_pretrained(str(self.model_dir))
            classifier = DistilBertForSequenceClassification.from_pretrained(str(self.model_dir))
            classifier.eval()

            self._classifier = classifier
            self._tokenizer = tokenizer
            self._torch = torch
            self.backend = "distilbert"
            self._load_error = None
        except Exception as exc:
            self._load_error = str(exc)
            self._classifier = None
            self._tokenizer = None
            self._torch = None
            self.backend = "llm"

    def classify(self, question: str) -> tuple[str, float, str]:
        if self._classifier is not None and self._tokenizer is not None and self._torch is not None:
            try:
                inputs = self._tokenizer(
                    question,
                    truncation=True,
                    padding=True,
                    return_tensors="pt",
                )
                with self._torch.no_grad():
                    logits = self._classifier(**inputs).logits
                    probabilities = self._torch.softmax(logits, dim=-1)[0]

                best_index = int(self._torch.argmax(probabilities).item())
                confidence = float(probabilities[best_index].item())
                id2label = getattr(self._classifier.config, "id2label", {}) or {}
                raw_label = id2label.get(best_index, str(best_index))
                label = self._normalize_label(str(raw_label))
                if label in SUPPORTED_DOMAINS and confidence >= self.min_confidence:
                    return label, confidence, "distilbert"
            except Exception:
                pass

        return self._llm_classify(question)

    def _llm_classify(self, question: str) -> tuple[str, float, str]:
        client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        if client is None:
            return "UNKNOWN", 0.0, "unavailable"

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
            f"Question: {question}"
        )

        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a strict JSON classifier."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            content = (response.choices[0].message.content or "").strip()
            match = re.search(r"\{.*\}", content, flags=re.DOTALL)
            if not match:
                return "UNKNOWN", 0.0, "llm"

            payload = json.loads(match.group(0))
            domain = self._normalize_label(str(payload.get("domain", "UNKNOWN")))
            confidence = float(payload.get("confidence", 0.0))
            if domain not in SUPPORTED_DOMAINS:
                return "UNKNOWN", 0.0, "llm"
            return domain, max(0.0, min(confidence, 1.0)), "llm"
        except Exception:
            return "UNKNOWN", 0.0, "llm"

    @staticmethod
    def _normalize_label(label: str) -> str:
        cleaned = re.sub(r"[^A-Za-z ]+", " ", label).strip().upper()
        return DOMAIN_ALIASES.get(cleaned, cleaned)

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error


class KnowledgeRetriever:
    def __init__(self, knowledge_base_dir: Optional[str] = None):
        self.knowledge_base_dir = resolve_knowledge_base_dir(knowledge_base_dir)
        self._chunks: list[KnowledgeChunk] = []
        self._loaded = False

    def _tokenize(self, text: str) -> Counter[str]:
        return Counter(TOKEN_PATTERN.findall(text.lower()))

    def _chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 200) -> Iterable[str]:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return

        if len(cleaned) <= chunk_size:
            yield cleaned
            return

        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + chunk_size)
            yield cleaned[start:end]
            if end >= len(cleaned):
                break
            start = max(0, end - overlap)

    def _load_pdf(self, file_path: Path, domain: str) -> None:
        try:
            reader = PdfReader(str(file_path))
            for page_index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                for chunk_index, chunk in enumerate(self._chunk_text(page_text), start=1):
                    if not chunk:
                        continue
                    self._chunks.append(
                        KnowledgeChunk(
                            domain=domain,
                            source=f"{file_path.name} | page {page_index} | chunk {chunk_index}",
                            text=chunk,
                            tokens=self._tokenize(chunk),
                        )
                    )
        except Exception:
            return

    def _load_text_file(self, file_path: Path, domain: str) -> None:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        for chunk_index, chunk in enumerate(self._chunk_text(text), start=1):
            if not chunk:
                continue
            self._chunks.append(
                KnowledgeChunk(
                    domain=domain,
                    source=f"{file_path.name} | chunk {chunk_index}",
                    text=chunk,
                    tokens=self._tokenize(chunk),
                )
            )

    def _load_csv(self, file_path: Path, domain: str) -> None:
        try:
            import pandas as pd

            df = pd.read_csv(file_path)
        except Exception:
            return

        self._load_dataframe(df, file_path, domain)

    def _load_excel(self, file_path: Path, domain: str) -> None:
        try:
            import pandas as pd

            sheets = pd.read_excel(file_path, sheet_name=None)
        except Exception:
            return

        for sheet_name, df in sheets.items():
            self._load_dataframe(df, file_path, domain, sheet_name=sheet_name)

    def _load_dataframe(self, df: pd.DataFrame, file_path: Path, domain: str, sheet_name: Optional[str] = None) -> None:
        if df.empty:
            return

        preview_rows = min(len(df), 60)
        subset = df.head(preview_rows).fillna("")
        rows: list[str] = []
        for _, row in subset.iterrows():
            pieces = [f"{column}: {row[column]}" for column in subset.columns]
            rows.append("; ".join(pieces))

        header = f"{file_path.name}"
        if sheet_name:
            header = f"{header} | sheet {sheet_name}"

        for chunk_index, chunk in enumerate(self._chunk_text("\n".join([header, *rows])), start=1):
            if not chunk:
                continue
            self._chunks.append(
                KnowledgeChunk(
                    domain=domain,
                    source=f"{header} | chunk {chunk_index}",
                    text=chunk,
                    tokens=self._tokenize(chunk),
                )
            )

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        if not self.knowledge_base_dir.exists():
            self._loaded = True
            return

        for domain_dir in sorted(self.knowledge_base_dir.iterdir()):
            if not domain_dir.is_dir():
                continue

            domain = domain_dir.name.upper()
            if domain not in SUPPORTED_DOMAINS:
                continue

            for file_path in sorted(domain_dir.rglob("*")):
                if not file_path.is_file():
                    continue

                suffix = file_path.suffix.lower()
                if suffix == ".pdf":
                    self._load_pdf(file_path, domain)
                elif suffix == ".csv":
                    self._load_csv(file_path, domain)
                elif suffix in {".xlsx", ".xls"}:
                    self._load_excel(file_path, domain)
                elif suffix in {".md", ".txt"}:
                    self._load_text_file(file_path, domain)

        self._loaded = True

    def retrieve(self, question: str, domain: str, top_k: int = 4) -> list[KnowledgeChunk]:
        self._ensure_loaded()
        if not self._chunks:
            return []

        query_tokens = self._tokenize(question)
        if not query_tokens:
            return []

        search_domains = self._search_domains(domain)
        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk in self._chunks:
            if chunk.domain not in search_domains:
                continue

            score = self._cosine_score(query_tokens, chunk.tokens)
            if chunk.domain == domain:
                score *= 1.3
            elif chunk.domain == "AI" and domain != "AI":
                score *= 1.1

            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def _search_domains(self, domain: str) -> set[str]:
        normalized = domain.upper()
        if normalized == "AI":
            return set(SUPPORTED_DOMAINS)
        return {normalized, "AI"} if normalized in SUPPORTED_DOMAINS else set(SUPPORTED_DOMAINS)

    def _cosine_score(self, query_tokens: Counter[str], chunk_tokens: Counter[str]) -> float:
        shared = set(query_tokens) & set(chunk_tokens)
        if not shared:
            return 0.0

        dot_product = sum(query_tokens[token] * chunk_tokens[token] for token in shared)
        query_norm = math.sqrt(sum(value * value for value in query_tokens.values()))
        chunk_norm = math.sqrt(sum(value * value for value in chunk_tokens.values()))
        if not query_norm or not chunk_norm:
            return 0.0
        return dot_product / (query_norm * chunk_norm)

    @property
    def chunk_count(self) -> int:
        self._ensure_loaded()
        return len(self._chunks)


class DomainSpecificEducationalAgent:
    def __init__(self) -> None:
        self.classifier = DistilBertDomainClassifier()
        self.retriever = KnowledgeRetriever()
        self.client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.confidence_floor = float(os.getenv("DOMAIN_CONFIDENCE_FLOOR", "0.35"))

    def answer(self, question: str) -> str:
        question = question.strip()
        if not question:
            return "Please ask a question related to AI, ML, DL, NLP, RL, or CV."

        domain, confidence, source = self.classifier.classify(question)
        if domain not in SUPPORTED_DOMAINS or confidence < self.confidence_floor:
            return (
                "I only answer questions in AI, ML, DL, NLP, RL, and CV. "
                f"Your question was classified as {domain} with confidence {confidence:.2f}, so I will not answer it."
            )

        retrieved = self.retriever.retrieve(question, domain, top_k=4)
        if not retrieved:
            return (
                f"I classified this as {domain}, but I could not find enough material in the knowledge base to answer safely. "
                "Try rephrasing the question with a more specific topic inside the supported domains."
            )

        context = self._format_context(retrieved)
        if self.client is None:
            return self._offline_answer(question, domain, confidence, source, context)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a domain-specific educational AI agent. Answer only using the provided context. "
                    "If the context does not contain the answer, say so plainly. "
                    "Keep the response educational, structured, and concise. "
                    "Supported domains are AI, ML, DL, NLP, RL, and CV."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Predicted domain: {domain} (confidence {confidence:.2f}, backend {source})\n\n"
                    f"Knowledge base context:\n{context}\n\n"
                    "Write the answer using only the context above."
                ),
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            reply = (response.choices[0].message.content or "").strip()
            if reply:
                return reply
        except Exception:
            pass

        return self._offline_answer(question, domain, confidence, source, context)

    def status(self) -> dict[str, object]:
        return {
            "classifier_backend": self.classifier.backend,
            "classifier_model_dir": str(self.classifier.model_dir),
            "classifier_load_error": self.classifier.load_error,
            "knowledge_base_dir": str(self.retriever.knowledge_base_dir),
            "knowledge_chunks": self.retriever.chunk_count,
            "openai_enabled": self.client is not None,
            "model_name": self.model_name,
        }

    def _offline_answer(self, question: str, domain: str, confidence: float, source: str, context: str) -> str:
        lines = [
            f"Predicted domain: {domain} (confidence {confidence:.2f}, backend {source})",
            "",
            "Retrieved context:",
            context,
            "",
            "Offline answer mode is active because OpenAI is not configured or the call failed.",
            "Use the retrieved material above to ground the response.",
        ]
        return "\n".join(lines)

    def _format_context(self, chunks: list[KnowledgeChunk]) -> str:
        formatted: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            excerpt = chunk.text.strip()
            if len(excerpt) > 1800:
                excerpt = excerpt[:1800] + "..."
            formatted.append(f"[{index}] Domain: {chunk.domain} | Source: {chunk.source}\n{excerpt}")
        return "\n\n".join(formatted)
