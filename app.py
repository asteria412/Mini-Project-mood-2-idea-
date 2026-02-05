# 경로 : app.py

import os
from flask import Flask, render_template, request, redirect, url_for, session
from core.storage_local import (
    append_record,
    read_last_n,
    read_records_by_date,
    get_calendar_data,
    build_record,
    save_upload_file,
    get_records_last_24h,
    delete_record_by_datetime,
)
from core.ai_helper import get_ai_response, get_closing_message
from core.color import (
    get_color_with_activity,
    calculate_color_intensity,
    lighten_color,
    get_gradient_css,
    MOOD_NAME_MAP,
)
from core.policy import (
    can_use_ai,
    is_final_interaction,
    MAX_AI_INTERACTIONS,
    get_ai_usage_display,
)
from core.music_helper import (
    parse_music_recommendations,
)

app = Flask(__name__)
app.secret_key = "dev-secret"  # 개발용 / 배포 시 환경변수로 교체

DATA_PATH = "data/mood_log.jsonl"
UPLOAD_DIR = "static/uploads/user"  # 사용자 업로드 원본
GENERATED_DIR = "static/uploads/generated"  # DALL-E 생성 이미지

# 폴더 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

# 시작 시 경로 확인
print("=" * 60)
print("📁 파일 업로드 경로 설정:")
print(f"  - UPLOAD_DIR: {os.path.abspath(UPLOAD_DIR)}")
print(f"  - GENERATED_DIR: {os.path.abspath(GENERATED_DIR)}")
print(f"  - UPLOAD_DIR 존재: {os.path.exists(UPLOAD_DIR)}")
print(f"  - GENERATED_DIR 존재: {os.path.exists(GENERATED_DIR)}")
print("=" * 60)

# 모든 요청 로깅
@app.before_request
def log_request():
    print(f"🌐 요청: {request.method} {request.path}")


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
# ROOT - 랜딩 페이지 (두둥실 떠오르는 달)
# -------------------------------------------------
@app.route("/")
def root():
    """
    랜딩 페이지:
    - 두둥실 떠오르는 달 애니메이션
    - "시작하기" 버튼 → step1로 이동
    """
    # ✅ 랜딩 페이지 진입 시 이전 세션 초기화
    clear_draft()
    return render_template("landing.html")


# -------------------------------------------------
# 튜토리얼 페이지
# -------------------------------------------------
@app.route("/tutorial")
def tutorial():
    """
    튜토리얼 페이지
    - Mood2Idea 사용 방법 안내
    """
    return render_template("tutorial.html")


# -------------------------------------------------
# STEP 1. 감정 색 선택
# -------------------------------------------------
@app.route("/step/1", methods=["GET", "POST"])
def step1():
    """
    STEP 1
    - 감정 색 선택
    - 24시간 내 3개 이상이면 교체 선택으로 리다이렉트
    """
    if request.method == "POST":
        mood_color = request.form.get("mood_color")
        if mood_color:
            # ✅ 새로운 기록 시작: 이전 세션 데이터 완전 초기화
            clear_draft()
            update_draft(mood_color=mood_color)
            return redirect(url_for("step2"))
    
    # GET: 24시간 내 기록 체크
    recent_records = get_records_last_24h(DATA_PATH)
    if len(recent_records) >= 3:
        # 3개 이상이면 교체 선택 화면으로
        return redirect(url_for("replace_selection"))

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

    # 현재 색상 계산 (아직 활동 전)
    current_color = None
    if draft.get("mood_color"):
        current_color = lighten_color(draft.get("mood_color"), 0.0)
    
    return render_template(
        "index.html",
        step=2,
        draft=draft,
        current_color=current_color,
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

    # 현재 색상 계산
    current_color = None
    if draft.get("mood_color"):
        current_color = lighten_color(draft.get("mood_color"), 0.0)
    
    return render_template(
        "index.html",
        step=3,
        draft=draft,
        current_color=current_color,
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
        print("=" * 60)
        print("🚀 Step 4 POST 요청 시작!")
        print(f"  - draft mode: {draft.get('mode')}")
        print(f"  - request.files: {list(request.files.keys())}")
        print(f"  - request.form: {dict(request.form)}")
        print("=" * 60)
        
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
            print(f"📷 Step 4 - 파일 업로드:")
            print(f"  - image_file 객체: {image_file}")
            print(f"  - filename: {image_file.filename if image_file else 'None'}")
            
            image_filename = save_upload_file(image_file, UPLOAD_DIR)
            print(f"  - 저장된 파일명: {image_filename}")

        elif draft["mode"] == "music":
            # ✅ 음악: 키워드만 저장 (예: 새벽, 몽환, 로파이, 비 오는 밤…)
            music_keywords = request.form.get("music_keywords")

        # -------------------------------------------------
        # 표현 내용을 draft에 저장
        # -------------------------------------------------
        print(f"💾 Step 4 - draft 업데이트:")
        print(f"  - mode: {draft['mode']}")
        print(f"  - text_content: {text_content}")
        print(f"  - draw_note: {draw_note}")
        print(f"  - image_filename: {image_filename}")
        print(f"  - music_keywords: {music_keywords}")
        
        update_draft(
            text_content=text_content,
            draw_note=draw_note,
            background=background,
            image_filename=image_filename,
            music_keywords=music_keywords,
            expression_done=True,  # ✅ 표현 활동 완료
        )
        
        # 업데이트 후 확인
        draft_after = get_draft()
        print(f"✅ Step 4 - draft 업데이트 후:")
        print(f"  - image_filename: {draft_after.get('image_filename')}")

        # -------------------------------------------------
        # 음악 모드: 자동으로 AI 추천 호출
        # -------------------------------------------------
        if draft["mode"] == "music":
            # AI 사용 가능 여부 체크
            current_ai_count = draft.get("ai_count", 0)
            
            if not can_use_ai(current_ai_count):
                # AI 제한 초과 - 바로 저장
                return redirect(url_for("step6"))
            
            # AI 음악 추천 자동 호출
            new_ai_count = current_ai_count + 1
            is_final = is_final_interaction(new_ai_count)
            
            ai_response = get_ai_response(
                mood_color=draft.get("mood_color"),
                mood_text=draft.get("mood_text"),
                mode="music",
                interaction_type="develop",  # 음악은 항상 develop (추천)
                user_content=music_keywords,
                is_final=is_final,
            )
            
            # 음악 추천 파싱 (YouTube 링크 생성)
            parsed_music = parse_music_recommendations(ai_response)
            
            # AI 응답 저장
            update_draft(
                ai_response=ai_response,
                ai_used=True,
                ai_count=new_ai_count,
                ai_limit_exceeded=False,
                music_parsed=parsed_music,  # 파싱된 음악 데이터 저장
            )
            
            # AI 응답 화면으로 바로 이동
            return redirect(url_for("step5_result"))
        
        # 글쓰기/그림 모드: STEP5로 이동 (AI 개입 선택)
        return redirect(url_for("step5"))

    # 현재 색상 계산 (표현 활동 완료 시 색 변화 시작)
    current_color = None
    if draft.get("mood_color"):
        expression_done = draft.get("expression_done", False)
        intensity = calculate_color_intensity(
            expression_count=1 if expression_done else 0,
            ai_interaction_count=0
        )
        current_color = lighten_color(draft.get("mood_color"), intensity)
    
    return render_template(
        "index.html",
        step=4,
        draft=draft,
        current_color=current_color,
    )


# -------------------------------------------------
# STEP 5. AI 개입 선택
# -------------------------------------------------
@app.route("/step/5", methods=["GET", "POST"])
def step5():
    """
    STEP 5
    - AI 개입 선택
      1. 그대로 저장
      2. AI와 대화 (표현 전 도움)
      3. AI와 디벨롭 (표현 후 확장)
    
    기획서 기준:
    - AI는 조력자 역할
    - 감정 판단/평가 금지
    """
    draft = get_draft()
    if not draft.get("mode"):
        return redirect(url_for("step3"))
    
    if request.method == "POST":
        ai_choice = request.form.get("ai_choice")
        
        # 1. 그대로 저장 → Step 6 (색 변화 확인)으로
        if ai_choice == "save":
            update_draft(ai_used=False, ai_count=0)
            return redirect(url_for("step6"))
        
        # 2. AI와 대화 또는 3. AI와 디벨롭
        elif ai_choice in ["chat", "develop"]:
            # AI 사용 가능 여부 체크
            current_ai_count = draft.get("ai_count", 0)
            
            if not can_use_ai(current_ai_count):
                # AI 제한 초과 - Step 5로 다시 (에러 메시지)
                update_draft(ai_limit_exceeded=True)
                return redirect(url_for("step5"))
            
            # 사용자가 추가로 입력한 내용 (선택)
            user_input = request.form.get("user_input", "").strip()
            print(f"📝 user_input 받음: '{user_input}' (길이: {len(user_input)})")
            
            # 표현 내용 가져오기 (mode에 따라)
            user_content = None
            if draft.get("mode") == "write":
                user_content = draft.get("text_content")
            elif draft.get("mode") == "draw":
                user_content = draft.get("draw_note")
            elif draft.get("mode") == "music":
                user_content = draft.get("music_keywords")
            
            # 사용자 입력과 기존 내용 결합
            combined_content = user_input if user_input else user_content
            
            # 이미지 경로 가져오기 (draw 모드)
            image_path = None
            new_image_filename = None
            new_image_path = None
            generate_dalle = False
            
            if draft.get("mode") == "draw" and draft.get("image_filename"):
                image_path = os.path.join(UPLOAD_DIR, draft.get("image_filename"))
                print(f"📷 이미지 경로: {image_path}, 존재: {os.path.exists(image_path)}")
                
                # develop 선택 + user_input 있음 → DALL-E로 새 이미지 생성
                if ai_choice == "develop" and user_input and len(user_input) > 0:
                    # 새 이미지 파일명 생성 (generated 폴더에 저장)
                    import time
                    new_image_filename = f"dalle_{int(time.time())}.png"
                    new_image_path = os.path.join(GENERATED_DIR, new_image_filename)
                    generate_dalle = True
                    print(f"🎨 DALL-E 준비: user_input='{user_input}', new_image_path='{new_image_path}'")
            
            # 카운트 먼저 증가
            new_ai_count = current_ai_count + 1
            
            # 마지막 상호작용인지 확인
            is_final = is_final_interaction(new_ai_count)
            
            # AI 응답 받기 (마지막 여부 전달)
            print(f"🤖 AI 호출: mode={draft.get('mode')}, type={ai_choice}, generate_dalle={generate_dalle}")
            print(f"📊 AI 카운트: {new_ai_count}/{MAX_AI_INTERACTIONS}, is_final={is_final}")
            ai_response = get_ai_response(
                mood_color=draft.get("mood_color"),
                mood_text=draft.get("mood_text"),
                mode=draft.get("mode"),
                interaction_type=ai_choice,
                user_content=combined_content,
                is_final=is_final,
                image_path=image_path,
                generate_new_image=generate_dalle,
                new_image_path=new_image_path,
            )
            
            # 새 이미지가 생성되었으면 draft 업데이트
            if new_image_filename:
                update_draft(image_filename=new_image_filename)
            
            # AI 응답을 draft에 저장 + 카운트 업데이트
            update_draft(
                ai_response=ai_response,
                ai_used=True,
                ai_count=new_ai_count,
                ai_limit_exceeded=False,
            )
            
            # AI 응답 화면으로 이동
            return redirect(url_for("step5_result"))
    
    # AI 사용 현황
    ai_count = draft.get("ai_count", 0)
    can_use_ai_more = can_use_ai(ai_count)
    ai_usage = get_ai_usage_display(ai_count)
    ai_limit_exceeded = draft.get("ai_limit_exceeded", False)
    
    # 🔍 디버그: draft 상태 출력
    print(f"🔍 Step 5 GET - draft 상태:")
    print(f"  - mode: {draft.get('mode')}")
    print(f"  - image_filename: {draft.get('image_filename')}")
    print(f"  - draw_note: {draft.get('draw_note')}")
    print(f"  - text_content: {draft.get('text_content')}")
    
    # 현재 색상 계산
    current_color = None
    if draft.get("mood_color"):
        expression_done = draft.get("expression_done", False)
        intensity = calculate_color_intensity(
            expression_count=1 if expression_done else 0,
            ai_interaction_count=ai_count
        )
        current_color = lighten_color(draft.get("mood_color"), intensity)
    
    return render_template(
        "index.html",
        step=5,
        draft=draft,
        current_color=current_color,
        ai_count=ai_count,
        can_use_ai_more=can_use_ai_more,
        ai_usage=ai_usage,
        ai_limit_exceeded=ai_limit_exceeded,
    )


# -------------------------------------------------
# STEP 5 결과. AI 응답 확인 후 저장
# -------------------------------------------------
@app.route("/step/5/result", methods=["GET", "POST"])
def step5_result():
    """
    STEP 5 결과
    - AI 응답 확인
    - Step 5.9 (다음 행동 선택)으로 이동
    """
    draft = get_draft()
    if not draft.get("ai_response"):
        return redirect(url_for("step5"))
    
    if request.method == "POST":
        # Step 5.9 (다음 행동 선택)으로 이동
        return redirect(url_for("step5_next"))
    
    # 현재 색상 계산 (AI 사용 후)
    current_color = None
    if draft.get("mood_color"):
        expression_done = draft.get("expression_done", False)
        ai_count = draft.get("ai_count", 0)
        intensity = calculate_color_intensity(
            expression_count=1 if expression_done else 0,
            ai_interaction_count=ai_count
        )
        current_color = lighten_color(draft.get("mood_color"), intensity)
    
    return render_template(
        "index.html",
        step=5.5,  # 5.5는 결과 화면
        draft=draft,
        current_color=current_color,
    )


# -------------------------------------------------
# STEP 5.9. 다음 행동 선택
# -------------------------------------------------
@app.route("/step/5/next", methods=["GET", "POST"])
def step5_next():
    """
    STEP 5.9
    - 다음 행동 선택
      1. 표현 더 작성하기 (무제한)
      2. AI와 더 대화하기 (최대 2회)
      3. 저장하기
    """
    draft = get_draft()
    if not draft.get("mood_color"):
        return redirect(url_for("step1"))
    
    # AI 사용 현황
    ai_count = draft.get("ai_count", 0)
    can_use_ai_more = can_use_ai(ai_count)
    ai_usage = get_ai_usage_display(ai_count)
    
    if request.method == "POST":
        next_action = request.form.get("next_action")
        
        if next_action == "continue_expression":
            # 표현 더 작성하기 → Step 4로
            return redirect(url_for("step4"))
        
        elif next_action == "continue_ai":
            if can_use_ai_more:
                # 음악 모드: 다시 추천받기 (자동 AI 호출)
                if draft.get("mode") == "music":
                    new_ai_count = ai_count + 1
                    is_final = is_final_interaction(new_ai_count)
                    
                    ai_response = get_ai_response(
                        mood_color=draft.get("mood_color"),
                        mood_text=draft.get("mood_text"),
                        mode="music",
                        interaction_type="develop",
                        user_content=draft.get("music_keywords"),
                        is_final=is_final,
                    )
                    
                    # 음악 추천 파싱 (YouTube 링크 생성)
                    parsed_music = parse_music_recommendations(ai_response)
                    
                    update_draft(
                        ai_response=ai_response,
                        ai_count=new_ai_count,
                        music_parsed=parsed_music,  # 파싱된 음악 데이터 저장
                    )
                    
                    return redirect(url_for("step5_result"))
                
                # 글쓰기/그림 모드: AI와 더 대화하기 → Step 5로
                # 이전 AI 답변 유지 (대화 맥락 보존)
                return redirect(url_for("step5"))
            else:
                # AI 제한 초과
                return redirect(url_for("step5_next"))
        
        elif next_action == "save":
            # 저장하기 → Step 6으로
            return redirect(url_for("step6"))
    
    # 현재 색상 계산
    current_color = None
    if draft.get("mood_color"):
        expression_done = draft.get("expression_done", False)
        ai_count_calc = draft.get("ai_count", 0)
        intensity = calculate_color_intensity(
            expression_count=1 if expression_done else 0,
            ai_interaction_count=ai_count_calc
        )
        current_color = lighten_color(draft.get("mood_color"), intensity)
    
    return render_template(
        "index.html",
        step=5.9,  # 5.9는 다음 행동 선택
        draft=draft,
        current_color=current_color,
        ai_count=ai_count,
        can_use_ai_more=can_use_ai_more,
        ai_usage=ai_usage,
    )


# -------------------------------------------------
# STEP 6. 색 변화 확인
# -------------------------------------------------
@app.route("/step/6", methods=["GET", "POST"])
def step6():
    """
    STEP 6
    - 초기 색 vs 현재 색 비교
    - 감정이 해소되었는지 확인
    
    기획서 기준:
    - 활동 및 AI 사용에 따른 색 변화 반영
    - 최종 색 정리 여부 선택
    """
    draft = get_draft()
    if not draft.get("mood_color"):
        return redirect(url_for("step1"))
    
    # 색 변화 계산
    initial_color = draft.get("mood_color")
    mood_name = MOOD_NAME_MAP.get(initial_color, initial_color)  # 감정 이름 가져오기
    expression_done = draft.get("expression_done", False)
    ai_used = draft.get("ai_used", False)
    ai_count = draft.get("ai_count", 0)
    
    # 최종 색상 계산
    final_color_hex = get_color_with_activity(
        initial_color,
        expression_done=expression_done,
        ai_used=ai_used,
        ai_count=ai_count
    )
    
    # 색 변화 강도
    intensity = calculate_color_intensity(
        expression_count=1 if expression_done else 0,
        ai_interaction_count=ai_count if ai_used else 0
    )
    
    # 초기 색상 (원색)
    initial_color_hex = lighten_color(initial_color, 0.0)
    
    # 그라데이션 CSS
    initial_gradient = get_gradient_css(initial_color, 0.0)
    final_gradient = get_gradient_css(initial_color, intensity)
    
    # ✅ draft에 final_color 저장 (인디케이터 업데이트용)
    update_draft(final_color=final_color_hex, color_intensity=intensity)
    
    if request.method == "POST":
        # 사용자가 선택한 감정 진하기 (intensity)
        intensity_level_str = request.form.get("intensity_level")
        
        if intensity_level_str:
            # 사용자가 선택한 intensity 레벨
            user_intensity = float(intensity_level_str)
            
            # 같은 색깔에 선택한 intensity 적용
            user_final_color_hex = lighten_color(initial_color, user_intensity)
            
            print(f"✅ 사용자 선택 진하기: {user_intensity} (처음 색: {initial_color}, 최종 색: {user_final_color_hex})")
        else:
            # 선택 안 했으면 자동 계산된 색 사용
            user_final_color_hex = final_color_hex
            user_intensity = intensity
            print(f"⚠️ 진하기 선택 없음 - 자동 계산 사용")
        
        # 색 변화 확인 완료 → Step 7로
        update_draft(
            final_color=user_final_color_hex,
            color_intensity=user_intensity,
            color_confirmed=True,
        )
        return redirect(url_for("step7"))
    
    # 사용자 선택을 위한 intensity별 색깔 미리 계산
    intensity_colors = []
    for level in [0.0, 0.25, 0.5, 0.75, 1.0]:
        color_hex = lighten_color(initial_color, level)
        intensity_colors.append({
            'level': level,
            'color_hex': color_hex,
            'percentage': int((1 - level) * 100)  # 0.0 = 100%, 1.0 = 0%
        })
    
    return render_template(
        "index.html",
        step=6,
        draft=draft,
        mood_name=mood_name,  # ✅ 추가: 감정 이름
        initial_color_hex=initial_color_hex,
        final_color_hex=final_color_hex,
        initial_gradient=initial_gradient,
        final_gradient=final_gradient,
        intensity=intensity,
        intensity_colors=intensity_colors,  # ✅ 추가: intensity별 색깔
        current_color=final_color_hex,  # ✅ 추가: 오른쪽 인디케이터 업데이트
    )


# -------------------------------------------------
# STEP 7. 최종 저장
# -------------------------------------------------
@app.route("/step/7", methods=["GET", "POST"])
def step7():
    """
    STEP 7
    - 최종 저장
    - AI 한마디 (옵션)
    """
    draft = get_draft()
    if not draft.get("color_confirmed"):
        return redirect(url_for("step6"))
    
    if request.method == "POST":
        # 최종 저장
        record = build_record(
            mood_color=draft.get("mood_color"),
            mood_text=draft.get("mood_text"),
            mode=draft.get("mode"),
            text_content=draft.get("text_content"),
            draw_note=draft.get("draw_note"),
            background=draft.get("background"),
            image_filename=draft.get("image_filename"),
            music_keywords=draft.get("music_keywords"),
            ai_response=draft.get("ai_response"),
            ai_used=draft.get("ai_used", False),
        )
        
        # 색 정보 추가
        record["initial_color"] = draft.get("mood_color")
        record["final_color"] = draft.get("final_color")
        record["color_intensity"] = draft.get("color_intensity", 0.0)
        record["expression_done"] = draft.get("expression_done", False)
        record["ai_interaction_count"] = draft.get("ai_count", 0)
        
        append_record(DATA_PATH, record)
        clear_draft()
        return redirect(url_for("history", saved=1, n=1))
    
    # 감정 이름 매핑
    initial_mood_name = MOOD_NAME_MAP.get(draft.get("mood_color"), draft.get("mood_color"))
    
    # AI 마무리 한마디
    closing_message = get_closing_message(
        initial_color=initial_mood_name,  # 감정 이름 전달
        final_color=draft.get("final_color"),
        mode=draft.get("mode"),
        ai_used=draft.get("ai_used", False),
    )
    
    return render_template(
        "index.html",
        step=7,
        draft=draft,
        closing_message=closing_message,
    )


# -------------------------------------------------
# 교체 선택 (24시간 내 3개 제한)
# -------------------------------------------------
@app.route("/replace-selection")
def replace_selection():
    """
    24시간 내 3개 기록이 있을 때 교체 선택 화면
    """
    recent_records = get_records_last_24h(DATA_PATH)
    
    if len(recent_records) < 3:
        # 3개 미만이면 그냥 step1로
        return redirect(url_for("step1"))
    
    # 각 기록에 "몇 시간 전" 표시용 계산
    from datetime import datetime
    now = datetime.now()
    for record in recent_records:
        dt_str = record.get("date_time") or record.get("timestamp")
        if dt_str:
            record_dt = datetime.fromisoformat(dt_str)
            delta = now - record_dt
            hours = int(delta.total_seconds() / 3600)
            if hours < 1:
                record["time_ago"] = "방금 전"
            elif hours < 24:
                record["time_ago"] = f"{hours}시간 전"
            else:
                record["time_ago"] = f"{int(hours/24)}일 전"
        else:
            record["time_ago"] = "알 수 없음"
        
        # 감정 이름 추가
        mood_color = record.get("mood_color") or record.get("initial_color")
        record["mood_name"] = MOOD_NAME_MAP.get(mood_color, mood_color)
    
    return render_template(
        "replace_selection.html",
        records=recent_records,
    )


@app.route("/replace-record", methods=["POST"])
def replace_record():
    """
    선택한 기록 삭제 후 step1로
    """
    selected_datetime = request.form.get("selected_datetime")
    
    if selected_datetime:
        success = delete_record_by_datetime(DATA_PATH, selected_datetime)
        if success:
            print(f"✅ 기록 교체를 위해 삭제: {selected_datetime}")
        else:
            print(f"⚠️ 기록 삭제 실패: {selected_datetime}")
    
    # step1으로 리다이렉트 (이제 2개만 남았으므로 진입 가능)
    return redirect(url_for("step1"))


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


# -------------------------------------------------
# 캘린더
# -------------------------------------------------
@app.route("/calendar")
@app.route("/calendar/<int:year>/<int:month>")
def calendar_view(year=None, month=None):
    """
    캘린더 페이지
    - 월별 감정 색깔 표시
    - 날짜 클릭 → 상세 페이지
    """
    from datetime import datetime
    import calendar as cal
    
    # 기본값: 현재 년월
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    # 월 범위 검증
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    # 캘린더 데이터 가져오기
    calendar_data = get_calendar_data(DATA_PATH, year, month)
    
    # 캘린더 생성
    cal_obj = cal.Calendar(firstweekday=6)  # 일요일 시작
    month_days = cal_obj.monthdayscalendar(year, month)
    
    # 이전/다음 달 계산
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    
    # 오늘 날짜
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    return render_template(
        "calendar.html",
        year=year,
        month=month,
        month_days=month_days,
        calendar_data=calendar_data,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        today_str=today_str,
    )


@app.route("/calendar/date/<date_str>")
def calendar_date_detail(date_str):
    """
    특정 날짜의 상세 페이지
    - 해당 날짜의 모든 기록 표시
    - 처음 감정 → 마지막 감정 변화
    """
    records = read_records_by_date(DATA_PATH, date_str)
    
    # initial_color를 HEX 코드로 변환 (호환성 처리)
    for r in records:
        # initial_color가 없으면 mood_color 사용
        if not r.get("initial_color") and r.get("mood_color"):
            r["initial_color"] = r["mood_color"]
        
        # initial_color가 색상 이름이면 HEX로 변환
        initial = r.get("initial_color")
        if initial and not initial.startswith("#"):
            r["initial_color_hex"] = lighten_color(initial, 0.0)
            r["mood_name"] = MOOD_NAME_MAP.get(initial, initial)
        else:
            r["initial_color_hex"] = initial
            r["mood_name"] = initial
    
    return render_template(
        "calendar_date.html",
        date_str=date_str,
        records=records,
    )


if __name__ == "__main__":
    app.run(debug=True)
