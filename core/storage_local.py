# 경로 : core/storage_local.py

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# ---------------------------------------------------------
# STEP 3-B. 파일 기반 persistence (jsonl)
# - 1줄 = 1기록(JSON)
# - append로 쌓고, 읽을 때는 최근 N개를 가져온다
# ---------------------------------------------------------


def _ensure_data_file(path: str) -> None:
    """
    data 폴더/파일이 없으면 생성한다.
    - 폴더 없으면 mkdir
    - 파일 없으면 빈 파일 생성
    """
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            pass


def build_record(
    mood_color: Optional[str],
    mood_text: Optional[str],
    mode: Optional[str],
    text_content: Optional[str] = None,
    draw_note: Optional[str] = None,
    background: Optional[str] = None,
) -> Dict:
    """
    저장 스키마를 만들어주는 함수
    - STEP 3-B 스키마 기반
    - date_time 포함
    """
    return {
        "date_time": datetime.now().isoformat(timespec="seconds"),
        "mood_color": mood_color,
        "mood_text": mood_text,
        "mode": mode,  # write / draw / music

        # 선택 필드
        "text_content": text_content,
        "draw_note": draw_note,
        "background": background,
    }


def append_record(path: str, record: Dict) -> None:
    """
    기록 1개를 jsonl 파일에 append 한다.
    - record는 dict 형태
    - json 한 줄로 저장
    """
    _ensure_data_file(path)

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_last_n(path: str, n: int = 1) -> List[Dict]:
    """
    jsonl 파일에서 최근 n개 기록을 읽어온다.
    - 파일이 없으면 []
    - 최신이 위로 오도록 반환
    """
    _ensure_data_file(path)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines = [ln.strip() for ln in lines if ln.strip()]
    if not lines:
        return []

    n = max(1, int(n))
    last_lines = lines[-n:]

    records: List[Dict] = []
    # 최신이 위로 오도록 reversed
    for ln in reversed(last_lines):
        try:
            records.append(json.loads(ln))
        except json.JSONDecodeError:
            # 깨진 줄은 무시 (안전장치)
            continue

    return records
