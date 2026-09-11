import os
import re
from typing import List, Dict, Any, Optional
import requests
from app.core.config import settings

class AnswerGenerator:
    """Generates answers from retrieved context via LLM API or grounded extractive synthesis."""

    def __init__(self):
        pass

    def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        provider: Optional[str] = None,
        custom_key: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        provider = provider or settings.LLM_PROVIDER
        api_key = custom_key or settings.GEMINI_API_KEY or settings.OPENAI_API_KEY

        if not retrieved_chunks:
            return "I could not find any relevant context in the uploaded documents to answer your question."

        context_text = "\n\n".join([
            f"[Source: {c.get('filename', 'Doc')} (Page {c.get('page_number', 1)})]\n{c.get('content', '')}"
            for c in retrieved_chunks
        ])

        # 1. Try Gemini if configured
        if provider == "gemini" or (api_key and "AIza" in api_key):
            gemini_ans = self._call_gemini(question, context_text, api_key or settings.GEMINI_API_KEY, temperature)
            if gemini_ans:
                return gemini_ans

        # 2. Try OpenAI if configured
        if provider == "openai" or (api_key and api_key.startswith("sk-")):
            openai_ans = self._call_openai(question, context_text, api_key or settings.OPENAI_API_KEY, temperature)
            if openai_ans:
                return openai_ans

        # 3. Built-in Extractive-Grounded RAG synthesis engine
        return self._extractive_synthesis(question, retrieved_chunks)

    def _call_gemini(self, question: str, context: str, api_key: str, temperature: float) -> Optional[str]:
        if not api_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            "You are a helpful and strictly grounded RAG assistant. Answer the user's question using ONLY "
            "the provided context below. If the answer cannot be found in the context, explicitly state "
            "that the context does not contain enough information. Do not hallucinate or use external knowledge.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": 800}
            }
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[Generator] Gemini API error: {e}")
        return None

    def _call_openai(self, question: str, context: str, api_key: str, temperature: float) -> Optional[str]:
        if not api_key:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        messages = [
            {
                "role": "system",
                "content": "You are a strictly grounded assistant. Answer using ONLY the provided context. Do not speculate."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-3.5-turbo", "messages": messages, "temperature": temperature}
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[Generator] OpenAI API error: {e}")
        return None

    def _extractive_synthesis(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """High-precision grounded synthesis by identifying most salient context sentences."""
        question_words = set(re.findall(r'\w+', question.lower())) - {
            "what", "is", "are", "who", "when", "where", "why", "how", "the", "a", "an", "of", "in", "to", "for", "and", "does", "do", "did"
        }

        all_sentences = []
        for ch in chunks:
            content = ch.get("content", "")
            # split into sentences
            raw_sents = re.split(r'(?<=[.!?])\s+', content)
            for s in raw_sents:
                clean_s = s.strip()
                if len(clean_s) > 15:
                    all_sentences.append(clean_s)

        if not all_sentences:
            return "The retrieved documents do not provide clear information to address this query."

        # Score sentences by keyword intersection and proximity
        scored_sents = []
        for s in all_sentences:
            s_lower = s.lower()
            s_words = set(re.findall(r'\w+', s_lower))
            overlap = len(question_words.intersection(s_words))
            scored_sents.append((overlap, len(s), s))

        # Sort by overlap descending, then by length
        scored_sents.sort(key=lambda x: (x[0], -x[1]), reverse=True)

        selected = []
        seen = set()
        for overlap, length, s in scored_sents:
            if overlap > 0 and s not in seen:
                selected.append(s)
                seen.add(s)
            if len(selected) >= 3:
                break

        # Fallback to top sentence of highest ranked chunk
        if not selected:
            selected = [all_sentences[0]]

        return " ".join(selected)

generator = AnswerGenerator()
