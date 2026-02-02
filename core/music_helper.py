# 경로: core/music_helper.py

"""
음악 추천 관련 유틸리티
"""

import re
from urllib.parse import quote_plus
from typing import List, Dict


def parse_music_recommendations(ai_response: str) -> Dict[str, any]:
    """
    AI 응답에서 추천 이유와 곡 리스트 파싱
    
    Args:
        ai_response: AI의 음악 추천 응답
    
    Returns:
        {
            "reason": "추천 이유",
            "songs": [
                {"title": "곡명", "artist": "아티스트", "youtube_url": "링크"},
                ...
            ],
            "raw_text": "전체 응답"
        }
    """
    lines = ai_response.strip().split('\n')
    
    # 첫 줄은 추천 이유
    reason = lines[0].strip() if lines else ""
    
    # 곡명 파싱 패턴
    # 예: "- Jinsang - Affection" 또는 "• Artist - Song" 또는 "1. Artist - Song"
    song_pattern = re.compile(r'^[\-\•\*\d\.)\s]+(.+?)\s*[-–]\s*(.+)$')
    
    songs = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        
        match = song_pattern.match(line)
        if match:
            artist = match.group(1).strip()
            title = match.group(2).strip()
            
            # YouTube 검색 링크 생성
            query = f"{artist} {title}"
            youtube_url = generate_youtube_search_url(query)
            
            songs.append({
                "artist": artist,
                "title": title,
                "youtube_url": youtube_url,
                "display": f"{artist} - {title}"
            })
    
    return {
        "reason": reason,
        "songs": songs,
        "raw_text": ai_response
    }


def generate_youtube_search_url(query: str) -> str:
    """
    YouTube 검색 URL 생성
    
    Args:
        query: 검색 쿼리 (예: "Jinsang Affection")
    
    Returns:
        YouTube 검색 URL
    """
    encoded_query = quote_plus(query)
    return f"https://www.youtube.com/results?search_query={encoded_query}"


def format_music_response_html(parsed_data: Dict) -> str:
    """
    파싱된 음악 추천을 HTML 형식으로 변환
    
    Args:
        parsed_data: parse_music_recommendations의 결과
    
    Returns:
        HTML 형식의 추천 텍스트
    """
    html_parts = []
    
    # 추천 이유
    if parsed_data.get("reason"):
        html_parts.append(f'<p class="music-reason">{parsed_data["reason"]}</p>')
    
    # 곡 리스트
    if parsed_data.get("songs"):
        html_parts.append('<ul class="music-list">')
        for song in parsed_data["songs"]:
            html_parts.append(
                f'<li>'
                f'<span class="music-title">{song["display"]}</span> '
                f'<a href="{song["youtube_url"]}" target="_blank" class="youtube-link">🎵 들어보기</a>'
                f'</li>'
            )
        html_parts.append('</ul>')
    
    return '\n'.join(html_parts) if html_parts else parsed_data.get("raw_text", "")
