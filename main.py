import re
import os
import json
import fitz  # pip install pymupdf


class SAAExamCLI:
    def __init__(self, pdf_path: str, log_file: str = "solved_problems.txt"):
        self.pdf_path = pdf_path
        self.log_file = log_file
        self.pdf_text = self._load_pdf_text()
        self.solved = self.load_solved()
        self.current_q = 170  # 시작 문제번호
        print("📖 로드 완료! 자동 다음문제")

    def _load_pdf_text(self) -> str:
        doc = fitz.open(self.pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text

    def load_solved(self) -> set:
        solved = set()
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ',' in line:
                        parts = line.split(',', 1)
                        solved.add(tuple(parts))
        return solved

    def save_solved(self, q_num: int, user_ans: str):
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"Q{q_num},{user_ans}\n")
        self.solved.add((f"Q{q_num}", user_ans))

    def get_question_only(self, q_num: int) -> str:
        q_pos = self.pdf_text.lower().find(f'q{q_num}')
        if q_pos == -1:
            return "❌ 문제없음"

        section = self.pdf_text[q_pos:]
        ans_pos = re.search(r'Answer[:\s]*[A-Z]', section, re.IGNORECASE)
        if ans_pos:
            return section[:ans_pos.start()].strip()
        return section.strip()

    def get_answer_explain(self, q_num: int) -> str:
        q_pos = self.pdf_text.lower().find(f'q{q_num}')
        if q_pos == -1:
            return "❌ 답안없음"

        section = self.pdf_text[q_pos:]
        ans_start = re.search(r'(?i)(Answer|답안|정답)', section)
        if ans_start:
            ans_section = section[ans_start.start():]
            next_q = re.search(r'Q\d{3}', ans_section, re.IGNORECASE)
            end_pos = next_q.start() if next_q else len(ans_section)
            return ans_section[:end_pos].strip()
        return "❌ 설명없음"

    def next_question(self):
        """다음 문제 자동"""
        self.current_q += 1
        while True:
            if f"Q{self.current_q}," in self.solved:
                self.current_q += 1  # 이미 푼 문제 스킵
            else:
                break

        print(f"\n➡️ 자동 다음: Q{self.current_q}")
        return self.current_q

    def cli_loop(self):
        print("🚀 자동 다음문제 학습기")
        print("번호직접/Enter:다음 / history / quit")
        question_num =0
        while True:
            cmd = input(f"\n📝 Q{self.current_q} (Enter=풀기 / 번호직접): ").strip()

            # 직접 번호
            if cmd.isdigit():
                q_num = int(cmd)
            elif cmd == '' or cmd.lower() == 'next' or cmd =='\r' or cmd =='\n':
                q_num = self.next_question()
            elif cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'history':
                self.show_history()
                continue
            else:
                print("❓ Enter/번호")
                continue

            # 이미 푼 문제
            if f"Q{q_num}," in self.solved:
                print(f"✅ Q{q_num} 이미 풀음. 다음으로!")
                self.current_q = q_num
                q_num = self.next_question()

            # 1. 문제 출력
            question = self.get_question_only(q_num)
            print(f"\n📄 Q{q_num}")
            print(question)
            print("\n" + "=" * 60)

            # 2. 답 입력
            user_ans = input("💭 답: ").strip().upper()
            if user_ans not in 'ABCDE':
                print("❓ A-E")
                continue

            # 3. 기록
            self.save_solved(q_num, user_ans)

            # 4. 정답+설명
            answer_section = self.get_answer_explain(q_num)
            print(f"\n🎯 Answer + 설명")
            print(answer_section)

            # 현재 번호 업데이트
            self.current_q = q_num

    def show_history(self):
        if not os.path.exists(self.log_file):
            print("📝 기록없음")
            return

        count = 0
        print("\n📊 푼 문제 (solved_problems.txt)")
        print("-" * 40)
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    print(line)
                    count += 1
        print(f"총 {count}문제")

# 실행
if __name__ == "__main__":
    import sys

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\nieah\Desktop\01_학습\00_AWS\SAA-C03_Examtopics_V18.35_KOR(aws1602)_unlocked.pdf'
    cli = SAAExamCLI(pdf_path)
    cli.cli_loop()
