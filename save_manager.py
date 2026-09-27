# -*- coding: utf-8 -*-
"""
save_manager.py
บันทึก / โหลดเกม เป็นไฟล์ JSON (เงื่อนไขจบเกมแบบที่ 3: เซฟแล้วออก)
"""
import json
import os
import settings as S


def save_exists():
    return os.path.isfile(S.SAVE_FILE)


def save_game(world, vehicle, extra=None):
    data = {
        "world": world.to_dict(),
        "vehicle": vehicle.to_dict(),
        "extra": extra or {},
    }
    with open(S.SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_game():
    with open(S.SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_save():
    if save_exists():
        os.remove(S.SAVE_FILE)
