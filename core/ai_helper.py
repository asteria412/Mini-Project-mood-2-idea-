# 경로 : core/ai_helper.py

import os
import base64
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def encode_image_to_base64(image_path: str) -> str:
    """
    이미지 파일을 base64로 인코딩
    
    Args:
        image_path: 이미지 파일 경로
    
    Returns:
        base64 인코딩된 문자열
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_image_for_dalle(image_path: str) -> str:
    """
    이미지를 분석해서 DALL-E 프롬프트용 설명 생성
    
    Args:
        image_path: 이미지 파일 경로
    
    Returns:
        이미지 설명 텍스트
    """
    try:
        base64_image = encode_image_to_base64(image_path)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """이미지를 분석해서 DALL-E가 재생성할 수 있도록 상세하게 설명해주세요.

**포함할 내용:**
- 전체 구도와 배치
- 색감과 분위기
- 주요 요소들과 위치
- 화풍/스타일 (수채화, 디지털, 스케치 등)
- 배경과 전경

**형식:** 
한 문단으로, 구체적이고 시각적으로 작성"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "이 이미지를 DALL-E가 재생성할 수 있도록 상세히 설명해주세요."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=300,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"이미지 분석 오류: {str(e)}"


def generate_image_with_dalle(prompt: str, output_path: str) -> bool:
    """
    DALL-E 3로 이미지 생성
    
    Args:
        prompt: DALL-E 프롬프트
        output_path: 저장할 파일 경로
    
    Returns:
        성공 여부
    """
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # 생성된 이미지 URL
        image_url = response.data[0].url
        
        # 이미지 다운로드 및 저장
        import requests
        img_data = requests.get(image_url).content
        with open(output_path, 'wb') as handler:
            handler.write(img_data)
        
        return True
    
    except Exception as e:
        print(f"DALL-E 이미지 생성 오류: {str(e)}")
        return False


def get_ai_response(
    mood_color: str,
    mood_text: str,
    mode: str,
    interaction_type: str,  # "chat" or "develop"
    user_content: Optional[str] = None,
    is_final: bool = False,  # ✅ 추가: 마지막 대화 여부
    image_path: Optional[str] = None,  # ✅ 추가: 이미지 경로 (draw 모드용)
    generate_new_image: bool = False,  # ✅ 추가: DALL-E로 새 이미지 생성 여부
    new_image_path: Optional[str] = None,  # ✅ 추가: 새 이미지 저장 경로
) -> str:
    """
    표현 방식별 AI 역할 수행
    
    기획서 기준:
    - 감정을 판단하거나 평가하지 않음
    - 감정을 해석하거나 결론 내리지 않음
    - 표현 활동이 자연스럽게 이어지도록 도움
    
    Args:
        mood_color: 감정 색 (예: pink, blue, navy)
        mood_text: 감정 한 줄
        mode: 표현 방식 (write/draw/music)
        interaction_type: AI 개입 유형 (chat/develop)
        user_content: 사용자가 입력한 내용 (선택)
        generate_new_image: DALL-E로 새 이미지 생성 여부 (draw 모드)
        new_image_path: 새 이미지 저장 경로
    
    Returns:
        AI 응답 텍스트
    """
    
    # ✅ DALL-E 이미지 생성 (draw 모드 + develop + 사용자 입력 있음)
    print(f"🔍 DALL-E 조건 체크: mode={mode}, type={interaction_type}, gen={generate_new_image}, img={image_path}, new={new_image_path}")
    
    if mode == "draw" and interaction_type == "develop" and generate_new_image and image_path and new_image_path:
        print(f"✅ DALL-E 실행 시작!")
        try:
            if os.path.exists(image_path):
                print(f"📷 이미지 분석 중: {image_path}")
                # 1. 기존 이미지 분석
                image_description = analyze_image_for_dalle(image_path)
                print(f"📝 이미지 설명: {image_description[:100]}...")
                
                # 2. 사용자 요청 결합
                if user_content:
                    dalle_prompt = f"{image_description}\n\n추가 요구사항: {user_content}"
                else:
                    dalle_prompt = image_description
                
                print(f"🎨 DALL-E 생성 시작...")
                # 3. DALL-E로 새 이미지 생성
                success = generate_image_with_dalle(dalle_prompt, new_image_path)
                
                if success:
                    print(f"✅ DALL-E 생성 완료: {new_image_path}")
                    return f"✨ 새로운 이미지를 생성했어요!\n\n{user_content if user_content else '기존 이미지를 바탕으로 재구성했습니다.'}\n\n생성된 이미지를 확인해보세요."
                else:
                    print(f"❌ DALL-E 생성 실패")
                    return "이미지 생성 중 오류가 발생했어요. 다시 시도해주세요."
            else:
                print(f"❌ 이미지 파일 없음: {image_path}")
        except Exception as e:
            print(f"❌ DALL-E 처리 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"이미지 생성 중 오류가 발생했어요: {str(e)}"
    else:
        print(f"❌ DALL-E 조건 불만족 - 일반 응답으로 진행")
    
    # 공통 시스템 프롬프트 (기획서: 감정 판단 금지)
    if is_final:
        # 2회차: 공감 마무리형
        system_prompt = """당신은 감정 표현을 돕는 따뜻한 조력자입니다.

**절대 금지 사항:**
- 질문하지 마세요 (❌ "~하셨나요?", "~어떠셨나요?", "~어떻게?")
- 감정을 판단하거나 평가하지 마세요
- "충분해요", "잘했어요" 같은 평가는 하지 마세요
- "좋아질 거예요", "괜찮아요" 같은 위로는 하지 마세요

**이번이 마지막 대화입니다. 반드시 다음 형식으로 응답:**
1. 공감 받아주기: "그렇게 느끼셨군요", "여기까지 표현하셨네요"
2. 부드러운 마무리: "떠오르는 글귀가 더 있다면 남겨보세요"
3. 2-3문장으로 짧게
4. **절대 질문으로 끝내지 마세요**

예시:
"붉은 색으로 강한 감정을 표현하셨네요. 더 떠오르는 생각이 있다면 자유롭게 남겨보세요."
"""
    else:
        # 1회차: 탐색형
        system_prompt = """당신은 감정 표현을 돕는 따뜻한 조력자입니다.

**중요한 원칙:**
- 감정을 판단하거나 평가하지 마세요
- 감정을 해석하거나 결론 내리지 마세요
- "좋아질 거예요", "괜찮아요" 같은 위로는 하지 마세요
- 대신, 표현 활동이 자연스럽게 이어지도록 도와주세요

**응답 방식:**
- 짧고 부드럽게 (2-3문장)
- 질문은 1~2개만 ("어떤 생각이 드세요?", "왜 그렇게 느끼셨어요?")
- 탐색적이고 호기심 있는 톤
- 사용자의 표현 의도를 존중하세요
"""
    
    # 표현 방식별 역할 (기획서 3페이지)
    mode_instructions = {
        "write": f"""당신은 글쓰기를 돕습니다.

{"**마무리 모드:**" if is_final else "**디벨롭 모드:**" if interaction_type == "develop" else "**대화 모드:**"}
{"""- 공감하고 마무리하세요
- 질문 금지""" if is_final else """- 질문하지 말고, 바로 개선된 글을 제시하세요
- 사용자 요청을 그대로 반영 (예: "당나라 시로" → 즉시 당나라 시 스타일로 다듬은 글 작성)
- 개선안만 제시하고, "~하면 어떨까요?" 같은 제안은 최소화""" if interaction_type == "develop" else """- 질문이나 제안을 통해 대화하세요
- 탐색적이고 호기심 있는 톤"""}

**공통 원칙:**
- 문체나 톤을 강제로 바꾸지 마세요 (사용자가 요청한 경우 제외)
- 글의 분위기와 흐름을 존중하세요""",
        
        "draw": f"""당신은 그림 표현을 돕습니다.

**중요: AI는 이미지를 편집하거나 그릴 수 없습니다**
- 이미지를 분석하고 조언만 할 수 있습니다

{"**마무리 모드:**" if is_final else "**디벨롭 모드:**" if interaction_type == "develop" else "**대화 모드:**"}
{"""- 공감하고 마무리하세요
- 질문 금지""" if is_final else """- 질문하지 말고, 바로 구체적인 개선 제안을 하세요
- 예: "나비 추가해줘" → "왼쪽 상단에 작은 나비 2마리를 그려보세요..."
- 실행 가능한 조언만 제시""" if interaction_type == "develop" else """- 질문을 통해 대화하세요
- 탐색적이고 호기심 있는 톤"""}

**공통 원칙:**
- 그림 실력이나 결과를 평가하지 마세요
- 이미지가 있으면: 구도, 색감, 분위기를 공감하세요""",
        
        "music": """당신은 음악 추천 전문가입니다.

**중요: 반드시 아래 형식을 정확히 따라주세요**

1. **첫 줄 (필수)**: 이 음악들을 추천하는 이유를 한 문장으로 설명
   - 감정 키워드와 음악 장르/분위기를 연결해서 설명
   - "~한 감정에 ~한 음악이 어울려요" 형식

2. **두 번째 줄**: 빈 줄

3. **세 번째 줄부터**: 곡 리스트 (3~5개)
   - 형식: "- 아티스트명 - 곡명"
   - 각 곡마다 줄바꿈

**예시 1:**
비 오는 밤의 감성을 담은 로파이 음악이 마음을 차분하게 만들어줄 거예요.

- Jinsang - Affection
- eevee - Rainy Days
- SwuM - Moonlight

**예시 2:**
답답한 마음을 뚫어줄 시원한 록 음악으로 에너지를 회복해보세요.

- Foo Fighters - The Pretender
- Arctic Monkeys - Do I Wanna Know
- The Killers - Mr. Brightside"""
    }
    
    mode_instruction = mode_instructions.get(mode, mode_instructions["write"])
    
    # 상호작용 유형별 접근
    if interaction_type == "chat":
        interaction_guide = """**상호작용 방식: 대화 (탐색)**
- 질문을 통해 표현을 도와주세요
- "어떤 생각이 드세요?", "왜 그렇게 느끼셨어요?" 같은 질문 OK
- 탐색적이고 호기심 있는 톤"""
    else:  # develop
        interaction_guide = f"""**상호작용 방식: 디벨롭 (개선/다듬기)**
- {"절대 질문하지 마세요! 공감하고 마무리하세요" if is_final else "절대 질문하지 마세요! 바로 개선안을 제시하세요"}
- 사용자의 요청을 그대로 반영해서 개선된 버전을 작성하세요
- 예: "당나라 시처럼 해줘" → 바로 당나라 시 스타일로 다듬은 글을 제시
- 예: "더 감성적으로" → 바로 감성적인 버전 제시
- **개선안만 제시하고, 추가 질문이나 설명은 최소화**"""
    
    # 사용자 프롬프트 구성
    user_prompt = f"""**오늘의 감정:**
색: {mood_color}
문장: {mood_text}

**표현 방식:** {mode}
**상황:** {interaction_guide}

"""
    
    if user_content:
        user_prompt += f"**사용자 입력:**\n{user_content}\n\n"
    
    # 상호작용 유형에 따라 다른 지시
    if interaction_type == "chat":
        user_prompt += "위 내용을 바탕으로, 질문이나 제안을 통해 표현 활동을 도와주세요."
    else:  # develop
        if is_final:
            user_prompt += "위 내용을 공감하고 짧게 마무리해주세요. **질문하지 마세요.**"
        else:
            user_prompt += "위 내용을 개선하거나 다듬어주세요. **질문하지 말고, 바로 개선된 버전을 제시하세요.**"
    
    # OpenAI API 호출
    try:
        # 이미지가 있는 경우 (draw 모드 + Vision)
        if image_path and os.path.exists(image_path):
            # 이미지를 base64로 인코딩
            base64_image = encode_image_to_base64(image_path)
            
            # Vision API 사용 (gpt-4o 필요)
            response = client.chat.completions.create(
                model="gpt-4o",  # Vision 지원 모델
                messages=[
                    {"role": "system", "content": system_prompt + "\n\n" + mode_instruction},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=300,
            )
        else:
            # 텍스트만 있는 경우 (기존 방식)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt + "\n\n" + mode_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300,
            )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"AI 응답 중 오류가 발생했습니다: {str(e)}"


def get_closing_message(
    initial_color: str,
    final_color: str,
    mode: str,
    ai_used: bool = False,
) -> str:
    """
    AI 한마디 - 세션 마무리 메시지
    
    기획서 부록:
    - 감정을 해석하거나 평가하지 않음
    - 오늘의 감정 기록이 완료되었음을 부드럽게 안내
    
    Args:
        initial_color: 시작 색
        final_color: 최종 색
        mode: 표현 방식
        ai_used: AI 사용 여부
    
    Returns:
        마무리 메시지
    """
    
    system_prompt = """당신은 감정 기록 세션을 마무리하는 따뜻한 조력자입니다.

**원칙:**
- 감정을 판단하거나 평가하지 마세요 ("좋아졌네요" ❌)
- 대신 따뜻한 바람과 위로는 괜찮습니다 ("풀렸길 바래요" ✅)
- 부드럽고 따뜻하게 마무리하세요

**응답 형식:**
- 1~2문장으로 짧게
- 따뜻하고 위로하는 톤
- 감정 이름을 언급하며 바람을 전하세요

**예시:**
- "오늘의 서운한 감정이 조금이나마 풀렸길 바래요."
- "화가 가라앉은 평온한 시간을 보내길 바랍니다."
- "외로움이 담긴 오늘이 기록되었어요. 차분한 시간 되길 바랄게요."
"""
    
    # 표현 방식 한글화
    mode_kr = {
        "write": "글쓰기",
        "draw": "그림",
        "music": "음악"
    }.get(mode, mode)
    
    user_prompt = f"""오늘의 감정 기록이 완료되었습니다.
- 감정: {initial_color}
- 표현 방식: {mode_kr}
- AI 사용: {"예" if ai_used else "아니오"}

이 감정에 맞는 따뜻한 마무리 인사를 해주세요.
감정 이름을 언급하며 "~풀렸길 바래요", "~되길 바랍니다" 같은 따뜻한 바람을 전해주세요."""
    
    print(f"🌙 마무리 메시지 생성 중... (색: {initial_color} → {final_color}, 모드: {mode})")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=100,
        )
        
        closing_msg = response.choices[0].message.content.strip()
        print(f"✅ 마무리 메시지: {closing_msg}")
        return closing_msg
    
    except Exception as e:
        # 오류 시 기본 메시지
        print(f"❌ 마무리 메시지 생성 실패: {e}")
        return "오늘의 감정이 기록되었어요. 🌙"
