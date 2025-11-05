"""
config_loader.py
------------------------------------
config.json 로드 전용 모듈
- 파일 존재와 구조가 보장된 환경 기준 (실전 버전)
------------------------------------
"""

import os
import json


def load_config():
    """config.json 로드"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        print(f"[Config] Loaded from {config_path}")
        return config
