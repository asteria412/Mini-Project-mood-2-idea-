import streamlit as st

st.set_page_config(page_title="Mood2Idea", layout="centered")

# [KEEP] 감정/색상 맵 (너가 확정한 버전)
EMOTION_COLORS = {
    "설렘 (핑크)": "#EC407A",
    "즐거움 (초록)": "#4CAF50",
    "평온 (민트)": "#00BCD4",
    "외로움 (보라)": "#9C27B0",
    "서운함 (자주색)": "#8E24AA",
    "우울 (파랑)": "#2196F3",
    "지침 (네이비)": "#1A237E",
    "불안 (노랑)": "#FBC02D",
    "초조함 (오렌지)": "#FB8C00",
    "서러움 (주황)": "#FF9800",
    "분노 (빨강)": "#F44336",
    "답답함 (와인)": "#B71C1C",
    "혼란 (검정)": "#000000",
}

st.title("🌱 Mood 2 Idea")
st.write("오늘의 감정을 색으로 남겨보세요.")

if "show_tutorial" not in st.session_state:
    st.session_state.show_tutorial = True

with st.sidebar:
    st.markdown("## 🌙 Mood 2 Idea")
    st.caption("필요할 때 언제든 다시 켤 수 있어요.")

    # [NEW] 토글 하나로 열고/닫기 (버튼 2개 제거)
    st.session_state.show_tutorial = st.toggle(
        "📖 How To Use",
        value=st.session_state.show_tutorial
    )

    # [NEW] 토글이 켜져 있을 때만 내용 표시
    if st.session_state.show_tutorial:
        st.markdown("""
### Mood 2 Idea는 ‘감정의 변화’를 관찰하는 기록 앱이에요.

**1) 기준점 만들기**
- 오늘 감정을 **색**으로 선택해요.
- 감정을 **한 줄**로 남겨요.

**2) 3-way 표현**
- ✍️ 글로 쓰거나,  
- 🎨 그림으로 남기거나,  
- 🎵 음악으로 대표해요.

**3) AI의 도움은 선택 사항**
- **혼자 계속 표현**해도 되고,
- 원하면 **AI와 대화** 하거나,
- 결과물을 **AI와 발전**시킬 수 있어요.

**4) 색의 변화 관찰**
- 글/그림/음악 활동을 하거나,  
- AI 기능을 사용할수록  
👉 오늘의 색이 **점점 옅어져요.**  
(감정을 평가하는 것이 아닌, **활동에 따른 변화 과정**을 보여주는 장치에요.)

**5) 최종 색(감정)은 내가 결정**
- 마지막에 오늘의 감정을 **정리할지/그대로 둘지**  
✅ 최종 색 결정은 **사용자 본인**이 해요.

**6) 달력에 저장**
- 오늘의 최종 색이 **달력에 점으로 기록**되어  
나중에 한 달/몇 달의 감정 흐름을 **색으로** 볼 수 있어요.
        """)

# [KEEP] step 초기화
if "step" not in st.session_state:
    st.session_state.step = "select_color"

# -----------------------------
# STEP A) 감정 색 선택
# -----------------------------
if st.session_state.step == "select_color":
    st.subheader("오늘의 기분은 무슨 색인가요?")

    selected_emotion = st.selectbox(
        "감정/색상 선택",
        options=list(EMOTION_COLORS.keys()),
        index=None,
        placeholder="색을 골라주세요"
    )

    if selected_emotion:
        selected_color = EMOTION_COLORS[selected_emotion]

        # [KEEP] 컬러칩 미리보기
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:18px;height:18px;border-radius:50%;background:{selected_color};"></div>
                <div>{selected_emotion} · {selected_color}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("이 색으로 기록 시작하기 ✅", use_container_width=True):
                # [KEEP] 선택값을 session_state에 저장
                st.session_state.base_emotion = selected_emotion
                st.session_state.base_color = selected_color
                st.session_state.current_color = selected_color

                # [NEW] 다음 단계로 이동
                st.session_state.step = "input_phrase"
                st.rerun()

        with col2:
            if st.button("초기화", use_container_width=True):
                for k in ["base_emotion", "base_color", "current_color", "phrase"]:
                    st.session_state.pop(k, None)
                st.rerun()
    else:
        st.info("색을 고르면 다음 단계로 넘어갈 수 있어요.")

# -----------------------------
# STEP B) 감정 한 줄 입력  ✅ (이번에 추가된 단계)
# -----------------------------
elif st.session_state.step == "input_phrase":
    st.subheader("오늘의 감정을 한 줄로 남겨주세요")

    # [ADD] 뒤로가기(색 다시 고르기)
    if st.button("← 색 다시 고르기"):
        st.session_state.step = "select_color"
        st.rerun()

    # [KEEP] 선택한 색/감정 보여주기 (맥락 유지)
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin-top:10px;">
            <div style="width:18px;height:18px;border-radius:50%;background:{st.session_state.base_color};"></div>
            <div><b>{st.session_state.base_emotion}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # [NEW] 한 줄 입력 UI
    phrase = st.text_input(
        "감정 한 줄",
        value=st.session_state.get("phrase", ""),
        placeholder="예: 오늘은 마음이 자꾸 가라앉는다."
    )

    # [NEW] 입력값을 즉시 세션에 저장 (새로고침/이동해도 유지)
    st.session_state.phrase = phrase

    # [ADD] 다음 단계로 갈 수 있는 조건(빈 값 방지)
    can_go_next = bool(phrase.strip())

    # [NEW] 다음 단계 버튼 (지금은 다음 단계 껍데기만 이동)
    if st.button("다음 단계로 (표현 방식 선택) ➜", disabled=not can_go_next):
        st.session_state.step = "choose_mode"   # [NEW] 다음 step 이름만 미리 만들어둠
        st.rerun()

    if not can_go_next:
        st.info("한 줄만 적어주면 다음으로 넘어갈 수 있어요 🙂")

# -----------------------------
# STEP C) 표현 방식 선택 (3-way)  ✅ 이번 STEP 핵심
# -----------------------------
elif st.session_state.step == "choose_mode":
    st.subheader("이 감정을 어떻게 표현해볼까요?")

    # [ADD] 뒤로가기 (한 줄 입력으로)
    if st.button("← 감정 한 줄로 돌아가기"):
        st.session_state.step = "input_phrase"
        st.rerun()

    st.write("")

    # [NEW] 3-way 버튼 배치
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✍️ 글로 표현", use_container_width=True):
            st.session_state.mode = "write"
            st.session_state.step = "mode_detail"
            st.rerun()

    with col2:
        if st.button("🎨 그림으로 표현", use_container_width=True):
            st.session_state.mode = "draw"
            st.session_state.step = "mode_detail"
            st.rerun()

    with col3:
        if st.button("🎵 음악으로 느끼기", use_container_width=True):
            st.session_state.mode = "listen"
            st.session_state.step = "mode_detail"
            st.rerun()


# -----------------------------
# STEP D) 선택한 표현 방식에 따른 상세 입력
# -----------------------------
elif st.session_state.step == "mode_detail":
    mode = st.session_state.get("mode")

    # [KEEP] 상단 맥락 유지
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:18px;height:18px;border-radius:50%;background:{st.session_state.base_color};"></div>
            <div>
                <b>{st.session_state.base_emotion}</b><br/>
                {st.session_state.phrase}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("---")

    # =========================
    # ✍️ 글 모드
    # =========================
    if mode == "write":
        st.subheader("✍️ 글로 표현하기")

        # [NEW] 글 입력
        text_content = st.text_area(
            "자유롭게 적어보세요",
            value=st.session_state.get("text_content", ""),
            height=180,
            placeholder="오늘의 감정을 글로 풀어내 보세요."
        )
        st.session_state.text_content = text_content

        # [NEW] 배경 설명
        background = st.text_input(
            "이 글을 쓰게 된 생각이나 맥락 (선택)",
            value=st.session_state.get("background", ""),
            placeholder="예: 이 감정이 들었던 상황"
        )
        st.session_state.background = background

    # =========================
    # 🎨 그림 모드
    # =========================
    elif mode == "draw":
        st.subheader("🎨 그림으로 표현하기")

        # [NEW] 그림 업로드
        image_file = st.file_uploader(
            "그림 또는 낙서 업로드",
            type=["png", "jpg", "jpeg"]
        )

        if image_file:
            st.image(image_file, caption="업로드한 그림", use_column_width=True)
            st.session_state.image_file = image_file

        # [NEW] 배경 설명
        background = st.text_input(
            "이 그림을 그릴 때의 생각이나 느낌 (선택)",
            value=st.session_state.get("background", ""),
            placeholder="예: 왜 이런 색이나 형태를 썼는지"
        )
        st.session_state.background = background

    # =========================
    # 🎵 음악 모드
    # =========================
    elif mode == "listen":
        st.subheader("🎵 음악으로 느끼기")

        # [NEW] 음악 모드는 설명 입력 없음
        st.info("선택한 감정과 문장을 바탕으로 음악을 추천합니다.")
        st.write("※ 다음 단계에서 AI 추천이 연결됩니다.")

    st.write("---")

    # [ADD] 다음 단계 버튼 (AI 개입 선택으로)
    if st.button("다음 단계로 ➜ (저장 / AI 대화 / 디벨롭)"):
        st.session_state.step = "ai_choice"
        st.rerun()
# -----------------------------
# STEP E) AI 개입 선택  ✅ 이번 STEP 핵심
# -----------------------------
elif st.session_state.step == "ai_choice":
    st.subheader("이 다음은 어떻게 할까요?")

    # [KEEP] 지금까지의 감정 맥락 요약
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:18px;height:18px;border-radius:50%;background:{st.session_state.base_color};"></div>
            <div>
                <b>{st.session_state.base_emotion}</b><br/>
                {st.session_state.phrase}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("---")

    # [NEW] 선택지를 카드처럼 배치
    col1, col2, col3 = st.columns(3)

    # -------------------------
    # 1️⃣ 그대로 저장
    # -------------------------
    with col1:
        if st.button("💾 그대로 저장", use_container_width=True):
            # [ADD] AI를 사용하지 않았다는 기록
            st.session_state.ai_action = "none"

            # [NEW] 다음 단계: 마무리
            st.session_state.step = "final_message"
            st.rerun()

    # -------------------------
    # 2️⃣ AI와 대화
    # -------------------------
    with col2:
        if st.button("💬 AI와 대화", use_container_width=True):
            # [ADD] AI 역할: 따뜻한 조력자
            st.session_state.ai_action = "talk"

            # [NEW] 다음 단계: AI 대화 화면
            st.session_state.step = "ai_talk"
            st.rerun()

    # -------------------------
    # 3️⃣ AI로 디벨롭
    # -------------------------
    with col3:
        if st.button("✨ AI로 디벨롭", use_container_width=True):
            # [ADD] AI 역할: 표현 확장 보조
            st.session_state.ai_action = "develop"

            # [NEW] 다음 단계: 디벨롭 화면
            st.session_state.step = "ai_develop"
            st.rerun()


