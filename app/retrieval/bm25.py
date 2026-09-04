"""In-memory Okapi BM25 index with legal statutory tokenization for IP-SAKTI Sahayak."""

import re
import math
import gzip
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

logger = logging.getLogger("IP-SAKTI.BM25")


def tokenize_legal_text(text: str) -> List[str]:
    """Tokenizes legal text while preserving statutory identifiers (e.g., 2(1)(ja), 3(p), 158B, Article 27)."""
    text_lower = text.lower()
    tokens: List[str] = []

    # 1. Nested subclauses: Section 2(1)(ja), 2(1)(ja), 2(1)(j), (1)(ja), (ja)
    nested_matches = re.findall(r"(?:section\s*)?(\d+)\s*\(([0-9]+)\)\s*\(([a-z0-9]+)\)", text_lower)
    for sec, sub1, sub2 in nested_matches:
        tokens.append(f"section {sec}({sub1})({sub2})")
        tokens.append(f"{sec}({sub1})({sub2})")
        tokens.append(f"section {sec}({sub1})")
        tokens.append(f"{sec}({sub1})")
        tokens.append(f"({sub2})")
        tokens.append(sub2)

    # 2. Statutory clause patterns: Section 3(p), 3(p), (p)
    clause_matches = re.findall(r"(?:section\s*)?(\d+)\s*\(([a-z0-9]+)\)", text_lower)
    for sec, clause in clause_matches:
        tokens.append(f"section {sec}({clause})")
        tokens.append(f"{sec}({clause})")
        tokens.append(f"section {sec}")
        tokens.append(f"({clause})")
        tokens.append(clause)

    # 3. Treaty Articles: Article 6, Article 27, Art. 6
    art_matches = re.findall(r"(?:article|art\.?)\s*(\d+[a-z]?)", text_lower)
    for art_num in art_matches:
        tokens.append(f"article {art_num}")
        tokens.append(f"article{art_num}")
        tokens.append(f"art {art_num}")

    # 4. Capture rule sub-parts: Rule 158B, 158-B, 158b
    rule_matches = re.findall(r"(?:rule\s*)?(\d+)\s*[-_ ]\s*([a-z0-9]+)", text_lower)
    for r_num, r_sub in rule_matches:
        tokens.append(f"rule {r_num}{r_sub}")
        tokens.append(f"{r_num}{r_sub}")
        tokens.append(f"{r_num}-{r_sub}")

    # 5. Capture hyphenated section numbers: 33-EEC, 33EEC
    hyphen_matches = re.findall(r"\b(\d+)\s*[-_]\s*([a-z]+)\b", text_lower)
    for h_num, h_sub in hyphen_matches:
        tokens.append(f"{h_num}{h_sub}")
        tokens.append(f"{h_num}-{h_sub}")

    # 6. Standard word tokenization (alphanumeric sequences >= 2 chars)
    cleaned = re.sub(r"[^\w\s\(\)]", " ", text_lower)
    words = cleaned.split()
    for w in words:
        if len(w) >= 2 or w in {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p"}:
            tokens.append(w)

    return tokens


class BM25Index:
    """Okapi BM25 Index with standard parameters (k1=1.5, b=0.75) partitioned by jurisdiction."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        self.docs_by_jurisdiction: Dict[str, List[Dict[str, Any]]] = {
            "national": [],
            "international": [],
        }
        self.df_by_jurisdiction: Dict[str, Dict[str, int]] = {
            "national": {},
            "international": {},
        }
        self.avg_dl_by_jurisdiction: Dict[str, float] = {
            "national": 0.0,
            "international": 0.0,
        }
        self.total_docs_by_jurisdiction: Dict[str, int] = {
            "national": 0,
            "international": 0,
        }

    def build_from_qdrant_points(self, points: List[Any]) -> None:
        """Indexes document points directly from Qdrant scroll results."""
        self.docs_by_jurisdiction = {"national": [], "international": []}
        self.df_by_jurisdiction = {"national": {}, "international": {}}

        for pt in points:
            payload = pt.payload if hasattr(pt, "payload") else pt.get("payload", {})
            pt_id = pt.id if hasattr(pt, "id") else pt.get("id")
            jurisdiction = str(payload.get("jurisdiction", "national")).lower()
            if jurisdiction not in self.docs_by_jurisdiction:
                self.docs_by_jurisdiction[jurisdiction] = []
                self.df_by_jurisdiction[jurisdiction] = {}

            searchable_text = (
                f"{payload.get('title', '')} {payload.get('citation_prefix', '')} "
                f"{payload.get('section', '')} {payload.get('text', '')}"
            )
            tokens = tokenize_legal_text(searchable_text)
            doc_len = len(tokens)

            doc_entry = {
                "id": str(pt_id),
                "payload": payload,
                "tokens": tokens,
                "tf": Counter(tokens),
                "doc_len": doc_len,
            }
            self.docs_by_jurisdiction[jurisdiction].append(doc_entry)

        for j, doc_list in self.docs_by_jurisdiction.items():
            n_docs = len(doc_list)
            self.total_docs_by_jurisdiction[j] = n_docs
            if n_docs == 0:
                self.avg_dl_by_jurisdiction[j] = 0.0
                continue

            total_len = sum(d["doc_len"] for d in doc_list)
            self.avg_dl_by_jurisdiction[j] = total_len / n_docs

            df = Counter()
            for d in doc_list:
                df.update(set(d["tokens"]))
            self.df_by_jurisdiction[j] = dict(df)

    def search(
        self,
        query: str,
        jurisdiction: str = "national",
        top_k: int = 30,
    ) -> List[Dict[str, Any]]:
        """Performs BM25 search over the specified jurisdiction."""
        j_key = jurisdiction.lower()
        doc_list = self.docs_by_jurisdiction.get(j_key, [])
        n_docs = self.total_docs_by_jurisdiction.get(j_key, 0)
        avg_dl = self.avg_dl_by_jurisdiction.get(j_key, 0.0)
        df_dict = self.df_by_jurisdiction.get(j_key, {})

        if not doc_list or n_docs == 0 or avg_dl == 0.0:
            return []

        query_tokens = tokenize_legal_text(query)
        if not query_tokens:
            return []

        q_term_idfs: Dict[str, float] = {}
        for term in set(query_tokens):
            df = df_dict.get(term, 0)
            if df > 0:
                idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                q_term_idfs[term] = max(idf, 0.001)

        if not q_term_idfs:
            return []

        scores: List[Tuple[float, Dict[str, Any]]] = []
        for doc in doc_list:
            doc_len = doc["doc_len"]
            doc_tf = doc["tf"]
            score = 0.0

            len_norm = 1.0 - self.b + self.b * (doc_len / avg_dl)

            for term, idf in q_term_idfs.items():
                tf = doc_tf.get(term, 0)
                if tf > 0:
                    term_score = idf * (tf * (self.k1 + 1.0)) / (tf + self.k1 * len_norm)
                    score += term_score

            if score > 0.0:
                scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_hits = scores[:top_k]

        results: List[Dict[str, Any]] = []
        for rank, (score, doc) in enumerate(top_hits, start=1):
            res_item = dict(doc["payload"])
            res_item["id"] = doc["id"]
            res_item["bm25_rank"] = rank
            res_item["bm25_score"] = float(score)
            results.append(res_item)

        return results

    def save_to_disk(self, file_path: str | Path) -> None:
        """Serializes the current BM25 index to a gzip-compressed pickle file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "k1": self.k1,
            "b": self.b,
            "docs_by_jurisdiction": self.docs_by_jurisdiction,
            "df_by_jurisdiction": self.df_by_jurisdiction,
            "avg_dl_by_jurisdiction": self.avg_dl_by_jurisdiction,
            "total_docs_by_jurisdiction": self.total_docs_by_jurisdiction,
        }
        temp_path = path.with_suffix(".tmp")
        try:
            with gzip.open(temp_path, "wb") as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
            if path.exists():
                path.unlink()
            temp_path.rename(path)
            logger.info(f"Successfully saved compressed BM25 index to {path}")
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            logger.error(f"Failed to save BM25 cache to {path}: {e}")
            raise

    @classmethod
    def load_from_disk(cls, file_path: str | Path) -> "BM25Index":
        """Loads a serialized BM25 index from a gzip-compressed pickle file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"BM25 cache file not found at {path}")
        with gzip.open(path, "rb") as f:
            state = pickle.load(f)
        index = cls(k1=state.get("k1", 1.5), b=state.get("b", 0.75))
        index.docs_by_jurisdiction = state.get("docs_by_jurisdiction", {"national": [], "international": []})
        index.df_by_jurisdiction = state.get("df_by_jurisdiction", {"national": {}, "international": {}})
        index.avg_dl_by_jurisdiction = state.get("avg_dl_by_jurisdiction", {"national": 0.0, "international": 0.0})
        index.total_docs_by_jurisdiction = state.get("total_docs_by_jurisdiction", {"national": 0, "international": 0})
        logger.info(f"Successfully loaded compressed BM25 index from {path} ({sum(index.total_docs_by_jurisdiction.values())} docs)")
        return index
