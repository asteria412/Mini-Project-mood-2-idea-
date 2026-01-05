# 경로 : app.py

from flask import Flask, render_template, request, redirect, url_for, session
from core.storage_local import (
    append_record,
    read_last_n,
    build_record,
    save_upload_file,
)

app = Flask(__name__)
app.secret_key = "dev-secret"  # 개발용 / 배포 시 환경변수로 교체

DATA_PATH = "data/mood_log.jsonl"
UPLOAD_DIR = "static/uploads"


# -------------------------------------------------
# 공통: draft(임시 상태) 관리
# -------------------------------------------------

def get_draft():
    """
    step 진행 중인 임시 입력 상태
    - 색 / 한줄 / 모드 / 표현 내용이 누적됨
    """
    return session.get("draft", {})


def update_draft(**kwargs):
    """draft에 값 누적"""
    draft = session.get("draft", {})
    draft.update(kwargs)
    session["draft"] = draft


def clear_draft():
    """최종 저장 후 draft 초기화"""
    session["draft"] = {}


# -------------------------------------------------
# ROOT
# - 접속하면 "기록 보기"가 아니라 "새 기록 시작"으로 보내기
# -------------------------------------------------
@app.route("/")
def root():
    """
    ✅ 윤서 UX 기준:
    - 최초 접속(루트)은 step1로 시작하는 게 자연스럽다.
    - 기록은 별도 페이지(/history)로 분리한다.
    """
    return redirect(url_for("step1"))


# -------------------------------------------------
# STEP 1. 감정 색 선택
# -------------------------------------------------
@app.route("/step/1", methods=["GET", "POST"])
def step1():
    """
    STEP 1
    - 감정 색 선택
    """
    if request.method == "POST":
        mood_color = request.form.get("mood_color")
        if mood_color:
            update_draft(mood_color=mood_color)
            return redirect(url_for("step2"))

    return render_template(
        "index.html",
        step=1,
        draft=get_draft(),
    )


# -------------------------------------------------
# STEP 2. 감정 한 줄
# -------------------------------------------------
@app.route("/step/2", methods=["GET", "POST"])
def step2():
    """
    STEP 2
    - 감정 한 줄 입력
    """
    draft = get_draft()
    if not draft.get("mood_color"):
        # step 건너뛰기 방지
        return redirect(url_for("step1"))

    if request.method == "POST":
        mood_text = request.form.get("mood_text")
        if mood_text:
            update_draft(mood_text=mood_text)
            return redirect(url_for("step3"))

    return render_template(
        "index.html",
        step=2,
        draft=draft,
    )


# -------------------------------------------------
# STEP 3. 표현 방식 선택
# -------------------------------------------------
@app.route("/step/3", methods=["GET", "POST"])
def step3():
    """
    STEP 3
    - 표현 방식 선택 (write / draw / music)
    """
    draft = get_draft()
    if not draft.get("mood_text"):
        return redirect(url_for("step2"))

    if request.method == "POST":
        mode = request.form.get("mode")
        if mode:
            update_draft(mode=mode)
            return redirect(url_for("step4"))

    return render_template(
        "index.html",
        step=3,
        draft=draft,
    )


# -------------------------------------------------
# STEP 4. 표현 입력 + 최종 저장
# -------------------------------------------------
@app.route("/step/4", methods=["GET", "POST"])
def step4():
    """
    STEP 4
    - 글 / 그림 / 음악 입력
    - 최종 저장(jsonl)

    ✅ 음악은 "키워드만 저장"까지 수행
    - 추천/검색/유튜브 연결은 STEP7(LLM)에서 묻어서 진행
    """
    draft = get_draft()
    if not draft.get("mode"):
        return redirect(url_for("step3"))

    if request.method == "POST":
        # 공통 입력
        background = request.form.get("background")

        # 모드별 입력
        text_content = None
        draw_note = None
        image_filename = None
        music_keywords = None

        if draft["mode"] == "write":
            # 글은 비어도 OK
            text_content = request.form.get("text_content")

        elif draft["mode"] == "draw":
            draw_note = request.form.get("draw_note")

            # 파일 업로드 처리 (storage_local에 위임)
            image_file = request.files.get("image_file")
            image_filename = save_upload_file(image_file, UPLOAD_DIR)

        elif draft["mode"] == "music":
            # ✅ 음악: 키워드만 저장 (예: 새벽, 몽환, 로파이, 비 오는 밤…)
            music_keywords = request.form.get("music_keywords")

        # -------------------------------------------------
        # 저장 스키마 생성 (정의는 storage_local에서 담당)
        # -------------------------------------------------
        record = build_record(
            mood_color=draft.get("mood_color"),
            mood_text=draft.get("mood_text"),
            mode=draft.get("mode"),
            text_content=text_content,
            draw_note=draw_note,
            background=background,
            image_filename=image_filename,
            music_keywords=music_keywords,   # ✅ 저장
        )

        append_record(DATA_PATH, record)
        clear_draft()

        # ✅ 저장 후에는 기록 페이지로 이동
        return redirect(url_for("history", saved=1, n=1))

    return render_template(
        "index.html",
        step=4,
        draft=draft,
    )


# -------------------------------------------------
# 기록 보기(히스토리)
# -------------------------------------------------
@app.route("/history")
def history():
    """
    기록 보기 페이지
    - 최근 기록 N개 표시 (?n=1/5/10)
    """
    try:
        n = int(request.args.get("n", "1"))
    except ValueError:
        n = 1
    n = max(1, min(n, 30))

    records = read_last_n(DATA_PATH, n)

    return render_template(
        "index.html",
        step=0,
        records=records,
        n=n,
        saved=request.args.get("saved"),
    )


if __name__ == "__main__":
    app.run(debug=True)
