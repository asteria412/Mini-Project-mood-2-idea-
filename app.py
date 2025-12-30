from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    """
    Mood2Idea 메인 페이지

    GET  : 초기 화면
    POST : 사용자가 '저장' 버튼을 눌렀을 때
    """

    # --- 기본값 (처음 접속했을 때 or 값 없을 때) ---
    mood_color = None
    mood_text = None
    mode = None

    # 모드별 추가 입력
    text_content = None       # ✍️ 글 모드
    draw_note = None          # 🎨 그림 모드 (느낌/생각)
    # music은 아직 추가 입력 없음

    # --- 저장 버튼 눌렀을 때 ---
    if request.method == "POST":
        # 공통 입력값
        mood_color = request.form.get("mood_color")
        mood_text = request.form.get("mood_text")
        mode = request.form.get("mode")

        # --- 모드별 입력 분기 ---
        if mode == "write":
            # 글 내용 textarea
            text_content = request.form.get("text_content")

        elif mode == "draw":
            # 그림에 대한 생각/느낌 (선택)
            draw_note = request.form.get("draw_note")
            # ※ 파일 업로드는 지금 단계에서는 저장 안 함

        elif mode == "music":
            # 음악은 다음 단계에서 처리 예정
            pass

    # --- template에 모든 상태를 다시 넘겨줌 ---
    # → 그래서 저장 눌러도 화면이 유지됨
    return render_template(
        "index.html",

        # 공통
        mood_color=mood_color,
        mood_text=mood_text,
        mode=mode,

        # 모드별
        text_content=text_content,
        draw_note=draw_note
    )


if __name__ == "__main__":
    # debug=True : 수정하면 자동 리로드
    app.run(debug=True)
