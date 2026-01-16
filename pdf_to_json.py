import re
import json
import fitz  # pip install pymupdf
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List


@dataclass
class ParsedQA:
    q_num: int
    question: str
    answer_block: str
    answer_choice: Optional[str]


class SAAExamParser:
    Q_HEADER_RE = re.compile(r'(?im)^\s*(Q(?P<num>\d{1,4}))\b')
    ANSWER_START_RE = re.compile(r'(?im)^\s*(Answer|답안|정답)\b\s*[:：]?\s*')
    ANSWER_CHOICE_RE = re.compile(r'(?im)\bAnswer\b\s*[:：]?\s*([A-E])\b')

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.full_text = self._load_pdf_text()

    def _load_pdf_text(self) -> str:
        # page.get_text("text")로 모든 페이지 텍스트를 추출해 합칩니다. [web:1]
        doc = fitz.open(self.pdf_path)
        try:
            parts: List[str] = []
            for page in doc:
                parts.append(page.get_text("text"))
            return "\n".join(parts)
        finally:
            doc.close()

    def parse_all(self) -> Dict[int, ParsedQA]:
        spans = self._split_into_question_spans(self.full_text)
        out: Dict[int, ParsedQA] = {}
        for q_num, raw_section in spans.items():
            out[q_num] = self._parse_one_section(q_num, raw_section)
        return out

    def _split_into_question_spans(self, text: str) -> Dict[int, str]:
        matches = list(self.Q_HEADER_RE.finditer(text))
        spans: Dict[int, str] = {}
        for i, m in enumerate(matches):
            q_num = int(m.group("num"))
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            spans[q_num] = text[start:end].strip()
        return spans

    def _parse_one_section(self, q_num: int, section: str) -> ParsedQA:
        ans_m = self.ANSWER_START_RE.search(section)
        if ans_m:
            question_part = section[:ans_m.start()].strip()
            answer_part = section[ans_m.start():].strip()
        else:
            question_part = section.strip()
            answer_part = ""

        question_part = re.sub(rf'(?im)^\s*Q{q_num}\b\s*', '', question_part, count=1).strip()

        choice_m = self.ANSWER_CHOICE_RE.search(answer_part)
        answer_choice = choice_m.group(1) if choice_m else None

        return ParsedQA(
            q_num=q_num,
            question=question_part,
            answer_block=answer_part,
            answer_choice=answer_choice
        )

    def export_json(self, out_path: str) -> Dict[int, ParsedQA]:
        data = self.parse_all()

        # JSON 키는 문자열이 호환성이 좋아서 str(q_num)로 저장 권장
        payload = {str(k): asdict(v) for k, v in data.items()}

        # 한글/UTF-8 깨짐 방지를 위해 ensure_ascii=False + encoding="utf-8" 사용 [web:20][web:23]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return data


if __name__ == "__main__":
    import sys

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\nieah\Desktop\01_학습\00_AWS\SAA-C03_Examtopics_V18.35_KOR(aws1602)_unlocked.pdf'
    out_path = sys.argv[2] if len(sys.argv) > 2 else "parsed_qa.json"

    parser = SAAExamParser(pdf_path)
    parser.export_json(out_path)

    print(f"OK: {out_path} 저장 완료")
