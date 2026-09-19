# Ngày 7 — Bài tập

## Nền tảng Dữ liệu: Embedding & Vector Store | Bài tập thực hành

**Họ tên:** Nguyễn Thái Anh  
**MSSV:** 2A202602810  
**Lớp:** K4-L3A  
**Nhóm:** G51  
**Ngày:** 19/09/2026

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity (Độ tương tự Cosine) bằng ngôn ngữ đời thường

Không yêu cầu toán học — hãy giải thích về mặt khái niệm:

- **Điều gì xảy ra khi hai đoạn văn bản có độ tương tự cosine cao?**

  > Hai vector embedding của chúng chỉ về cùng một hướng trong không gian nhiều chiều ($cos(\theta) \to 1.0$). Điều này thể hiện hai văn bản có sự tương đồng sâu sắc về mặt ngữ nghĩa (semantic meaning) và ngữ cảnh đời sống, dù người viết có thể dùng các từ ngữ hoàn toàn khác nhau để diễn đạt.

- **Đưa ra một ví dụ cụ thể về hai câu sẽ có độ tương tự CAO và hai câu sẽ có độ tương tự THẤP:**
  - _Ví dụ độ tương tự CAO:_
    - Câu A: _"Sinh viên hoàn trả sách trước kỳ nghỉ hè."_
    - Câu B: _"Người học nộp lại giáo trình thư viện trước đợt nghỉ kết thúc năm học."_
    - _Giải thích:_ Hai câu sử dụng các từ đồng nghĩa/paraphrase hoàn toàn khác nhau nhưng cùng mô tả chung một hành vi học vụ.
  - _Ví dụ độ tương tự THẤP:_
    - Câu A: _"Thời hạn mượn giáo trình tại phòng mượn là một học kỳ."_
    - Câu B: _"Hôm nay trời mưa to và căng tin trường bán món bún chả rất ngon."_
    - _Giải thích:_ Thuộc hai miền ngữ cảnh độc lập (nội quy thư viện vs ẩm thực/thời tiết), không có mối liên hệ ngữ nghĩa trong không gian vector.

- **Tại sao độ tương tự cosine lại được ưu tiên hơn khoảng cách Euclid (Euclidean distance) đối với text embeddings?**
  > Độ tương tự cosine đo góc giữa hai vector mà không bị phụ thuộc vào độ lớn (magnitude/độ dài vector). Trong xử lý văn bản, một câu ngắn và một đoạn văn dài diễn đạt cùng một ý nghĩa sẽ có độ dài vector khác nhau; khoảng cách Euclid sẽ đánh giá chúng rất xa nhau, trong khi Cosine similarity vẫn nhận diện chính xác chúng cùng hướng ngữ nghĩa.

> **Ghi kết quả vào:** REPORT_CANHAN.md

---

### Bài tập 1.2 — Bài toán tính toán Chunking

- **Một tài liệu có độ dài 10,000 ký tự. Bạn tiến hành chia nhỏ (chunk) với `chunk_size=500` (kích thước chunk), `overlap=50` (độ chồng chéo). Bạn dự kiến sẽ có bao nhiêu chunks?**
  - _Công thức:_ $\text{số lượng chunk} = \lceil \frac{\text{độ dài} - \text{overlap}}{\text{chunk\_size} - \text{overlap}} \rceil$
  - _Phép tính:_ $\lceil \frac{10000 - 50}{500 - 50} \rceil = \lceil \frac{9950}{450} \rceil = \lceil 22.111... \rceil = \mathbf{23}$ chunks.
  - _Kiểm chứng thực tế:_ `len(FixedSizeChunker(500, 50).chunk('a' * 10000))` = 23 chunks.

- **Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk sẽ thay đổi như thế nào? Tại sao bạn lại muốn tăng độ chồng chéo?**
  - _Khi overlap = 100:_ bước nhảy giảm xuống $500 - 100 = 400$, số chunk tăng lên $\lceil \frac{10000 - 100}{400} \rceil = \lceil 24.75 \rceil = \mathbf{25}$ chunks (tăng thêm 2 chunks).
  - _Lý do tăng overlap:_ Nhằm bảo toàn ngữ cảnh liền mạch (context preservation), ngăn chặn hiện tượng đứt gãy ngữ cảnh (context fragmentation) tại ranh giới cắt, bảo đảm một câu phức hoặc một thực thể ngữ nghĩa quan trọng không bị chia cắt làm hai nửa ở hai chunk khác nhau.

> **Ghi kết quả vào:** REPORT_CANHAN.md

---

## Phần 2 — Lập trình cốt lõi (Cá nhân)

Hoàn thành tất cả các TODOs trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. `Document` dataclass và `FixedSizeChunker` đã được triển khai sẵn làm ví dụ — hãy đọc kỹ để hiểu cấu trúc trước khi lập trình phần còn lại.

Chạy `pytest tests/` để kiểm tra tiến độ.

### Danh sách cần làm (Checklist)

- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [x] `SentenceChunker` — tách dựa trên ranh giới câu, nhóm lại thành các chunks
- [x] `RecursiveChunker` — thử nghiệm các dấu phân cách (separators) theo thứ tự, thực hiện đệ quy trên các đoạn có kích thước quá lớn
- [x] `compute_similarity` — công thức tính độ tương tự cosine kèm cơ chế bảo vệ chia cho 0
- [x] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính toán các chỉ số thống kê
- [x] `EmbeddingStore.__init__` — khởi tạo store (lưu trữ trong bộ nhớ hoặc ChromaDB)
- [x] `EmbeddingStore.add_documents` — nhúng (embed) và lưu trữ từng tài liệu
- [x] `EmbeddingStore.search` — nhúng truy vấn, xếp hạng theo tích vô hướng (dot product)
- [x] `EmbeddingStore.get_collection_size` — trả về số lượng
- [x] `EmbeddingStore.search_with_filter` — lọc theo siêu dữ liệu (metadata), sau đó tìm kiếm
- [x] `EmbeddingStore.delete_document` — xóa tất cả các chunks của một doc_id
- [x] `KnowledgeBaseAgent.answer` — truy xuất (retrieve) + tạo prompt + gọi LLM

> **Nộp code:** thư mục `src/`  
> **Ghi lại hướng tiếp cận vào:** REPORT_CANHAN.md
> **Kết quả test:** 42 / 42 passed in 0.04s.

---

## Phần 3 — So Sánh Chiến Lược Truy Xuất (Nhóm)

### Bài tập 3.0 — Chuẩn Bị Tài Liệu (Giờ đầu tiên)

Mỗi nhóm chọn một chủ đề (domain) và chuẩn bị bộ tài liệu:

**Bước 1 — Chọn chủ đề:** Hệ thống Quy định & Dịch vụ Thông tin Thư viện Đại học (Học viện Công nghệ Bưu chính Viễn thông - PTIT)

**Bước 2 — Thu thập 5-10 tài liệu:** Thu thập 6 tài liệu công khai từ `https://lib.ptit.edu.vn/`, lưu tại `data/university/`.

| #   | Tên tài liệu                                            | Nguồn (Source URL)                                                                                                  | Ngày lấy / Phiên bản    | Số ký tự | Metadata đã gán                                                        |
| --- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------- | -------- | ---------------------------------------------------------------------- |
| 1   | Nội quy thư viện PTIT                                   | https://lib.ptit.edu.vn/noi-quy-thu-vien/                                                                           | 2026-09-19 / not-stated | 3,320    | `audience: all`, `category: regulation`, `department: library`         |
| 2   | Giới thiệu Trung tâm Thông tin Thư viện PTIT            | https://lib.ptit.edu.vn/gioi-thieu/                                                                                 | 2026-09-19 / not-stated | 2,350    | `audience: all`, `category: service`, `department: library`            |
| 3   | Thông báo mượn tài liệu in và số cho sinh viên khóa D19 | https://lib.ptit.edu.vn/thong-bao-ve-viec-muon-tai-lieu-in-va-tai-lieu-so-cho-sinh-vien-khoa-d19-nam-hoc-2019-2020/ | 2026-09-19 / not-stated | 1,420    | `audience: student`, `category: borrowing`, `department: library`      |
| 4   | Thông báo về phục vụ bạn đọc tại thư viện               | https://lib.ptit.edu.vn/thong-bao-ve-phuc-vu-ban-doc-tai-thu-vien-tu-2122022/                                       | 2026-09-19 / not-stated | 1,280    | `audience: all`, `category: service`, `department: library`            |
| 5   | Thông báo thư viện                                      | https://lib.ptit.edu.vn/thong-bao-2/                                                                                | 2026-09-19 / not-stated | 1,310    | `audience: all`, `category: notice`, `department: library`             |
| 6   | Cổng thông tin thư viện OPAC PTIT                       | https://lib.ptit.edu.vn/opac/                                                                                       | 2026-09-19 / not-stated | 1,590    | `audience: student`, `category: search-service`, `department: library` |

**Bước 3 — Thiết kế cấu trúc metadata:**

- `doc_id`: Mã định danh tài liệu
- `title`: Tên tài liệu
- `source_url`: Nguồn gốc xuất xứ
- `retrieved_at`: Ngày thu thập (`2026-09-19`)
- `document_version`: Phiên bản (`not-stated`)
- `audience`: Phân loại đối tượng (`student` / `all`) — _trường cốt lõi để lọc_
- `department`: Đơn vị ban hành (`library`)
- `category`: Danh mục chuyên môn (`regulation`, `borrowing`, `service`, `notice`, `search-service`)
- `language`: Ngôn ngữ (`vi`)

> **Ghi kết quả vào:** REPORT_NHOM.md

---

### Bài tập 3.1 — Thiết Kế Chiến Lược Truy Xuất (Mỗi người thử riêng)

**Bước 1 — Đường cơ sở (Baseline):** Đã chạy `ChunkingStrategyComparator().compare()` trên `library-rules.md`, `student-library-borrowing.md`, `library-introduction.md` (xem chi tiết trong `REPORT_NHOM.md`).

**Bước 2 — Chiến lược tùy chỉnh của tôi (`HeadingSectionChunker`):**

```python
import re
from src.chunking import RecursiveChunker

class HeadingSectionChunker:
    """Tách văn bản quy định theo tiêu đề Markdown và tự động gắn lại tiêu đề vào mảnh con."""
    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self._recursive = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        parts = text.split("---")
        body = "---".join(parts[2:]).strip() if len(parts) >= 3 and parts[0].strip() == "" else text.strip()
        pattern = r'(?m)(?=^#{1,4}\s+)'
        raw_sections = [s.strip() for s in re.split(pattern, body) if s.strip()]
        chunks = []
        for section in raw_sections:
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
            else:
                lines = section.splitlines()
                heading_line = lines[0].strip() if lines and lines[0].startswith("#") else ""
                sub_chunks = self._recursive.chunk(section)
                for sub in sub_chunks:
                    chunks.append(f"{heading_line}\n{sub}" if heading_line and not sub.startswith(heading_line) else sub)
        return chunks
```

**Bước 3 — So sánh:** `HeadingSectionChunker` giữ trọn vẹn ngữ cảnh pháp lý của từng Điều khoản học vụ, khắc phục hiện tượng cắt ngang giữa điều kiện và chế tài của Fixed-size, đồng thời không bị phình to khi gặp danh sách thiếu dấu chấm như SentenceChunker.

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 2 (Thiết kế chiến lược)

---

### Bài tập 3.2 — Chuẩn Bị Câu Hỏi Đánh Giá (Benchmark Queries)

Bộ **5 câu hỏi đánh giá** thống nhất cho cả nhóm G51:

| #            | Câu hỏi (Query)                                                                                       | Câu trả lời chuẩn (Gold Answer)                                                                      | Chunk nào chứa thông tin?                                                     |
| ------------ | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1 _(filter)_ | Mật khẩu mặc định và tên đăng nhập để truy cập hệ thống tài liệu số là gì?                            | Tên đăng nhập là mã sinh viên viết thường (ví dụ: `b17dccn123`), mật khẩu mặc định là `123456`.      | `student-library-borrowing#2` (Mục 2: Hướng dẫn truy cập và mượn tài liệu số) |
| 2            | Mượn tài liệu kho mở về nhà đối với sinh viên và cán bộ giảng viên có thời hạn tối đa bao nhiêu ngày? | Sinh viên được mượn 02 cuốn / 07 ngày; cán bộ, giảng viên được mượn 03 cuốn / 15 ngày.               | `library-rules#9` (Điều 13: Quy định mượn tài liệu kho mở về nhà)             |
| 3            | Thời gian sử dụng máy tính tại phòng truy cập Internet của thư viện được quy định thế nào?            | Mỗi máy tính chỉ 01 người sử dụng, thời gian tối đa là 01 giờ/buổi.                                  | `library-rules#11` (Điều 15: Nội quy phòng truy cập Internet)                 |
| 4            | Giấy tờ bạn đọc cần xuất trình khi đến mượn sách tại phòng mượn là gì?                                | Mang theo Thẻ sinh viên hoặc Căn cước công dân (CMTND) và đọc đúng mã sinh viên được cấp.            | `library-reader-service#3` (Mục 3: Quy định phục vụ tại phòng mượn)           |
| 5            | Phòng Đọc thư viện tạm ngừng phục vụ từ ngày nào để sửa chữa nội thất?                                | Từ ngày 04/07/2022 phòng đọc tạm thời không phục vụ để sửa chữa nội thất; phòng mượn mở bình thường. | `library-notice#0` (Nội dung thông báo)                                       |

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 3 (Câu hỏi đánh giá)

---

### Bài tập 3.3 — Dự Đoán Độ Tương Tự Cosine (Cá nhân)

Thực nghiệm đo `compute_similarity()` với `MockEmbedder` trên 5 cặp câu:

| Cặp | Câu A                                                                       | Câu B                                                                                        | Dự đoán | Điểm thực tế | Đúng?         |
| --- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------- | ------------ | ------------- |
| 1   | Sinh viên được mượn tối đa bao nhiêu cuốn sách tại phòng mượn thư viện?     | Quy định số lượng tài liệu tối đa được mượn về nhà đối với sinh viên chính quy là mấy quyển? | cao     | -0.0177      | Sai (do Mock) |
| 2   | Thời gian phục vụ của thư viện vào buổi chiều bắt đầu từ mấy giờ?           | Giờ mở cửa đón bạn đọc buổi chiều tại thư viện PTIT là lúc nào?                              | cao     | 0.0676       | Đúng          |
| 3   | Địa chỉ truy cập cổng tra cứu trực tuyến OPAC thư viện là gì?               | Học viện Công nghệ Bưu chính Viễn thông có trụ sở chính tại Hoàng Quốc Việt.                 | thấp    | 0.0274       | Đúng          |
| 4   | Hình thức xử lý kỷ luật khi làm mất hoặc hư hỏng tài liệu thư viện là gì?   | Quy định khóa thẻ thư viện và mức bồi thường thiệt hại đối với bạn đọc vi phạm.              | cao     | 0.0791       | Đúng          |
| 5   | Sinh viên sử dụng phòng máy tính Internet thư viện tối đa bao lâu một buổi? | Món bún chả và phở bò tại căng tin trường có giá bao nhiêu tiền một suất?                    | thấp    | 0.2290       | Sai (do Mock) |

**Suy ngẫm:** `MockEmbedder` băm MD5 dựa trên chuỗi byte ký tự ngẫu nhiên nên hai câu đồng nghĩa có thể có score âm (-0.0177), trong khi hai câu khác miền ngữ cảnh lại có score dương cao (0.2290). Trong hệ thống thực tế bắt buộc phải sử dụng các mô hình embedding học sâu (Deep Transformer) để vector nắm bắt được không gian ngữ nghĩa ẩn (semantic latent space).

> **Ghi kết quả vào:** REPORT_CANHAN.md — Phần 4 (Dự đoán độ tương tự)

---

### Bài tập 3.4 — Chạy Đánh Giá & So Sánh Trong Nhóm

**Bước 1:** Đã xây dựng `bench.py` và chạy trên 6 tài liệu với 4 chiến lược. Kết quả được lưu tại `ket_qua_benchmark.txt`.

**Bước 2 — Trả lời 3 câu hỏi so sánh:**

- **Chiến lược nào cho việc truy xuất tốt nhất? Tại sao?**
  > `HeadingSectionChunker` tốt nhất vì bảo toàn trọn vẹn ngữ cảnh điều khoản và gắn lại tiêu đề mục vào từng mảnh con. Ở câu 1, chiến lược này đưa chính xác chunk chứa mật khẩu vào Top-2 và LLM trích xuất được `123456`.
- **Có câu hỏi nào mà chiến lược A tốt hơn B nhưng lại ngược lại ở câu hỏi khác không?**
  > Có. Ở câu 1, `HeadingSectionChunker` đạt Level 2 (trúng nội dung chứa `123456`) trong khi `FixedSizeChunker` và `RecursiveChunker` bị trượt do cắt vỡ câu. Ngược lại, ở câu 5 (thông báo ngắn), `RecursiveChunker` trích xuất nhanh hơn nhờ độ dài chunk linh hoạt.
- **Lọc bằng metadata (Metadata filtering) có giúp ích không?**
  > Rất hữu ích. Thực nghiệm A/B câu 1 chứng minh: khi **không lọc**, các chunk tài liệu chung (`audience: all`) chiếm 2/3 vị trí trong Top-3 (nhầm sang chính sách cán bộ); khi **có lọc `audience: student`**, 100% Top-3 được cô lập chính xác cho sinh viên, giúp Agent trả lời tuyệt đối chính xác.

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 3 & 4

---

### Bài tập 3.5 — Phân Tích Lỗi (Failure Analysis)

**1. Câu hỏi bị hỏng:**

- **Câu 2:** _"Mượn tài liệu kho mở về nhà đối với sinh viên và cán bộ giảng viên có thời hạn tối đa bao nhiêu ngày?"_ (Gold: Điều 13 quy định 02 cuốn / 07 ngày đối với SV, 03 cuốn / 15 ngày đối với CBGV).

**2. Tại sao hỏng?**

- **Đúng tài liệu nhưng sai section:** Cả 3 kết quả Top-3 đều thuộc đúng tài liệu `library-rules.md` (Level 1 đạt), nhưng các section lọt vào Top-3 lại là Section 4 (Khen thưởng & Kỷ luật, khóa thẻ) và Section 1 (Quy định chung Điều 4).
- **Cosine similarity đo chủ đề chung:** Toàn bộ văn bản đều nói về nội quy thư viện, nên độ tương đồng góc không phân biệt được mật độ số liệu trả lời câu hỏi. Kết hợp với hàm băm MD5 ngẫu nhiên của `MockEmbedder`, Điều 13 bị xếp sau các điều khoản khác.

**3. Đề xuất cải thiện:**

- Áp dụng **Hybrid Search** (kết hợp vector dense và từ khóa sparse BM25) để boost các chunk có chứa đồng thời các thực thể số liệu ("ngày", "cuốn", "kho mở", "thời hạn").
- Sử dụng mô hình **Cross-Encoder Re-ranker** ở bước hậu xử lý để chấm điểm lại Top-20 ứng viên trước khi chuyển Top-3 cho LLM.

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 2 & REPORT_CANHAN.md — Phần 5

---

## Danh Sách Kiểm Tra Nộp Bài (Submission Checklist)

- [x] Vượt qua tất cả các bài kiểm thử (tests): `pytest tests/ -v` (42 / 42 passed)
- [x] Cập nhật thư mục `src/` (cá nhân) (`chunking.py`, `store.py`, `agent.py`, `__init__.py`)
- [x] Hoàn thành báo cáo nhóm (`report/REPORT_NHOM.md` — 1 file/nhóm, 40/40 điểm)
- [x] Hoàn thành báo cáo cá nhân (`report/REPORT_CANHAN.md` — 1 file/sinh viên, 60/60 điểm)
