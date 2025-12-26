import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
from typing import List, Tuple

class FallbackRetriever:
    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]
        csv_path = project_root / "data" / "agriculture_qna_expanded.csv"
        if not csv_path.exists():
            self.df = pd.DataFrame({"question": [], "answer": [], "source": []})
            self.vectorizer = TfidfVectorizer(stop_words='english')
            self.matrix = self.vectorizer.fit_transform(["placeholder question"])
            return
        self.df = pd.read_csv(csv_path)
        if 'question' not in self.df.columns or 'answer' not in self.df.columns:
            raise ValueError("Dataset must have 'question' and 'answer' columns")
        if 'source' not in self.df.columns:
            self.df['source'] = 'csv:agriculture_qna_expanded'
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.matrix = self.vectorizer.fit_transform(self.df['question'].astype(str))

    def search(self, query: str, k: int = 8) -> List[Tuple[str, float, str]]:
        if not query:
            return []
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.matrix).flatten()
        top_idx = similarities.argsort()[::-1][:k]
        results: List[Tuple[str, float, str]] = []
        for idx in top_idx:
            score = float(similarities[idx])
            chunk = str(self.df.loc[idx, 'answer'])
            source = str(self.df.loc[idx, 'source'])
            results.append((chunk, score, source))
        return results


