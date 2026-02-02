# 경로 : core/policy.py

"""
AI 사용 정책

기획서 기준:
- 세션당 AI 호출 횟수 제한
- 감정의 과도한 가공을 방지하기 위한 정책 로직
"""

# AI 티키타카 최대 횟수 (프로토타입)
MAX_AI_INTERACTIONS = 2


def can_use_ai(current_count: int) -> bool:
    """
    AI 사용 가능 여부 체크
    
    Args:
        current_count: 현재 AI 사용 횟수
    
    Returns:
        사용 가능 여부 (True/False)
    """
    return current_count < MAX_AI_INTERACTIONS


def get_ai_limit_message(current_count: int) -> str:
    """
    AI 제한 상태 메시지
    
    Args:
        current_count: 현재 AI 사용 횟수
    
    Returns:
        상태 메시지
    """
    remaining = MAX_AI_INTERACTIONS - current_count
    
    if remaining > 0:
        return f"AI와 {remaining}회 더 대화할 수 있어요"
    else:
        return "AI와의 대화를 모두 사용했어요"


def is_final_interaction(current_count: int) -> bool:
    """
    마지막 AI 상호작용인지 확인
    
    Args:
        current_count: 현재 AI 사용 횟수 (사용 후 값)
    
    Returns:
        마지막 여부 (True/False)
    """
    return current_count >= MAX_AI_INTERACTIONS


def get_ai_usage_display(current_count: int) -> str:
    """
    AI 사용 현황 표시용
    
    Args:
        current_count: 현재 AI 사용 횟수
    
    Returns:
        "1/2회" 형식 문자열
    """
    return f"{current_count}/{MAX_AI_INTERACTIONS}회"
