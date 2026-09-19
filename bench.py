"""
Benchmark script for Lab 7: Embedding & Vector Store.
Implements the 4-step workflow and two-level evaluation from lecture slides:
1. Read .md files, parse YAML frontmatter & content.
2. Chunk content into Document(id=f"{stem}#{i}", content=chunk, metadata={**frontmatter, "doc_id": stem}).
3. Load into EmbeddingStore, run 5 benchmark queries via search_with_filter().
4. Evaluate retrieval at two levels:
   - Level 1: doc_id check (naive)
   - Level 2: gold substring content check (strict)
5. Run A/B testing for metadata_filter vs unfiltered.
6. Generate agent answers and output ket_qua_benchmark.txt.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    HeadingSectionChunker,
    RecursiveChunker,
    SentenceChunker,
)
from src.embeddings import MockEmbedder, OpenAIEmbedder
from src.models import Document
from src.store import EmbeddingStore


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse YAML-like frontmatter between leading --- delimiters."""
    meta: dict[str, str] = {}
    if not text.startswith("---"):
        return meta, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return meta, text

    yaml_block = parts[1]
    body = parts[2].strip()

    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            meta[key] = val

    return meta, body


def load_corpus_documents(
    corpus_dir: str | pathlib.Path,
    chunker: Any,
) -> list[Document]:
    """Load markdown files from corpus_dir, chunk outside store, return list of Document."""
    corpus_path = pathlib.Path(corpus_dir)
    md_files = sorted(corpus_path.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No .md files found in {corpus_dir}")

    all_docs: list[Document] = []
    for file_path in md_files:
        raw_text = file_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw_text)
        stem = file_path.stem

        # Chunk body outside store
        chunks = chunker.chunk(body)
        for i, chunk in enumerate(chunks):
            doc_id = f"{stem}#{i}"
            doc_meta = {**meta, "doc_id": stem, "chunk_index": i}
            all_docs.append(Document(id=doc_id, content=chunk, metadata=doc_meta))

    return all_docs


# 5 Benchmark Queries unified for Group G51
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Mật khẩu mặc định và tên đăng nhập để truy cập hệ thống tài liệu số là gì?",
        "filter": {"audience": "student"},
        "gold_doc_id": "student-library-borrowing",
        "gold_substring": "123456",
        "gold_answer": "Tên đăng nhập là mã sinh viên viết thường, mật khẩu mặc định là 123456.",
        "needs_ab": True,
    },
    {
        "id": 2,
        "query": "Mượn tài liệu kho mở về nhà đối với sinh viên và cán bộ giảng viên có thời hạn tối đa bao nhiêu ngày?",
        "filter": None,
        "gold_doc_id": "library-rules",
        "gold_substring": "02 cuốn / 07 ngày",
        "gold_answer": "Sinh viên được mượn 02 cuốn / 07 ngày; cán bộ, giảng viên được mượn 03 cuốn / 15 ngày.",
        "needs_ab": False,
    },
    {
        "id": 3,
        "query": "Thời gian sử dụng máy tính tại phòng truy cập Internet của thư viện được quy định thế nào?",
        "filter": None,
        "gold_doc_id": "library-rules",
        "gold_substring": "01 giờ/buổi",
        "gold_answer": "Mỗi máy chỉ 01 người sử dụng, thời gian tối đa là 01 giờ/buổi.",
        "needs_ab": False,
    },
    {
        "id": 4,
        "query": "Giấy tờ bạn đọc cần xuất trình khi đến mượn sách tại phòng mượn là gì?",
        "filter": None,
        "gold_doc_id": "library-reader-service",
        "gold_substring": "Thẻ sinh viên",
        "gold_answer": "Mang theo Thẻ sinh viên hoặc CMTND/CCCD và đọc đúng mã sinh viên được cấp.",
        "needs_ab": False,
    },
    {
        "id": 5,
        "query": "Phòng Đọc thư viện tạm ngừng phục vụ từ ngày nào để sửa chữa nội thất?",
        "filter": None,
        "gold_doc_id": "library-notice",
        "gold_substring": "4/7/2022",
        "gold_answer": "Từ ngày 04/07/2022 phòng đọc tạm thời không phục vụ để sửa chữa nội thất.",
        "needs_ab": False,
    },
]


def run_benchmark(
    strategy_name: str = "heading",
    corpus_dir: str = "data/university",
    top_k: int = 3,
) -> tuple[str, dict]:
    """Run retrieval benchmark on the corpus using specified chunking strategy."""
    if strategy_name == "heading":
        chunker = HeadingSectionChunker(max_chunk_size=500)
    elif strategy_name == "fixed":
        chunker = FixedSizeChunker(chunk_size=500, overlap=50)
    elif strategy_name == "sentence":
        chunker = SentenceChunker(max_sentences_per_chunk=3)
    elif strategy_name == "recursive":
        chunker = RecursiveChunker(chunk_size=350)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    embedder = MockEmbedder()
    store = EmbeddingStore(embedding_fn=embedder)

    docs = load_corpus_documents(corpus_dir, chunker)
    store.add_documents(docs)

    lines: list[str] = []
    lines.append("================================================================================")
    lines.append(f"KẾT QUẢ BENCHMARK TRUY XUẤT (Lab 7) — Chiến lược: {strategy_name.upper()}")
    lines.append(f"Số chunk đã nạp vào EmbeddingStore: {len(docs)} chunks")
    lines.append(f"Embedding backend: MockEmbedder (băm MD5)")
    lines.append("================================================================================\n")

    total_points = 0
    level1_matches = 0
    level2_matches = 0

    results_summary = []

    # Setup LLM for KnowledgeBaseAgent
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)

            def llm_fn(prompt: str) -> str:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Bạn là trợ lý RAG của Thư viện PTIT. Hãy trả lời câu hỏi ngắn gọn, trung thực CHỈ dựa trên Context được cung cấp. Nếu trong Context không có đủ thông tin, hãy trả lời rõ là ngữ cảnh không chứa thông tin này."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.0,
                )
                return resp.choices[0].message.content.strip()
        except Exception as e:
            def llm_fn(prompt: str) -> str:
                return f"[Fallback LLM Error: {e}]"
    else:
        def llm_fn(prompt: str) -> str:
            return f"[Mock LLM: Không tìm thấy API Key]"

    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)

    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        qtext = item["query"]
        qfilter = item["filter"]
        gold_doc = item["gold_doc_id"]
        gold_sub = item["gold_substring"]
        gold_ans = item["gold_answer"]

        # Run search_with_filter
        top_results = store.search_with_filter(qtext, metadata_filter=qfilter, top_k=top_k)

        # Check Level 1: doc_id match in top_k
        level1_hit = any(r["metadata"].get("doc_id") == gold_doc for r in top_results)
        if level1_hit:
            level1_matches += 1

        # Check Level 2: gold_substring appears in content
        gold_chunk_rank = -1
        for rank, r in enumerate(top_results, start=1):
            if gold_sub.lower() in r["content"].lower():
                gold_chunk_rank = rank
                break

        level2_hit = gold_chunk_rank != -1
        if level2_hit:
            level2_matches += 1

        # Scoring rubric: 2 points if top-1 and contains answer; 1 point if top-2/3; 0 if missing
        if gold_chunk_rank == 1:
            pts = 2
        elif gold_chunk_rank in (2, 3):
            pts = 1
        else:
            pts = 0
        total_points += pts

        # Generate Agent answer with context
        context_str = "\n\n".join(r["content"] for r in top_results) if top_results else "No relevant context found."
        prompt = f"Context:\n{context_str}\n\nQuestion: {qtext}\n\nAnswer:"
        agent_answer = llm_fn(prompt)

        lines.append(f"--- Câu {qid}: {qtext} ---")
        if qfilter:
            lines.append(f"  [Filter]: {qfilter}")
        lines.append(f"  [Gold Document]: {gold_doc} | [Chuỗi đặc trưng]: '{gold_sub}'")
        lines.append(f"  [Gold Answer]: {gold_ans}")
        lines.append(f"  Top-{top_k} kết quả truy xuất:")

        for rank, r in enumerate(top_results, start=1):
            doc_stem = r["metadata"].get("doc_id", "")
            has_sub = "[CHỨA ĐÁP ÁN]" if gold_sub.lower() in r["content"].lower() else ""
            preview = r["content"].replace("\n", " ")[:90]
            lines.append(f"    {rank}. [Score: {r['score']:+.4f}] ID={r['id']} Doc={doc_stem} {has_sub}")
            lines.append(f"       Trích: \"{preview}...\"")

        lines.append(f"  -> Đánh giá: Level 1 (Doc ID): {'ĐẠT' if level1_hit else 'TRƯỢT'} | Level 2 (Nội dung): {'ĐẠT (Hạng ' + str(gold_chunk_rank) + ')' if level2_hit else 'TRƯỢT'}")
        lines.append(f"  -> Điểm câu này: {pts} / 2 điểm")
        lines.append(f"  -> Agent trả lời: {agent_answer}\n")

        top1_content = top_results[0]["content"] if top_results else ""
        results_summary.append({
            "id": qid,
            "query": qtext,
            "top1_id": top_results[0]["id"] if top_results else "",
            "top1_doc": top_results[0]["metadata"].get("doc_id", "") if top_results else "",
            "top1_score": top_results[0]["score"] if top_results else 0.0,
            "level1_hit": level1_hit,
            "level2_hit": level2_hit,
            "gold_rank": gold_chunk_rank,
            "points": pts,
            "agent_answer": agent_answer,
            "top1_preview": top1_content.replace("\n", " ")[:100],
        })


    # A/B Testing on Query 1 (Filter vs No-Filter)
    lines.append("================================================================================")
    lines.append("THỰC NGHIỆM A/B BẮT BUỘC: SO SÁNH CÓ FILTER VS KHÔNG FILTER (Câu 1)")
    lines.append("================================================================================")
    q1 = BENCHMARK_QUERIES[0]
    res_filtered = store.search_with_filter(q1["query"], metadata_filter=q1["filter"], top_k=top_k)
    res_unfiltered = store.search_with_filter(q1["query"], metadata_filter=None, top_k=top_k)

    lines.append(f"Câu hỏi: \"{q1['query']}\"")
    lines.append(f"\n[A] CÓ FILTER (metadata_filter={q1['filter']}):")
    for rk, r in enumerate(res_filtered, start=1):
        has_sub = "[CHỨA ĐÁP ÁN]" if q1["gold_substring"].lower() in r["content"].lower() else ""
        lines.append(f"  {rk}. Score={r['score']:+.4f} | ID={r['id']} | Audience={r['metadata'].get('audience')} {has_sub}")
        lines.append(f"     \"{r['content'].replace(chr(10), ' ')[:90]}...\"")

    lines.append(f"\n[B] KHÔNG FILTER (toàn bộ corpus):")
    for rk, r in enumerate(res_unfiltered, start=1):
        has_sub = "[CHỨA ĐÁP ÁN]" if q1["gold_substring"].lower() in r["content"].lower() else ""
        lines.append(f"  {rk}. Score={r['score']:+.4f} | ID={r['id']} | Audience={r['metadata'].get('audience')} {has_sub}")
        lines.append(f"     \"{r['content'].replace(chr(10), ' ')[:90]}...\"")

    lines.append("\n[KẾT LUẬN A/B]:")
    if res_filtered[0]["id"] != res_unfiltered[0]["id"] or res_filtered[0]["metadata"].get("audience") != res_unfiltered[0]["metadata"].get("audience"):
        lines.append("  => Kết quả khác biệt rõ rệt! Filter giúp cô lập chính xác đối tượng student, loại bỏ nhiễu.")
    else:
        lines.append("  => Kết quả hai lần trả về cùng tài liệu.")

    lines.append("\n================================================================================")
    lines.append(f"TỔNG KẾT CHIẾN LƯỢC: {strategy_name.upper()}")
    lines.append(f"- Chấm Level 1 (Khớp Doc ID): {level1_matches} / 5 câu")
    lines.append(f"- Chấm Level 2 (Chuỗi đặc trưng chứa đáp án): {level2_matches} / 5 câu")
    lines.append(f"- Tổng điểm đánh giá (Rubric): {total_points} / 10 điểm")
    lines.append("================================================================================\n")

    report_text = "\n".join(lines)
    return report_text, {
        "strategy": strategy_name,
        "chunk_count": len(docs),
        "level1_matches": level1_matches,
        "level2_matches": level2_matches,
        "total_points": total_points,
        "results": results_summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Lab 7 Benchmark Tool")
    parser.add_argument(
        "--strategy",
        choices=["heading", "fixed", "sentence", "recursive", "all"],
        default="heading",
        help="Chunking strategy to benchmark (default: heading)",
    )
    parser.add_argument(
        "--output",
        default="ket_qua_benchmark.txt",
        help="Output file path for benchmark results",
    )
    args = parser.parse_args()

    if args.strategy == "all":
        all_reports = []
        for strat in ["heading", "fixed", "sentence", "recursive"]:
            text, _ = run_benchmark(strat)
            all_reports.append(text)
        full_text = "\n\n".join(all_reports)
    else:
        full_text, _ = run_benchmark(args.strategy)

    print(full_text)
    output_path = pathlib.Path(args.output)
    output_path.write_text(full_text, encoding="utf-8")
    print(f"\n[OK] Đã lưu kết quả benchmark vào: {output_path.resolve()}")


if __name__ == "__main__":
    main()
