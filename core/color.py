# 경로 : core/color.py

"""
색 변화 로직

기획서 기준:
- 표현 활동 및 AI 상호작용 횟수에 따라 색을 점진적으로 옅게 변환
- 감정을 판단하지 않고 변화 과정을 시각화하는 역할
"""

from typing import Tuple


# 색상 이름 → RGB 매핑 (기본 원색)
COLOR_MAP = {
    "pink": (255, 105, 180),      # 설렘
    "green": (50, 205, 50),       # 즐거움
    "mint": (79, 209, 197),       # 평온
    "purple": (148, 0, 211),      # 외로움 (Dark Violet - 채도 높음)
    "magenta": (199, 21, 133),    # 서운함
    "blue": (30, 144, 255),       # 우울 (Dodger Blue - 채도 높음)
    "navy": (26, 58, 82),         # 지침
    "anxiety": (106, 90, 205),    # 불안 (Slate Blue)
    "orange": (255, 140, 0),      # 초조함
    "tangerine": (255, 99, 71),   # 서러움
    "red": (220, 20, 60),         # 분노
    "wine": (114, 47, 55),        # 답답함
    "black": (54, 69, 79),        # 혼란 (차콜색)
    "panic": (28, 28, 28),        # 패닉
    "shame": (139, 125, 107),     # 자괴감 (회갈색)
    "embarrassed": (255, 182, 193), # 창피함 (연분홍)
    "proud": (107, 142, 35),      # 뿌듯함 (올리브그린)
    "jealousy": (255, 179, 71),   # 질투 (밝은 골드)
    "longing": (255, 215, 0),     # 그리움 (Gold - 채도 높은 노란색)
    "grateful": (255, 218, 185),  # 감사함 (Peach)
    "emptiness": (169, 169, 169), # 허무함 (Dark Gray)
}

# 색상 코드 → 한글 감정 이름 매핑
MOOD_NAME_MAP = {
    "pink": "설렘",
    "green": "즐거움",
    "mint": "평온",
    "purple": "외로움",
    "magenta": "서운함",
    "blue": "우울",
    "navy": "지침",
    "anxiety": "불안",
    "orange": "초조함",
    "tangerine": "서러움",
    "red": "분노",
    "wine": "답답함",
    "black": "혼란",
    "panic": "패닉",
    "shame": "자괴감",
    "embarrassed": "창피함",
    "proud": "뿌듯함",
    "jealousy": "질투",
    "longing": "그리움",
    "grateful": "감사함",
    "emptiness": "허무함",
}


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB를 HEX 코드로 변환"""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX 코드를 RGB로 변환"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def lighten_color(
    color_name: str,
    intensity: float = 0.0
) -> str:
    """
    색을 점진적으로 옅게 만듦 (원색 → 흰색)
    
    Args:
        color_name: 색상 이름 (예: "pink", "blue")
        intensity: 옅어지는 강도 (0.0 ~ 1.0)
                   0.0 = 원색, 1.0 = 완전 흰색
    
    Returns:
        HEX 색상 코드 (예: "#FF69B4")
    """
    if color_name not in COLOR_MAP:
        # 기본값: 회색
        return "#999999"
    
    # 강도 제한 (0.0 ~ 1.0)
    intensity = max(0.0, min(1.0, intensity))
    
    # 원색 RGB 가져오기
    r, g, b = COLOR_MAP[color_name]
    
    # 흰색(255, 255, 255)에 가까워지도록 조정
    new_r = int(r + (255 - r) * intensity)
    new_g = int(g + (255 - g) * intensity)
    new_b = int(b + (255 - b) * intensity)
    
    return rgb_to_hex(new_r, new_g, new_b)


def calculate_color_intensity(
    expression_count: int = 0,
    ai_interaction_count: int = 0
) -> float:
    """
    표현 활동 + AI 사용 횟수에 따른 색 변화 강도 계산
    
    기획서 기준:
    - 표현 활동 1회 = 0.2 옅어짐
    - AI 상호작용 1회 = 0.15 옅어짐
    - 최대 0.8까지 (완전 흰색은 안 됨)
    
    Args:
        expression_count: 표현 활동 횟수 (글 쓰기, 그림 그리기 등)
        ai_interaction_count: AI 사용 횟수
    
    Returns:
        강도 값 (0.0 ~ 0.8)
    """
    # 표현 활동: 한 번에 0.2씩 옅어짐
    expression_impact = expression_count * 0.2
    
    # AI 상호작용: 한 번에 0.15씩 옅어짐
    ai_impact = ai_interaction_count * 0.15
    
    # 합산 (최대 0.8)
    total_intensity = min(0.8, expression_impact + ai_impact)
    
    return total_intensity


def get_color_with_activity(
    color_name: str,
    expression_done: bool = False,
    ai_used: bool = False,
    ai_count: int = 0
) -> str:
    """
    활동 상태에 따른 최종 색상 계산
    
    Args:
        color_name: 초기 감정 색
        expression_done: 표현 활동 완료 여부
        ai_used: AI 사용 여부
        ai_count: AI 사용 횟수
    
    Returns:
        HEX 색상 코드
    """
    # 활동 횟수 계산
    expression_count = 1 if expression_done else 0
    ai_interaction_count = ai_count if ai_used else 0
    
    # 강도 계산
    intensity = calculate_color_intensity(expression_count, ai_interaction_count)
    
    # 색 변환
    return lighten_color(color_name, intensity)


def get_color_preview(
    color_name: str,
    steps: int = 5
) -> list:
    """
    색 변화 미리보기 (단계별)
    
    Args:
        color_name: 색상 이름
        steps: 단계 수
    
    Returns:
        색상 코드 리스트 (원색 → 옅은색)
    """
    result = []
    for i in range(steps):
        intensity = (i / (steps - 1)) * 0.8  # 0.0 ~ 0.8
        result.append(lighten_color(color_name, intensity))
    return result


def get_gradient_css(color_name: str, intensity: float = 0.0) -> str:
    """
    그라데이션 CSS 생성 (UI용)
    
    Args:
        color_name: 색상 이름
        intensity: 옅어지는 강도
    
    Returns:
        CSS linear-gradient 문자열
    """
    base_color = lighten_color(color_name, intensity)
    light_color = lighten_color(color_name, min(1.0, intensity + 0.2))
    
    return f"linear-gradient(135deg, {light_color} 0%, {base_color} 100%)"
