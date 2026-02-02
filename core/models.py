# 경로 : core/models.py

"""
데이터 모델

기획서 기준:
- 하루의 감정 기록을 하나의 객체로 관리
- 감정의 시작(기준 색) – 과정(활동, AI 사용) – 결과(최종 색)를 포함
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class MoodRecord:
    """
    감정 기록 데이터 모델
    
    기획서 기준:
    - 시작 색 (initial_color)
    - 최종 색 (final_color)
    - 활동 과정 추적
    """
    # 기본 정보
    date_time: str
    mood_text: str
    mode: str  # write / draw / music
    
    # 색상 정보 (핵심!)
    initial_color: str  # 시작 색 (원색)
    final_color: str    # 최종 색 (활동 후)
    color_intensity: float  # 옅어진 정도 (0.0 ~ 0.8)
    
    # 활동 정보
    expression_done: bool = False  # 표현 활동 완료 여부
    ai_used: bool = False         # AI 사용 여부
    ai_interaction_count: int = 0  # AI 사용 횟수
    
    # 내용
    text_content: Optional[str] = None
    draw_note: Optional[str] = None
    background: Optional[str] = None
    image_filename: Optional[str] = None
    music_keywords: Optional[str] = None
    ai_response: Optional[str] = None
    
    # 메타
    color_confirmed: bool = False  # 최종 색 확인 여부


def create_mood_record(
    mood_color: str,
    mood_text: str,
    mode: str,
    **kwargs
) -> dict:
    """
    감정 기록 생성 (딕셔너리 형태)
    
    storage_local.py의 build_record와 호환
    """
    return {
        "date_time": datetime.now().isoformat(timespec="seconds"),
        "mood_text": mood_text,
        "mode": mode,
        
        # 색상 정보
        "initial_color": mood_color,
        "final_color": kwargs.get("final_color", mood_color),
        "color_intensity": kwargs.get("color_intensity", 0.0),
        
        # 활동 정보
        "expression_done": kwargs.get("expression_done", False),
        "ai_used": kwargs.get("ai_used", False),
        "ai_interaction_count": kwargs.get("ai_interaction_count", 0),
        
        # 내용
        "text_content": kwargs.get("text_content"),
        "draw_note": kwargs.get("draw_note"),
        "background": kwargs.get("background"),
        "image_filename": kwargs.get("image_filename"),
        "music_keywords": kwargs.get("music_keywords"),
        "ai_response": kwargs.get("ai_response"),
        
        # 메타
        "color_confirmed": kwargs.get("color_confirmed", False),
    }
