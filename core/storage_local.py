# 경로 : core/storage_local.py

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


# ---------------------------------------------------------
# STEP 3-B. jsonl 저장/읽기
# - 1줄 = 1기록
# - 서버 껐다 켜도 남아있음
# ---------------------------------------------------------

def ensure_parent_dir(path: str) -> None:
    """파일 저장 경로의 상위 폴더가 없으면 생성"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def append_record(data_path: str, record: Dict[str, Any]) -> None:
    """jsonl에 한 줄 append"""
    ensure_parent_dir(data_path)
    with open(data_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_last_n(data_path: str, n: int = 1) -> List[Dict[str, Any]]:
    """
    최근 n개 레코드 반환 (최신이 먼저 오도록)
    - 파일이 없으면 []
    - 깨진 줄이 있어도 가능한 줄만 읽음(내구성)
    """
    if n <= 0:
        return []

    if not os.path.exists(data_path):
        return []

    records: List[Dict[str, Any]] = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # 깨진 줄은 스킵 (UX/내구성 우선)
                continue

    return list(reversed(records[-n:]))


def read_all_records(data_path: str) -> List[Dict[str, Any]]:
    """
    모든 레코드 반환 (최신이 먼저 오도록)
    """
    if not os.path.exists(data_path):
        return []

    records: List[Dict[str, Any]] = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return list(reversed(records))


def read_records_by_date(data_path: str, date_str: str) -> List[Dict[str, Any]]:
    """
    특정 날짜의 레코드만 반환
    
    Args:
        data_path: jsonl 파일 경로
        date_str: 날짜 문자열 (YYYY-MM-DD 형식)
    
    Returns:
        해당 날짜의 레코드 리스트 (최신순)
    """
    if not os.path.exists(data_path):
        return []

    records: List[Dict[str, Any]] = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # timestamp 또는 date_time에서 날짜 부분만 추출 (YYYY-MM-DD)
                timestamp = obj.get("timestamp") or obj.get("date_time", "")
                if timestamp.startswith(date_str):
                    # 오래된 데이터 호환: final_color가 없으면 mood_color 사용
                    if "final_color" not in obj and "mood_color" in obj:
                        from core.color import COLOR_MAP, rgb_to_hex
                        color_rgb = COLOR_MAP.get(obj["mood_color"])
                        if color_rgb:
                            obj["final_color"] = rgb_to_hex(*color_rgb)
                        else:
                            obj["final_color"] = "#808080"
                    records.append(obj)
            except json.JSONDecodeError:
                continue

    return list(reversed(records))


def get_calendar_data(data_path: str, year: int, month: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    특정 년월의 캘린더 데이터 반환
    
    Args:
        data_path: jsonl 파일 경로
        year: 년도
        month: 월
    
    Returns:
        {
            "2024-01-15": [record1, record2, ...],
            "2024-01-16": [record3, ...],
            ...
        }
    """
    if not os.path.exists(data_path):
        return {}

    # 해당 년월 문자열 (예: "2024-01")
    year_month_str = f"{year:04d}-{month:02d}"
    
    calendar_data: Dict[str, List[Dict[str, Any]]] = {}
    
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # timestamp 또는 date_time 사용
                timestamp = obj.get("timestamp") or obj.get("date_time", "")
                
                # 해당 년월인지 확인
                if timestamp.startswith(year_month_str):
                    # 날짜 추출 (YYYY-MM-DD)
                    date_str = timestamp[:10]
                    
                    # 오래된 데이터 호환: final_color가 없으면 mood_color 사용
                    if "final_color" not in obj and "mood_color" in obj:
                        from core.color import COLOR_MAP, rgb_to_hex
                        color_rgb = COLOR_MAP.get(obj["mood_color"])
                        if color_rgb:
                            obj["final_color"] = rgb_to_hex(*color_rgb)
                        else:
                            obj["final_color"] = "#808080"
                    
                    if date_str not in calendar_data:
                        calendar_data[date_str] = []
                    
                    calendar_data[date_str].append(obj)
            except json.JSONDecodeError:
                continue
    
    # 각 날짜별로 최신순 정렬
    for date_str in calendar_data:
        calendar_data[date_str] = list(reversed(calendar_data[date_str]))
    
    return calendar_data


# ---------------------------------------------------------
# STEP 4. 스키마(저장 데이터 형태) 빌더
# - 윤서가 이미 확인한 스키마 기반 + 확장 필드 포함
# ---------------------------------------------------------

def build_record(
    mood_color: str,
    mood_text: str,
    mode: str,
    *,
    text_content: Optional[str] = None,
    draw_note: Optional[str] = None,
    background: Optional[str] = None,
    image_filename: Optional[str] = None,
    music_keywords: Optional[str] = None,
    ai_response: Optional[str] = None,
    ai_used: bool = False,
) -> Dict[str, Any]:
    """
    저장 스키마 확정(= 이 함수가 '정의' 역할을 함)

    기본 필드:
    - date_time
    - mood_color
    - mood_text
    - mode (write/draw/music)

    선택 필드:
    - text_content (write)
    - draw_note (draw)
    - background (공통 맥락)
    - image_filename (draw)
    - music_keywords (music)
    - ai_response (STEP5: AI 응답)
    - ai_used (STEP5: AI 사용 여부)
    """
    return {
        "date_time": datetime.now().isoformat(timespec="seconds"),
        "mood_color": mood_color,
        "mood_text": mood_text,
        "mode": mode,

        "text_content": text_content,
        "draw_note": draw_note,
        "background": background,

        # STEP4 확장
        "image_filename": image_filename,
        "music_keywords": music_keywords,

        # STEP5 확장: AI 연동
        "ai_response": ai_response,
        "ai_used": ai_used,
    }


# ---------------------------------------------------------
# STEP 4. 업로드 파일 저장 유틸 (로컬 저장 방식)
# - static/uploads에 저장
# - uuid로 이름 충돌 방지
# - DB에는 파일 자체가 아니라 image_filename/URL을 저장하게 됨
# ---------------------------------------------------------

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def save_upload_file(
    file: Optional[FileStorage],
    upload_dir: str,
) -> Optional[str]:
    """
    업로드된 파일을 upload_dir에 저장하고 filename만 반환
    - 실패/없음이면 None
    - 한글 파일명 지원 (확장자만 추출)
    """
    print(f"💾 save_upload_file 호출:")
    print(f"  - file 객체: {file}")
    print(f"  - file.filename: {file.filename if file else 'None'}")
    print(f"  - upload_dir: {upload_dir}")
    
    if file is None or not getattr(file, "filename", ""):
        print(f"  ⚠️ 파일 없음 또는 filename 없음")
        return None

    # 원본 파일명에서 확장자 추출 (한글 파일명 지원)
    original_filename = file.filename
    if "." not in original_filename:
        return None

    ext = original_filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return None

    # UUID로 새 파일명 생성 (확장자만 유지)
    os.makedirs(upload_dir, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(upload_dir, new_name)
    
    try:
        file.save(save_path)
        print(f"✅ 파일 저장 성공: {new_name} (원본: {original_filename})")
        return new_name
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        return None
