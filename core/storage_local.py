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
    """
    if file is None or not getattr(file, "filename", ""):
        return None

    filename = secure_filename(file.filename)
    if "." not in filename:
        return None

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return None

    os.makedirs(upload_dir, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(upload_dir, new_name)
    file.save(save_path)
    return new_name
