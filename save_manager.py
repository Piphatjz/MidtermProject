# -*- coding: utf-8 -*-
"""
save_manager.py  (web-safe version)
บันทึก/โหลดเกมผ่าน virtual filesystem ของ Pygbag
(ไม่คงค้างระหว่าง session แต่ทำงานได้ใน WASM)
"""
import json
import os
import settings as S


def save_exists():
    try:
        return os.path.isfile(S.SAVE_FILE)
    except Exception:
        return False


def save_game(world, vehicle, extra=None):
    try:
        data = {
            "world": world.to_dict(),
            "vehicle": vehicle.to_dict(),
            "extra": extra or {},
        }
        with open(S.SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def load_game():
    with open(S.SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_save():
    try:
        if save_exists():
            os.remove(S.SAVE_FILE)
    except Exception:
        pass
