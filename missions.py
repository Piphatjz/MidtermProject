# -*- coding: utf-8 -*-
"""
missions.py
ระบบภารกิจผสมประจำตา (Composite Missions with Difficulty Tiers)
มี 3 ระดับ: ง่าย (Easy), ปานกลาง (Medium), ยาก (Hard)
ผู้เล่นต้องบรรลุเงื่อนไขครบทุกข้อ (AND) แล้วกลับมาที่บ้านเพื่อรับชัยชนะ
"""
import random
import settings as S

DIFFICULTIES = {
    "easy": {
        "name": "ง่าย",
        "badge": "🟢 ง่าย",
        "color": (90, 220, 120),
        "bg_color": (22, 38, 28),
        "border_color": (55, 160, 85),
    },
    "medium": {
        "name": "ปานกลาง",
        "badge": "🟡 ปานกลาง",
        "color": (255, 205, 60),
        "bg_color": (38, 34, 22),
        "border_color": (190, 150, 45),
    },
    "hard": {
        "name": "ยาก",
        "badge": "🔴 ยาก",
        "color": (255, 95, 110),
        "bg_color": (38, 22, 26),
        "border_color": (190, 55, 75),
    },
}

MISSION_POOL = [
    # ==================== ง่าย (EASY) ====================
    {
        "id": "e_novice",
        "difficulty": "easy",
        "title": "มือใหม่หัดขุด",
        "desc": "ขุดทองคำ สำรวจชั้นดินตื้น และสร้างทุนเริ่มต้น",
        "goals": {
            "gold": 6,
            "depth": 15,
            "coins": 150,
        },
    },
    {
        "id": "e_shallow",
        "difficulty": "easy",
        "title": "สำรวจชั้นตื้น",
        "desc": "ขุดลึก 20 เมตร และค้นหาเพชรแรกใต้ผืนดิน",
        "goals": {
            "diamonds": 1,
            "gold": 8,
            "depth": 20,
        },
    },
    {
        "id": "e_apprentice",
        "difficulty": "easy",
        "title": "ช่างสว่านฝึกหัด",
        "desc": "อัปเกรดหัวขุด Lv.2 เก็บกระป๋องน้ำมันและขุดลึก 25 ม.",
        "goals": {
            "drill_lv": 2,
            "depth": 25,
            "fuel": 3,
        },
    },
    {
        "id": "e_merchant",
        "difficulty": "easy",
        "title": "พ่อค้าแร่รุ่นเยาว์",
        "desc": "สะสมทองคำ 10 ก้อน พร้อมเงินทุนสำรวจ 200 เหรียญ",
        "goals": {
            "gold": 10,
            "coins": 200,
            "depth": 18,
        },
    },

    # ==================== ปานกลาง (MEDIUM) ====================
    {
        "id": "m_gem_hunter",
        "difficulty": "medium",
        "title": "นักล่าอัญมณีใต้พิภพ",
        "desc": "เจาะลึก 40 ม. ตามหาเพชรเลอค่า 4 เม็ดและทองคำ 15 ก้อน",
        "goals": {
            "diamonds": 4,
            "gold": 15,
            "depth": 40,
        },
    },
    {
        "id": "m_bedrock",
        "difficulty": "medium",
        "title": "ผู้พิชิตชั้นหิน",
        "desc": "อัปเกรดหัวขุด Lv.3 ทะลวงชั้นหินลึก 50 ม. และเก็บเงิน 500 เหรียญ",
        "goals": {
            "drill_lv": 3,
            "depth": 50,
            "coins": 500,
        },
    },
    {
        "id": "m_machinist",
        "difficulty": "medium",
        "title": "วิศวกรเครื่องจักรยักษ์",
        "desc": "ยกระดับรถขุดขึ้นสู่ Tier 2 สำรวจลึก 45 ม. และหาเพชร 3 เม็ด",
        "goals": {
            "tier": 2,
            "diamonds": 3,
            "depth": 45,
        },
    },
    {
        "id": "m_energy",
        "difficulty": "medium",
        "title": "นักสำรวจพลังงาน",
        "desc": "เก็บน้ำมันใต้ดิน 6 กระป๋อง ขุดลึก 55 ม. และทองคำ 18 ก้อน",
        "goals": {
            "fuel": 6,
            "depth": 55,
            "gold": 18,
        },
    },

    # ==================== ยาก (HARD) ====================
    {
        "id": "h_abyss",
        "difficulty": "hard",
        "title": "ราชันย์เหมืองอเวจี",
        "desc": "ดำดิ่งสู่แกนพิภพลึก 80 ม. กวาดเพชร 8 เม็ดและทอง 25 ก้อน",
        "goals": {
            "diamonds": 8,
            "gold": 25,
            "depth": 80,
        },
    },
    {
        "id": "h_colossal",
        "difficulty": "hard",
        "title": "จักรกลสว่านสะท้านดิน",
        "desc": "พัฒนารถขึ้นสู่ Tier 3 ขุดลึก 70 ม. พร้อมเงินสะสม 1,200 เหรียญ",
        "goals": {
            "tier": 3,
            "depth": 70,
            "coins": 1200,
        },
    },
    {
        "id": "h_gravity",
        "difficulty": "hard",
        "title": "จ้าวแห่งแรงโน้มถ่วง",
        "desc": "ทำ Gravity Dive พุ่งดิ่ง 10 ครั้ง เพชร 6 เม็ด และขุดลึก 65 ม.",
        "goals": {
            "dives": 10,
            "diamonds": 6,
            "depth": 65,
        },
    },
    {
        "id": "h_tycoon",
        "difficulty": "hard",
        "title": "มหาเศรษฐีใต้พิภพ",
        "desc": "กอบโกยเพชร 10 เม็ด เงินสะสม 1,500 เหรียญ ขุดลึก 75 ม.",
        "goals": {
            "diamonds": 10,
            "coins": 1500,
            "depth": 75,
        },
    },
]


def format_goal_label(key, target):
    """ส่งคืนข้อความเป้าหมายแบบสั้นพร้อมไอคอน"""
    labels = {
        "diamonds": f"💎 เพชร {target} เม็ด",
        "gold": f"🪙 ทอง {target} ก้อน",
        "depth": f"⬇️ ลึก {target} ม.",
        "drill_lv": f"⛏️ หัวขุด Lv.{target}",
        "tier": f"📦 รถ Tier {target}",
        "coins": f"💰 สะสม {target:,} 🪙",
        "fuel": f"⛽ น้ำมัน {target} กระป๋อง",
        "dives": f"💥 พุ่งดิ่ง {target} ครั้ง",
    }
    return labels.get(key, f"{key}: {target}")


def format_goal_progress(key, current, target):
    """ส่งคืนข้อความความคืบหน้าปัจจุบัน / เป้าหมาย"""
    if key == "drill_lv":
        return f"⛏️ หัวขุด Lv.{current}/{target}"
    elif key == "tier":
        return f"📦 Tier {current}/{target}"
    elif key == "depth":
        return f"⬇️ {current}/{target} ม."
    elif key == "coins":
        return f"💰 {current:,}/{target:,}"
    elif key == "diamonds":
        return f"💎 {current}/{target}"
    elif key == "gold":
        return f"🪙 {current}/{target}"
    elif key == "fuel":
        return f"⛽ {current}/{target}"
    elif key == "dives":
        return f"💥 {current}/{target}"
    return f"{current}/{target}"


class Mission:
    def __init__(self, blueprint):
        self.id = blueprint["id"]
        self.difficulty = blueprint["difficulty"]
        self.title = blueprint["title"]
        self.desc = blueprint["desc"]
        self.goals = dict(blueprint["goals"])

        self.diff_info = DIFFICULTIES.get(self.difficulty, DIFFICULTIES["easy"])

        self.progress = {
            "diamonds": 0,
            "gold": 0,
            "depth": 0,
            "drill_lv": 1,
            "tier": 1,
            "coins": 0,
            "fuel": 0,
            "dives": 0,
        }

    def update_from_game(self, vehicle, depth):
        """อัปเดตสถิติที่ขึ้นกับยานพาหนะและตำแหน่ง"""
        self.progress["depth"] = max(self.progress["depth"], depth)
        self.progress["drill_lv"] = vehicle.drill_level()
        self.progress["tier"] = vehicle.overall_tier()
        self.progress["coins"] = max(self.progress["coins"], vehicle.coins)

    def add_mined_resource(self, res):
        """บันทึกแร่ที่ขุดได้เข้าสู่ความคืบหน้าภารกิจ"""
        if res == S.RES_DIAMOND:
            self.progress["diamonds"] += 1
        elif res == S.RES_GOLD:
            self.progress["gold"] += 1
        elif res == S.RES_FUEL:
            self.progress["fuel"] += 1

    def add_dive(self):
        """บันทึกการทำ Gravity Slam หรือพุ่งดิ่ง"""
        self.progress["dives"] += 1

    def is_goal_met(self, key):
        target = self.goals.get(key, 0)
        return self.progress.get(key, 0) >= target

    def is_completed(self):
        """ต้องบรรลุเป้าหมายครบทุกข้อ (AND)"""
        return all(self.is_goal_met(k) for k in self.goals)

    def completion_ratio(self):
        if not self.goals:
            return 1.0
        met = sum(1 for k in self.goals if self.is_goal_met(k))
        return met / len(self.goals)

    def get_goals_status(self):
        """
        ส่งคืนลิสต์ของเป้าหมาย:
        [(key, label, is_met, current, target, progress_text), ...]
        """
        result = []
        for key, target in self.goals.items():
            cur = self.progress.get(key, 0)
            is_met = cur >= target
            prog_txt = format_goal_progress(key, cur, target)
            label = format_goal_label(key, target)
            result.append((key, label, is_met, cur, target, prog_txt))
        return result

    def to_dict(self):
        return {
            "id": self.id,
            "difficulty": self.difficulty,
            "title": self.title,
            "desc": self.desc,
            "goals": self.goals,
            "progress": self.progress,
        }

    @classmethod
    def from_dict(cls, data):
        bp = {
            "id": data["id"],
            "difficulty": data["difficulty"],
            "title": data["title"],
            "desc": data.get("desc", ""),
            "goals": data["goals"],
        }
        m = cls(bp)
        m.progress = data.get("progress", m.progress)
        return m


def get_random_mission(difficulty=None):
    """สุ่มภารกิจ 1 แผน (สามารถระบุระดับได้)"""
    pool = MISSION_POOL
    if difficulty:
        pool = [m for m in MISSION_POOL if m["difficulty"] == difficulty]
        if not pool:
            pool = MISSION_POOL
    choice = random.choice(pool)
    return Mission(choice)


def get_three_contract_options():
    """สุ่มภารกิจมา 3 แผน: ง่าย 1, ปานกลาง 1, ยาก 1 สำหรับหน้าต่างเลือกสัญญา"""
    easy_pool = [m for m in MISSION_POOL if m["difficulty"] == "easy"]
    med_pool = [m for m in MISSION_POOL if m["difficulty"] == "medium"]
    hard_pool = [m for m in MISSION_POOL if m["difficulty"] == "hard"]

    chosen_easy = Mission(random.choice(easy_pool))
    chosen_med = Mission(random.choice(med_pool))
    chosen_hard = Mission(random.choice(hard_pool))

    return [chosen_easy, chosen_med, chosen_hard]
