from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|(?<=\.)\n+', text.strip()) if s.strip()]
        if not sentences:
            return []
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_str = " ".join(group).strip()
            if chunk_str:
                chunks.append(chunk_str)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        if sep == "":
            splits = list(current_text)
        else:
            splits = current_text.split(sep)

        # Recursively split any piece that exceeds chunk_size
        sub_pieces: list[str] = []
        for piece in splits:
            if not piece:
                continue
            if len(piece) > self.chunk_size:
                sub_pieces.extend(self._split(piece, next_seps))
            else:
                sub_pieces.append(piece)

        # Merge adjacent pieces back together up to chunk_size
        merged: list[str] = []
        current_chunk = ""
        join_sep = sep if sep != "" else ""

        for piece in sub_pieces:
            if not current_chunk:
                current_chunk = piece
            elif len(current_chunk) + len(join_sep) + len(piece) <= self.chunk_size:
                current_chunk = current_chunk + join_sep + piece
            else:
                merged.append(current_chunk)
                current_chunk = piece

        if current_chunk:
            merged.append(current_chunk)

        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    similarity = _dot(vec_a, vec_b) / (norm_a * norm_b)
    return max(-1.0, min(1.0, float(similarity)))


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=20).chunk(text)
        sentences = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        strategies = {
            "fixed_size": fixed,
            "by_sentences": sentences,
            "recursive": recursive,
        }

        result = {}
        for name, chunks in strategies.items():
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            result[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return result


class HeadingSectionChunker:
    """
    Split document by Markdown headings (e.g., #, ##, ###).
    If a section exceeds max_chunk_size, fall back to recursive splitting
    and re-attach the section heading to each sub-chunk so context is preserved.
    """

    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self._recursive = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Strip YAML frontmatter if present
        parts = text.split("---")
        body = "---".join(parts[2:]).strip() if len(parts) >= 3 and parts[0].strip() == "" else text.strip()

        # Split on Markdown headings (#, ##, ###, ####)
        pattern = r"(?m)(?=^#{1,4}\s+)"
        raw_sections = [s.strip() for s in re.split(pattern, body) if s.strip()]
        if not raw_sections:
            raw_sections = [body]

        chunks: list[str] = []
        for section in raw_sections:
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
            else:
                lines = section.splitlines()
                heading_line = lines[0].strip() if lines and lines[0].startswith("#") else ""

                sub_chunks = self._recursive.chunk(section)
                for sub in sub_chunks:
                    if heading_line and not sub.startswith(heading_line):
                        chunks.append(f"{heading_line}\n{sub}")
                    else:
                        chunks.append(sub)
        return chunks

