# -*- coding: utf-8 -*-
"""
save_manager.py
ระบบจัดการบันทึกและโหลดเกมแบบหลายช่อง (Multi-Slot Save/Load System 5 ช่อง):
- บันทึกแยกอิสระ 5 สล็อต: saves/slot_1.json .. saves/slot_5.json
- บันทึกการตั้งค่าเสียงและระบบ: saves/settings.json
- บันทึกแบบ Atomic Write (เขียนลง temp file แล้ว os.replace) ป้องกันไฟล์เสียหาย
- ปลอดภัย ไฟล์เสียหรือผิดฟอร์แมตไม่ทำให้เกม crash
- ย้ายข้อมูลเซฟเดี่ยวเดิม (savegame.json) เข้า slot_1 อัตโนมัติ (Backward Compatibility Migration)
- รองรับการเปลี่ยนโฟลเดอร์สำหรับชุดทดสอบอัตโนมัติ (set_saves_dir)
"""
import json
import os
import tempfile
from datetime import datetime
import settings as S

MAX_SLOTS = 5
_DEFAULT_SAVES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
_CURRENT_SAVES_DIR = _DEFAULT_SAVES_DIR


def set_saves_dir(path):
    """กำหนดโฟลเดอร์สำหรับเก็บไฟล์เซฟ (ใช้สำหรับชุดทดสอบอัตโนมัติเพื่อไม่ให้กระทบเซฟจริง)"""
    global _CURRENT_SAVES_DIR
    _CURRENT_SAVES_DIR = path
    os.makedirs(_CURRENT_SAVES_DIR, exist_ok=True)


def get_saves_dir():
    """คืนค่าโฟลเดอร์เก็บเซฟปัจจุบัน และสร้างโฟลเดอร์หากยังไม่มี"""
    os.makedirs(_CURRENT_SAVES_DIR, exist_ok=True)
    return _CURRENT_SAVES_DIR


def reset_saves_dir():
    """รีเซ็ตกลับเป็นโฟลเดอร์เซฟมาตรฐาน"""
    global _CURRENT_SAVES_DIR
    _CURRENT_SAVES_DIR = _DEFAULT_SAVES_DIR
    os.makedirs(_CURRENT_SAVES_DIR, exist_ok=True)


def get_slot_path(slot_id):
    """ส่งคืนพาธไฟล์ JSON ของสล็อตที่ระบุ (1 - 5)"""
    return os.path.join(get_saves_dir(), f"slot_{slot_id}.json")


def get_settings_path():
    """ส่งคืนพาธไฟล์การตั้งค่า settings.json"""
    return os.path.join(get_saves_dir(), "settings.json")


def load_settings():
    """โหลดการตั้งค่าระบบ (เช่น สถานะปิดเสียง muted) คืนค่า dict"""
    path = get_settings_path()
    if not os.path.isfile(path):
        return {"muted": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"muted": False}


def save_settings(settings_data):
    """บันทึกการตั้งค่าระบบลง settings.json แบบ Atomic Write"""
    s_dir = get_saves_dir()
    final_path = get_settings_path()
    fd, temp_path = tempfile.mkstemp(prefix="set_tmp_", suffix=".json", dir=s_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, final_path)
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        print(f"[SaveManager] Error saving settings: {e}")


def get_profile_path():
    """ส่งคืนพาธไฟล์ข้อมูลส่วนกลาง/ปลดล็อคถาวร profile.json"""
    return os.path.join(get_saves_dir(), "profile.json")


def _get_default_profile():
    return {
        "tokens": getattr(S, "DEFAULT_TOKENS", 0),
        "unlocked_colors": ["yellow", "blue", "red", "green"],
        "unlocked_chassis": ["standard"],
        "unlocked_drills": ["spiral"],
        "tech_drone": False,
        "tech_radio": False,
        "equipped_color": getattr(S, "DEFAULT_VEHICLE_COLOR", "yellow"),
        "equipped_type": getattr(S, "DEFAULT_VEHICLE_TYPE", "standard"),
        "equipped_drill": getattr(S, "DEFAULT_DRILL_HEAD", "spiral"),
    }


def load_profile():
    """
    โหลดข้อมูลความคืบหน้าระดับบัญชี/ส่วนกลาง (Global Account Profile):
    - Token รวมสะสม
    - รายการสี, ตัวถัง, หัวขุด, เทคโนโลยีที่ปลดล็อคแล้วถาวร
    หากยังไม่มีไฟล์ จะตรวจสอบและดึง (migrate) ข้อมูลจากเซฟเดิมเข้ามาอัตโนมัติ
    """
    path = get_profile_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            prof = _get_default_profile()
            prof.update(data)
            return prof
        except Exception:
            return _get_default_profile()

    # หากยังไม่มี profile.json: ตรวจสอบและดึงข้อมูลจากทุกช่องเซฟเดิมหรือ savegame.json
    prof = _get_default_profile()
    max_tokens = 0
    all_colors = set(prof["unlocked_colors"])
    all_chassis = set(prof["unlocked_chassis"])
    all_drills = set(prof["unlocked_drills"])
    has_drone = False
    has_radio = False

    for sid in range(1, MAX_SLOTS + 1):
        sp = get_slot_path(sid)
        if os.path.isfile(sp):
            try:
                with open(sp, "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                vdata = sdata.get("game_data", {}).get("vehicle", sdata.get("vehicle", {}))
                max_tokens = max(max_tokens, vdata.get("tokens", 0))
                all_colors.update(vdata.get("unlocked_colors", []))
                all_chassis.update(vdata.get("unlocked_chassis", []))
                all_drills.update(vdata.get("unlocked_drills", []))
                if vdata.get("tech_drone", False):
                    has_drone = True
                if vdata.get("tech_radio", False):
                    has_radio = True
            except Exception:
                pass

    if os.path.isfile(S.SAVE_FILE):
        try:
            with open(S.SAVE_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            ov = old.get("vehicle", {})
            max_tokens = max(max_tokens, ov.get("tokens", 0))
            all_colors.update(ov.get("unlocked_colors", []))
            all_chassis.update(ov.get("unlocked_chassis", []))
            all_drills.update(ov.get("unlocked_drills", []))
            if ov.get("tech_drone", False):
                has_drone = True
            if ov.get("tech_radio", False):
                has_radio = True
        except Exception:
            pass

    prof["tokens"] = max_tokens
    prof["unlocked_colors"] = sorted(list(all_colors))
    prof["unlocked_chassis"] = sorted(list(all_chassis))
    prof["unlocked_drills"] = sorted(list(all_drills))
    prof["tech_drone"] = has_drone
    prof["tech_radio"] = has_radio

    save_profile(prof)
    return prof


def save_profile(profile_data):
    """บันทึกข้อมูลส่วนกลางลง profile.json แบบ Atomic Write"""
    s_dir = get_saves_dir()
    final_path = get_profile_path()
    fd, temp_path = tempfile.mkstemp(prefix="prof_tmp_", suffix=".json", dir=s_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, final_path)
        return True
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        print(f"[SaveManager] Error saving profile: {e}")
        return False


def add_global_tokens(amount):
    """เพิ่มหรือลด Token กองกลางรวม และบันทึกลง profile.json ทันที คืนค่าจำนวนล่าสุด"""
    prof = load_profile()
    prof["tokens"] = max(0, prof.get("tokens", 0) + amount)
    save_profile(prof)
    return prof["tokens"]


def unlock_profile_item(category, item_id):
    """ปลดล็อคชิ้นส่วนในโปรไฟล์ส่วนกลาง ('colors', 'chassis', 'drills', 'drone', 'radio')"""
    prof = load_profile()
    if category == "colors":
        colors = set(prof.get("unlocked_colors", []))
        colors.add(item_id)
        prof["unlocked_colors"] = sorted(list(colors))
    elif category == "chassis":
        chassis = set(prof.get("unlocked_chassis", []))
        chassis.add(item_id)
        prof["unlocked_chassis"] = sorted(list(chassis))
    elif category == "drills":
        drills = set(prof.get("unlocked_drills", []))
        drills.add(item_id)
        prof["unlocked_drills"] = sorted(list(drills))
    elif category == "drone":
        prof["tech_drone"] = True
    elif category == "radio":
        prof["tech_radio"] = True
    save_profile(prof)
    return prof


def migrate_legacy_save():
    """
    ตรวจสอบหากมีไฟล์ savegame.json เดิมอยู่ และยังไม่มี slot_1.json
    ให้ทำการย้ายข้อมูลเซฟเดิมเข้า slot_1.json อัตโนมัติ
    """
    legacy_file = S.SAVE_FILE
    slot1_path = get_slot_path(1)
    if os.path.isfile(legacy_file) and not os.path.isfile(slot1_path):
        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            # แปลงเป็นฟอร์แมต v2
            world_data = old_data.get("world", {})
            veh_data = old_data.get("vehicle", {})
            extra = old_data.get("extra", {})

            game_mode = extra.get("game_mode", "classic" if not extra.get("mission") else "mission")
            unlocked_floor = extra.get("unlocked_floor", 1)
            coins = veh_data.get("coins", 0)
            tokens = veh_data.get("tokens", 0)
            vtype = veh_data.get("vehicle_type", "standard")
            drill = veh_data.get("drill_head", "spiral")
            color = veh_data.get("color_id", "yellow")

            if game_mode == "classic":
                title = f"ชั้นที่ {unlocked_floor}"
                prog_txt = f"ปลดล็อคชั้น {unlocked_floor}"
            else:
                m_info = extra.get("mission", {})
                title = m_info.get("title", "ภารกิจผสม") if m_info else "ภารกิจผสม"
                prog_txt = "ข้อมูลที่ย้ายจากเซฟเดิม"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            migrated_payload = {
                "version": 2,
                "slot_id": 1,
                "game_mode": game_mode,
                "saved_at": now_str,
                "play_time_sec": 0,
                "summary": {
                    "mode_name": "โหมดคลาสสิก" if game_mode == "classic" else "โหมดภารกิจ",
                    "title": title,
                    "coins": coins,
                    "tokens": tokens,
                    "depth": int(veh_data.get("y", 0) // S.TILE) if S.TILE else 0,
                    "vehicle_type": vtype,
                    "drill_head": drill,
                    "color_id": color,
                    "unlocked_floor": unlocked_floor,
                    "progress_text": prog_txt,
                },
                "game_data": old_data,
            }
            # บันทึกลง slot 1
            s_dir = get_saves_dir()
            fd, temp_path = tempfile.mkstemp(prefix="mig_tmp_", suffix=".json", dir=s_dir)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(migrated_payload, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, slot1_path)
            print("[SaveManager] Migrated legacy savegame.json to slot_1.json successfully.")
        except Exception as e:
            print(f"[SaveManager] Legacy save migration failed: {e}")


def list_slots():
    """
    ตรวจสอบข้อมูลสรุปของทั้ง 5 ช่องเซฟ คืนค่าลิสต์ของ dict สำหรับนำไปวาดการ์ดใน UI
    หากไฟล์เสียจะส่งคืนสถานะ corrupted: True เพื่อให้ UI แสดงผลได้โดยไม่ crash
    """
    migrate_legacy_save()
    slots_info = []
    for sid in range(1, MAX_SLOTS + 1):
        path = get_slot_path(sid)
        if not os.path.isfile(path):
            slots_info.append({
                "slot_id": sid,
                "empty": True,
            })
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # รองรับทั้งฟอร์แมตใหม่ v2 และฟอร์แมตตรง
            if "summary" in data and "game_data" in data:
                summary = data["summary"]
                slots_info.append({
                    "slot_id": sid,
                    "empty": False,
                    "corrupted": False,
                    "version": data.get("version", 2),
                    "game_mode": data.get("game_mode", "mission"),
                    "saved_at": data.get("saved_at", "ไม่ระบุเวลา"),
                    "play_time_sec": data.get("play_time_sec", 0),
                    "summary": summary,
                })
            else:
                # กรณีไฟล์มีโครงสร้างแบบเดิมแปลงสรุปเบื้องต้น
                extra = data.get("extra", {})
                v_data = data.get("vehicle", {})
                gmode = extra.get("game_mode", "classic" if not extra.get("mission") else "mission")
                uflr = extra.get("unlocked_floor", 1)
                m_info = extra.get("mission", {})
                title = f"ชั้นที่ {uflr}" if gmode == "classic" else (m_info.get("title", "ภารกิจ") if m_info else "ภารกิจ")
                slots_info.append({
                    "slot_id": sid,
                    "empty": False,
                    "corrupted": False,
                    "version": 1,
                    "game_mode": gmode,
                    "saved_at": "บันทึกเก่า",
                    "play_time_sec": 0,
                    "summary": {
                        "mode_name": "โหมดคลาสสิก" if gmode == "classic" else "โหมดภารกิจ",
                        "title": title,
                        "coins": v_data.get("coins", 0),
                        "tokens": v_data.get("tokens", 0),
                        "depth": 0,
                        "vehicle_type": v_data.get("vehicle_type", "standard"),
                        "drill_head": v_data.get("drill_head", "spiral"),
                        "color_id": v_data.get("color_id", "yellow"),
                        "unlocked_floor": uflr,
                        "progress_text": "ข้อมูลเกมที่บันทึกไว้",
                    }
                })
        except Exception as e:
            slots_info.append({
                "slot_id": sid,
                "empty": False,
                "corrupted": True,
                "error": str(e),
                "summary": {
                    "mode_name": "ไฟล์เสียหาย",
                    "title": "ไฟล์บันทึกมีปัญหา",
                    "coins": 0,
                    "tokens": 0,
                    "depth": 0,
                    "vehicle_type": "standard",
                    "drill_head": "spiral",
                    "color_id": "yellow",
                    "unlocked_floor": 1,
                    "progress_text": "ไม่สามารถอ่านข้อมูลเซฟนี้ได้",
                }
            })
    return slots_info


def save_slot(slot_id, world, vehicle, extra=None, play_time_sec=0):
    """
    บันทึกข้อมูลเกมลงในสล็อตที่ระบุ (1 - 5) ด้วยวิธี Atomic Write (tempfile + os.replace)
    พร้อมคำนวณและเก็บ summary สำหรับแสดงผลบนการ์ดอย่างรวดเร็ว
    """
    if not (1 <= slot_id <= MAX_SLOTS):
        raise ValueError(f"slot_id must be between 1 and {MAX_SLOTS}")

    extra = extra or {}
    game_mode = extra.get("game_mode", "mission")
    unlocked_floor = extra.get("unlocked_floor", 1)
    mission_dict = extra.get("mission")

    if game_mode == "classic":
        mode_title = f"ชั้นที่ {unlocked_floor}"
        finfo = S.get_floor_info(unlocked_floor)
        prog_txt = f"{finfo['name']} (ลึก {finfo['min_depth']}ม.+)"
    else:
        if mission_dict:
            mode_title = mission_dict.get("title", "ภารกิจผสม")
            prog_txt = f"เป้าหมาย {len(mission_dict.get('goals', {}))} ข้อ"
        else:
            mode_title = "โหมดอิสระ"
            prog_txt = "ขุดสำรวจอิสระ"

    current_depth = int(max(0, (vehicle.y - (S.SURFACE_ROW * S.TILE)) // S.TILE)) if hasattr(S, "SURFACE_ROW") else 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    payload = {
        "version": 2,
        "slot_id": slot_id,
        "game_mode": game_mode,
        "saved_at": now_str,
        "play_time_sec": int(play_time_sec),
        "summary": {
            "mode_name": "โหมดคลาสสิก" if game_mode == "classic" else "โหมดภารกิจ",
            "title": mode_title,
            "coins": vehicle.coins,
            "tokens": getattr(vehicle, "tokens", 0),
            "depth": current_depth,
            "vehicle_type": vehicle.vehicle_type,
            "drill_head": vehicle.drill_head,
            "color_id": vehicle.color_id,
            "unlocked_floor": unlocked_floor,
            "progress_text": prog_txt,
        },
        "game_data": {
            "world": world.to_dict(),
            "vehicle": vehicle.to_dict(),
            "extra": extra,
        }
    }

    s_dir = get_saves_dir()
    final_path = get_slot_path(slot_id)
    fd, temp_path = tempfile.mkstemp(prefix=f"slot_{slot_id}_tmp_", suffix=".json", dir=s_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, final_path)
        return True
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        print(f"[SaveManager] Error saving slot {slot_id}: {e}")
        return False


def load_slot(slot_id):
    """
    โหลดข้อมูลเกมจากสล็อตที่ระบุ (1 - 5)
    ส่งคืน tuple: (success: bool, raw_game_data: dict, meta: dict)
    หากไฟล์เสียจะส่งคืน (False, None, error_dict) โดยไม่ crash
    """
    if not (1 <= slot_id <= MAX_SLOTS):
        return False, None, {"error": "Invalid slot ID"}

    path = get_slot_path(slot_id)
    if not os.path.isfile(path):
        return False, None, {"error": "Slot file does not exist"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "game_data" in data:
            game_data = data["game_data"]
            meta = {
                "version": data.get("version", 2),
                "slot_id": slot_id,
                "game_mode": data.get("game_mode", "mission"),
                "saved_at": data.get("saved_at", ""),
                "play_time_sec": data.get("play_time_sec", 0),
                "summary": data.get("summary", {}),
            }
            return True, game_data, meta
        else:
            # รูปแบบเก่าดั้งเดิม
            meta = {
                "version": 1,
                "slot_id": slot_id,
                "game_mode": data.get("extra", {}).get("game_mode", "mission"),
                "saved_at": "",
                "play_time_sec": 0,
                "summary": {},
            }
            return True, data, meta
    except Exception as e:
        print(f"[SaveManager] Error loading slot {slot_id}: {e}")
        return False, None, {"error": str(e)}


def delete_slot(slot_id):
    """ลบไฟล์บันทึกของสล็อตที่ระบุ"""
    path = get_slot_path(slot_id)
    if os.path.isfile(path):
        try:
            os.remove(path)
            return True
        except Exception as e:
            print(f"[SaveManager] Error deleting slot {slot_id}: {e}")
            return False
    return False


def has_any_save():
    """ส่งคืน True หากมีไฟล์เซฟอยู่ในสล็อตใดสล็อตหนึ่ง (1 - 5) หรือมีไฟล์เซฟเดิม"""
    migrate_legacy_save()
    for sid in range(1, MAX_SLOTS + 1):
        if os.path.isfile(get_slot_path(sid)):
            return True
    return False


# ==================== Backward Compatibility Helpers ====================

def save_exists():
    """ตรวจสอบการมีอยู่ของเซฟ (รองรับโค้ดเก่า)"""
    return has_any_save()


def save_game(world, vehicle, extra=None):
    """บันทึกเกมลง slot 1 (รองรับโค้ดเก่า)"""
    return save_slot(1, world, vehicle, extra=extra)


def get_latest_slot():
    """ค้นหาสล็อตที่มีการบันทึกล่าสุด (อิงจากเวลาแก้ไขไฟล์ mtime ล่าสุด)"""
    migrate_legacy_save()
    latest_sid = None
    latest_mtime = -1.0
    for sid in range(1, MAX_SLOTS + 1):
        p = get_slot_path(sid)
        if os.path.isfile(p):
            try:
                mt = os.path.getmtime(p)
                if mt > latest_mtime:
                    latest_mtime = mt
                    latest_sid = sid
            except Exception:
                pass
    return latest_sid


def load_game():
    """โหลดเกมจาก slot ที่บันทึกล่าสุด (รองรับโค้ดเก่า)"""
    latest_sid = get_latest_slot()
    if latest_sid is not None:
        ok, gdata, _ = load_slot(latest_sid)
        if ok:
            return gdata
    for sid in range(1, MAX_SLOTS + 1):
        path = get_slot_path(sid)
        if os.path.isfile(path):
            ok, gdata, _ = load_slot(sid)
            if ok:
                return gdata
    raise FileNotFoundError("No valid save file found.")


def delete_save():
    """ลบเซฟทั้งหมด (รองรับโค้ดเก่า)"""
    for sid in range(1, MAX_SLOTS + 1):
        delete_slot(sid)
    legacy = S.SAVE_FILE
    if os.path.isfile(legacy):
        try:
            os.remove(legacy)
        except Exception:
            pass
