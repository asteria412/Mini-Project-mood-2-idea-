# 경로 : app.py

from flask import Flask, render_template, request, redirect, url_for, session
import os

# ✅ STEP 3-B: 저장/읽기 모듈 분리
from core.storage_local import append_record, read_last_n, build_record

app = Flask(__name__)

# ✅ 세션을 쓰기 위해 필요 (개발용 키 / 배포 때는 환경변수로)
app.secret_key = "dev-secret"

# ---------------------------------------------------------
# STEP 3-B. jsonl 저장 경로
# - "실행 위치"에 흔들리지 않게 app.py 기준 절대경로로 고정
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "mood_log.jsonl")


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Mood2Idea 메인 페이지

    ✅ STEP 3-A 핵심 (UX 안정화)
    - GET  : 화면 표시 전용
    - POST : 저장 처리 전용 → 저장 후 Redirect → GET(PRG 패턴)

    이렇게 분리하면:
    - 새로고침 시 '양식 재제출' 경고가 사라짐
    - '저장했는데 왜 사라져?' / '왜 남아있지?' 혼란을 통제할 수 있음

    ✅ STEP 3-B 핵심 (저장 구조 만들기)
    - 기록이 “화면에만” 있는 게 아니라
      data/mood_log.jsonl 파일에 실제로 쌓이기 시작
    """

    # ---------------------------------------------------------
    # [STEP 3-A] 폼 상태 정책 (A/B)
    # - A안: 입력값 유지 (계속 쓰기)
    # - B안: 입력값 초기화 (새 기록)
    # ---------------------------------------------------------
    policy = session.get("form_policy", "B")  # ✅ 기본은 B안(초기화)

    # ---------------------------------------------------------
    # 1) POST : "저장" 처리만 담당
    # ---------------------------------------------------------
    if request.method == "POST":
        # 공통 입력값
        mood_color = request.form.get("mood_color")
        mood_text = request.form.get("mood_text")
        mode = request.form.get("mode")

        # 모드별 추가 입력
        text_content = None
        draw_note = None
        background = request.form.get("background")  # ✅ 템플릿에 이미 있으니 받아줌

        # --- 모드별 입력 분기 ---
        if mode == "write":
            # 글 내용 textarea
            text_content = request.form.get("text_content")

        elif mode == "draw":
            # 그림에 대한 생각/느낌 (선택)
            # ※ 템플릿엔 draw_note가 아직 없으면 None 그대로 저장됨 (문제 없음)
            draw_note = request.form.get("draw_note")
            # image_file 업로드는 STEP4에서 본격 처리 예정

        elif mode == "music":
            # 음악은 다음 단계에서 처리 예정
            pass

        # ---------------------------------------------------------
        # [STEP 3-B] 파일에 진짜 저장하기 (jsonl append)
        # - 스키마: date_time / mood_color / mood_text / mode / ...
        # ---------------------------------------------------------
        record = build_record(
            mood_color=mood_color,
            mood_text=mood_text,
            mode=mode,
            text_content=text_content,
            draw_note=draw_note,
            background=background,
        )
        append_record(DATA_PATH, record)

        # ---------------------------------------------------------
        # [STEP 3-A] 저장 후 폼 상태 정책 적용
        # - 윤서 선택: B안(초기화) 기본
        # - A안 유지가 필요하면 여기서 draft 저장 로직을 추가하면 됨
        # ---------------------------------------------------------
        session["draft"] = {}

        # ---------------------------------------------------------
        # ✅ PRG 패턴 핵심: POST에서 화면 렌더 금지
        # POST → Redirect → GET
        # - 새로고침 경고창 제거
        # - 중복 제출 위험 제거
        # ---------------------------------------------------------
        return redirect(url_for("home", saved="1"))

    # ---------------------------------------------------------
    # 2) GET : 화면 표시 전용
    # ---------------------------------------------------------

    # ✅ 오늘의 기록 표시 규칙
    # - 기본: 최근 1개
    # - 옵션: ?n=5 등으로 확장 가능
    try:
        n = int(request.args.get("n", "1"))
    except ValueError:
        n = 1
    n = max(1, min(n, 30))

    # ---------------------------------------------------------
    # [STEP 3-B] 파일에서 최근 n개 읽어오기
    # - 최신이 위로 오도록 storage_local에서 정렬해서 반환
    # ---------------------------------------------------------
    today_records = read_last_n(DATA_PATH, n=n)

    # ✅ 폼에 채워줄 값 (A안일 때만 draft 유지)
    # (B안이면 무조건 빈 값으로 렌더링)
    draft = session.get("draft", {}) if policy == "A" else {}

    return render_template(
        "index.html",

        # 폼 상태 (draft 기반)
        mood_color=draft.get("mood_color"),
        mood_text=draft.get("mood_text"),
        mode=draft.get("mode"),
        text_content=draft.get("text_content"),
        background=draft.get("background"),

        # 오늘의 기록
        today_records=today_records,
        n=n,

        # UX 플래그
        saved=request.args.get("saved"),
        policy=policy,
    )


@app.post("/policy")
def set_policy():
    """
    [STEP 3-A] 폼 상태 정책 전환
    - A안: 입력 유지
    - B안: 초기화
    """
    policy = (request.form.get("policy") or "B").upper()
    if policy not in ("A", "B"):
        policy = "B"
    session["form_policy"] = policy

    # B안으로 바꾸면 draft도 즉시 비워주는 게 UX상 직관적
    if policy == "B":
        session["draft"] = {}

    return redirect(url_for("home"))


if __name__ == "__main__":
    # debug=True : 수정하면 자동 리로드
    app.run(debug=True)
