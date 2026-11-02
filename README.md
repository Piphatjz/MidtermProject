# Dig & Treasure

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-green.svg)](https://www.pygame.org/)
[![Tests](https://img.shields.io/badge/Automated%20Tests-Passing%20100%25-brightgreen.svg)](test_game.py)
[![License](https://img.shields.io/badge/License-Com%20Sci%20Chula-red.svg)](#license)

Dig & Treasure is a 2D Action Mining & Resource Management game developed in Python using Pygame. The game is inspired by classic titles such as *Motherload* and *SteamWorld Dig*.

Players control a drill vehicle to explore subterranean soil and rock layers, gather valuable resources (Coins, Gold, Diamonds, and Fuel Canisters), and return to the surface base to sell ores, upgrade stats, customize vehicle parts in the Garage, and complete mission contracts or explore endless subterranean depths.

---

## Table of Contents

- [Key Features](#key-features)
- [Installation & Setup](#installation--setup)
- [Controls & Input Handling](#controls--input-handling)
- [Gameplay Loop](#gameplay-loop)
- [Vehicle Customization & Specifications](#vehicle-customization--specifications)
- [Resource & Upgrade System](#resource--upgrade-system)
- [Game Modes](#game-modes)
- [Project Architecture](#project-architecture)
- [Automated Testing](#automated-testing)
- [Documentation Reference](#documentation-reference)
- [License](#license)

---

## Key Features

1. **Dual Game Modes**:
   - **Mission Contracts Mode**: Procedural composite missions across three difficulty tiers (Easy, Medium, Hard) with real-time goal progress tracking.
   - **Classic Endless Mode**: Unlimited mining gameplay with depth-based Security Floor Barriers unlocked using collected coins.
2. **Physics-Driven Digging & Gravity Slam**:
   - **Auto-Centering Engine**: Smoothly aligns the vehicle to grid column centers when drilling vertically.
   - **Gravity Slam**: Converts accumulated potential energy from ascending into an explosive downward slam, boosting movement speed by 2.6x and digging power by 3.0x.
3. **Deep Customization & Progression**:
   - 4 upgrade paths (Power, Capacity, Energy, Speed) up to Level 6.
   - 4 chassis types (Standard, Scout Buggy, Titan Crawler, Hover-Pod) and 8 body colors.
   - 5 specialized drill heads with distinct passive abilities (Spiral, Titanium Diamond, Plasma Cutter, Magnetic Vortex, Seismic Hammer).
4. **Procedural Underground World**:
   - Randomly generated 15-column by 650-row grid with depth-scaled mineral density and rock hardness.
   - Dynamic block cracking rendering using 3 damage state overlay sprites.
5. **Resolution-Independent Display**:
   - Rendered on a fixed 720x810 virtual canvas with automatic scale/offset adjustment and mouse coordinate re-mapping for seamless Fullscreen (F11) support.
6. **Self-Contained Asset Generation**:
   - Includes `assets_gen.py` to procedurally draw all PNG sprites using Pillow and synthesize 12 WAV sound effects using mathematical wave equations.


---

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Pygame 2.5.0 or higher
- Pillow (PIL)

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Piphatjz/MidtermProject.git
   cd MidtermProject
   ```

2. **Install Required Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Game**:
   ```bash
   python main.py
   ```

---

## Controls & Input Handling

| Input Key | Function |
| :--- | :--- |
| **W / A / S / D** or **Arrow Keys** | Move vehicle and drill adjacent blocks (Up, Left, Down, Right) |
| **Left Mouse Click (Hold)** | Move and drill towards mouse cursor location |
| **Shift** or **Spacebar** | Activate Turbo Boost (2.6x speed) and Gravity Slam (3.0x drill power) |
| **E** | Interact: Open Shop/Garage at surface or unlock Floor Barrier |
| **H** or **F1** | Toggle How to Play / Help Overlay |
| **M** | Toggle Mute / Unmute Audio |
| **F11** | Toggle Fullscreen Display Mode |
| **ESC** | Open Pause Menu or return to previous menu |

---

## Gameplay Loop

```text
[ Underground Mining ] -> [ Gather Ores & Fuel ] -> [ Return to Surface Base ] -> [ Sell Ores & Refuel ] -> [ Upgrade & Customize ]
```

---

## Vehicle Customization & Specifications

### 1. Chassis Specifications
- **Standard Excavator**: Balanced default parameters.
- **Scout Buggy**: Lightweight frame providing +20% movement speed.
- **Titan Crawler**: Heavy-duty chassis expanding cargo capacity by +50% and energy reserve by +30%.
- **Hover-Pod**: Frictionless thrusters reducing flight energy consumption by 35%.

### 2. Specialized Drill Heads
- **Spiral Auger**: Standard drill head with low energy drain.
- **Titanium Rock-Crusher (Diamond)**: Bedrock Breaker passive — Drills solid rock immediately from Level 1 and increases rock damage by +50%.
- **Plasma Laser Cutter**: Superheated Melter passive — High-thermal beam boosting dirt digging speed by +65%.
- **Magnetic Vortex Drill**: Fortune Attractor passive — Increases ore selling value by +25% and provides a chance to extract extra minerals/fuel from empty earth.
- **Seismic Hammer Head**: Seismic Cleave passive — Impact shockwave drills 3 adjacent blocks simultaneously in a wide radius.

---

## Resource & Upgrade System

### Resource Values
- **Coin**: Value = 2G (Common in upper layers)
- **Gold**: Value = 5G (Uncommon in mid-depth layers)
- **Diamond**: Value = 20G (Rare in deep rock strata)
- **Fuel Canister**: Value = 0G (Restores +40 Energy immediately upon collection)

### Upgrade Categories
- **Power**: Increases drilling speed against dirt and rock blocks.
- **Capacity**: Expands cargo hold capacity for resources.
- **Energy**: Expands fuel tank capacity for longer expeditions.
- **Speed**: Increases flight and horizontal movement speed.

---

## 📥 วิธีติดตั้งและเริ่มเล่น (Installation & Setup)

### ข้อกำหนดเบื้องต้น (Prerequisites)
- **Python 3.9+** (รองรับ Python 3.9, 3.10, 3.11, 3.12)
- **Pygame 2.5+**
- **Pillow (PIL)** (สำหรับใช้สร้างสไปรต์ภาพอัตโนมัติ)

### ขั้นตอนการติดตั้ง (Installation Steps)

1. **Clone หรือ ดาวน์โหลด Repository**:
   ```bash
   git clone https://github.com/Piphatjz/MidtermProject.git
   cd MidtermProject
   ```

2. **ติดตั้ง Dependencies ที่จำเป็น**:
   ```bash
   pip install -r requirements.txt
   ```

3. **เริ่มต้นเล่นเกม**:
   ```bash
   python main.py
   ```

---

## 🎮 วิธีเล่นและการบังคับ (Controls & Gameplay Guide)

### ปุ่มควบคุมทั้งหมด (Controls Reference)

| ปุ่มควบคุม | การทำงาน |
| :--- | :--- |
| **`W` / `A` / `S` / `D`** หรือ **ปุ่มลูกศร** | บังคับทิศทางรถขุด (ขึ้น / ซ้าย / ลง / ขวา) |
| **คลิกเมาส์ซ้ายค้าง** | บังคับรถขุดเคลื่อนที่และขุดไปตามทิศทางของเคอร์เซอร์เมาส์ |
| **`Shift`** หรือ **`Spacebar`** | เปิดใช้งาน **Turbo Boost** (เร่งสปีด `2.6x`) และ **Gravity Slam** (เจาะกระแทก `3.0x`) |
| **`E`** | **Interact**: เปิดร้านค้า & อู่แต่งรถ (หน้าร้านผิวดิน) หรือกดปลดล็อคประตูกั้นชั้น |
| **`H`** หรือ **`F1`** | เปิด/ปิดหน้าต่าง **คู่มือวิธีเล่น & ปุ่มควบคุม (How to Play)** |
| **`M`** | เปิด/ปิดเสียงเกม (Mute / Unmute) |
| **`F11`** | สลับโหมดเต็มจอ (Fullscreen Toggle) |
| **`ESC`** | เมนูหยุดชั่วคราว (Pause Menu) หรือย้อนกลับ |

### วงจรเกมเพลย์ (Gameplay Loop)
```text
[ลงเหมืองขุดเจาะ] ➡️ [เก็บแร่ & น้ำมัน] ➡️ [ขับกลับบ้านบนผิวดิน] ➡️ [ขายแร่ & เติมพลังงานฟรี] ➡️ [อัปเกรด & แต่งรถ]
```

---

## 🚗 ระบบอู่แต่งรถและหัวขุดพิเศษ (Garage & Customization)

ผู้เล่นสามารถเข้าอู่แต่งรถได้จาก **หน้าร้านค้า (`E`)** หรือ **หน้าเมนูหลัก** เพื่อปรับแต่งรถขุด:

### 1. ตัวถังรถขุด 4 สไตล์ (Chassis Types)
- 🚜 **Standard Excavator**: ตัวถังมาตรฐาน สมดุลรอบด้าน
- 🏎️ **Scout Buggy**: ตัวถังน้ำหนักเบา ความเร็วเคลื่อนที่ `+20%`
- 🐘 **Titan Crawler**: ตัวถังยักษ์เพิ่มความจุถังแร่ `+50%` และความจุพลังงาน `+30%`
- 🛸 **Hover-Pod**: ยานลอยตัวไร้แรงเสียดทาน ประหยัดพลังงานจากการบิน `+35%`

### 2. หัวขุดพิเศษ 5 แบบ (Drill Heads & Abilities)
- 🌀 **Spiral Auger (มาตรฐาน)**: หัวเจาะเกลียวประหยัดพลังงาน ไว้วางใจได้เสมอ
- 💎 **Titanium Rock-Crusher (หัวเพชร)**: ** Bedrock Breaker** — เจาะหินแข็งได้ทันทีตั้งแต่เริ่มเกมโดยไม่ต้องรออัปเกรด + เจาะหินแรงขึ้น `+50%`
- ⚡ **Plasma Laser Cutter (หัวพลาสม่า)**: ** Superheated Melter** — ลำแสงความร้อนสูง เพิ่มแรงเจาะดิน `+65%` (เจาะไวมาก)
- 🧲 **Magnetic Vortex Drill (หัวแม่เหล็ก)**: ** Fortune Attractor** — ขายแร่ได้ราคาสูงขึ้น `+25%` และสุ่มดูดแร่/น้ำมันจากดินว่าง
- 💥 **Seismic Hammer Head (หัวคลื่นสั่นสะเทือน)**: ** Seismic Cleave** — คลื่นกระแทกขุดบล็อกข้างเคียงพร้อมกันวงกว้าง 3 ช่อง

---

## Game Modes

### 1. Mission Contracts Mode
- Select from 3 difficulty tiers (Easy, Medium, Hard).
- Complete composite objectives (e.g., mine 4 diamonds, reach depth 40m, earn 500 coins).
- Return to the surface home base upon completing all goals to win the mission.

### 2. Classic Endless Mode
- Continuous mining progression focused on coin accumulation.
- Security Floor Barriers guard deeper zones:
  - **Floor 1 (0-20m)**: Upper Soil (Unlocked)
  - **Floor 2 (21-45m)**: Sediment Strata (Unlock cost: 300 coins)
  - **Floor 3 (46-75m)**: Crystal Caverns (Unlock cost: 800 coins)
  - **Floor 4 (76-110m)**: Ancient Deep (Unlock cost: 1,800 coins)
  - **Floor 5 (111-150m)**: Core Abyss (Unlock cost: 3,200 coins)
  - **Floor 6+**: Endless Depths (Extends procedurally every 50m)

---

## Project Architecture

```text
MidtermProject/
├── main.py               # Application entry point, 60 FPS Game Loop, Resolution Scaling
├── settings.py           # Game balance constants, tile specifications, pricing formulas
├── game.py               # Core State Machine (MENU, CONTRACT, PLAYING, SHOP, GARAGE, PAUSED)
├── world.py              # Procedural grid generation, block HP logic, floor barriers
├── vehicle.py            # Physics, auto-centering, digging logic, Gravity Slam, upgrade stats
├── missions.py           # Composite mission generator and objective progress tracking
├── ui.py                 # HUD rendering, menu systems, vehicle/drill drawing, toasts & hints
├── particles.py          # Particle systems (dirt debris, sparks, smoke, shockwaves) & floating text
├── assets.py             # Asset loading manager with image/sound caching and cooldowns
├── assets_gen.py         # Procedural asset generator for PNG images and WAV audio synthesis
├── save_manager.py       # Game state serialization/deserialization (JSON)
├── test_game.py          # Automated headless integration & unit test suite
├── CODE_PRESENTATION_GUIDE.md # Code presentation guide for mentors and reviewers
├── SYSTEM_DOCUMENTATION.md    # Detailed system architecture documentation
└── requirements.txt      # Dependency specification (pygame, pillow)
```


---

## Automated Testing

The project includes an automated test runner (`test_game.py`) operating headlessly without requiring a graphical display:

```bash
python test_game.py
```

### Verified Test Cases:
- Asset loading validation for all images and synthesized audio.
- Vehicle physics, movement bounds, and block breaking logic.
- Chassis stat modifiers and special drill head abilities.
- Floor barrier unlocking and classic mode persistence.
- Save/load state serialization integrity.
- Full UI state rendering.

---

## Documentation Reference

- **[Code Presentation Guide (CODE_PRESENTATION_GUIDE.md)](CODE_PRESENTATION_GUIDE.md)**: Guide for code walkthroughs and mentor reviews.
- **[System Architecture Documentation (SYSTEM_DOCUMENTATION.md)](SYSTEM_DOCUMENTATION.md)**: Full technical specifications and subsystem design.
- **[1-Page Game Features (GAME_FEATURES_1PAGE.md)](GAME_FEATURES_1PAGE.md)**: Executive summary of game features.

---

## License

This project is developed as part of the coursework for the **Department of Computer Science, Chulalongkorn University (Com Sci Chula)**. All rights reserved.


