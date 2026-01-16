let QA = null;
let qNumsSorted = [];
let currentIndex = -1;
let solved = {};

const $ = (id) => document.getElementById(id);

function loadSolved() {
  try {
    solved = JSON.parse(localStorage.getItem("saa_solved") || "{}");
  } catch {
    solved = {};
  }
}

function saveSolved() {
  localStorage.setItem("saa_solved", JSON.stringify(solved));
}

function loadQAFromGlobal() {
  // data/parsed_qa.js에서 window.__QA__ 로 주입됨 [web:68]
  QA = window.__QA__;
  if (!QA || typeof QA !== "object") {
    throw new Error("QA 데이터 없음: data/parsed_qa.js 로드/생성 확인");
  }

  qNumsSorted = Object.keys(QA)
    .map((k) => Number(QA[k]?.q_num ?? k))
    .filter((n) => Number.isFinite(n))
    .sort((a, b) => a - b);
}

function findKeyByQNum(qNum) {
  // JSON key가 "1","2"... 이고 내부 q_num이 동일하다고 가정하지만,
  // 혹시 key와 q_num이 다를 수 있어 안전하게 탐색.
  const direct = String(qNum);
  if (QA[direct] && Number(QA[direct].q_num) === qNum) return direct;

  const keys = Object.keys(QA);
  for (const k of keys) {
    if (Number(QA[k]?.q_num) === qNum) return k;
  }
  return null;
}

function render() {
  const qNum = qNumsSorted[currentIndex];
  const key = findKeyByQNum(qNum);
  const item = key ? QA[key] : null;

  $("qNo").textContent = `Q${qNum}`;
  $("progress").textContent = `${currentIndex + 1} / ${qNumsSorted.length}`;
  $("question").textContent = item?.question || "(문제 없음)";

  $("result").textContent = solved[qNum] ? `내 답: ${solved[qNum]}` : "";
  $("result").className = "result";

  $("explainWrap").classList.add("hidden");
  $("answerBlock").textContent = "";

  $("btnPrev").disabled = currentIndex <= 0;
  $("btnNext").disabled = currentIndex >= qNumsSorted.length - 1;
  $("btnReveal").disabled = false;

  $("userAnswer").value = "";
  $("userAnswer").focus();
  $("btnNextAfterExplain").disabled = (currentIndex >= qNumsSorted.length - 1);

}

function normalizeChoice(s) {
  const t = (s || "").trim().toUpperCase();
  return t ? t[0] : "";
}

function getCorrectChoice(item) {
  if (item?.answer_choice) return normalizeChoice(item.answer_choice);

  const m = (item?.answer_block || "").match(/\bAnswer\b\s*[:：]?\s*([A-E])\b/i);
  return m ? normalizeChoice(m[1]) : "";
}

function showExplain() {
  const qNum = qNumsSorted[currentIndex];
  const key = findKeyByQNum(qNum);
  const item = key ? QA[key] : null;

  $("answerBlock").textContent = item?.answer_block || "(정답/설명 없음)";
  $("explainWrap").classList.remove("hidden");
  if (currentIndex < qNumsSorted.length - 1) {
    $("btnNextAfterExplain").disabled = false;
  }
}

function grade() {
  const qNum = qNumsSorted[currentIndex];
  const key = findKeyByQNum(qNum);
  const item = key ? QA[key] : null;

  const user = normalizeChoice($("userAnswer").value);
  if (!"ABCDE".includes(user)) {
    $("result").textContent = "A~E로 입력";
    $("result").className = "result bad";
    return;
  }

  solved[qNum] = user;
  saveSolved();

  const correct = getCorrectChoice(item);
  if (!correct) {
    $("result").textContent = `저장됨(정답 추출 실패). 내 답: ${user}`;
    $("result").className = "result";
    return;
  }

  if (user === correct) {
    $("result").textContent = `정답! (${user})`;
    $("result").className = "result ok";
  } else {
    $("result").textContent = `오답. 내 답: ${user} / 정답: ${correct}`;
    $("result").className = "result bad";
  }
}

function goToQNum(qNum) {
  const idx = qNumsSorted.indexOf(qNum);
  if (idx === -1) {
    $("question").textContent = `Q${qNum} 없음. (범위: ${qNumsSorted[0]} ~ ${qNumsSorted[qNumsSorted.length - 1]})`;
    return;
  }
  currentIndex = idx;

  $("btnPrev").disabled = false;
  $("btnNext").disabled = false;
  $("btnReveal").disabled = false;
  $("userAnswer").disabled = false;
  $("btnSubmit").disabled = false;

  render();
}

function next() {
  if (currentIndex < qNumsSorted.length - 1) {
    currentIndex += 1;
    render();
  }
}

function prev() {
  if (currentIndex > 0) {
    currentIndex -= 1;
    render();
  }
}

window.addEventListener("DOMContentLoaded", () => {
  loadSolved();
  $("btnNextAfterExplain").disabled = true;
  try {
    loadQAFromGlobal();
  } catch (e) {
    $("question").textContent = `데이터 로드 실패: ${e.message}`;
    return;
  }

  $("btnStart").addEventListener("click", () => {
    const q = Number($("startNumber").value);
    if (!Number.isFinite(q)) return;
    goToQNum(q);
  });

  $("btnNext").addEventListener("click", next);
  $("btnPrev").addEventListener("click", prev);
  $("btnReveal").addEventListener("click", showExplain);
  $("btnSubmit").addEventListener("click", grade);

  $("userAnswer").addEventListener("keydown", (e) => {
    if (e.key === "Enter") grade();
  });

  // URL hash 지원 (#170)
  const hash = (location.hash || "").replace("#", "").trim();
  if (/^\d+$/.test(hash)) {
    $("startNumber").value = hash;
    $("btnStart").click();
  }
  $("btnNextAfterExplain").addEventListener("click", () => {
    next(); // 기존 next() 재사용
  });
});
