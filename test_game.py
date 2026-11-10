# -*- coding: utf-8 -*-
"""
test_game.py
ทดสอบอัตโนมัติ (Automated headless test):
1. ตรวจสอบการโหลด Assets ครบทุกชิ้น
2. ทดสอบ Game Loop, World, Vehicle
3. ทดสอบการเคลื่อนที่ การเจาะบล็อก และการแตกของบล็อก
4. ทดสอบ Particle และระบบเซฟเกม
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import settings as S
import assets
import ui
from game import Game, PLAYING, SHOP
from world import World
from vehicle import Vehicle
from particles import ParticleSystem
import save_manager as SM


def run_tests():
    print("=== STARTING AUTOMATED TESTS ===")
    pygame.init()
    assets.init()
    ui.init_fonts()

    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))

    # Test 1: Assets Loading
    print("Testing assets loading...")
    for img in ["dirt", "grass", "rock", "tunnel", "crack_1", "crack_2", "crack_3",
                "res_coin", "res_gold", "res_diamond", "vehicle_body",
                "drill_down", "drill_up", "drill_left", "drill_right",
                "building_home", "building_shop"]:
        surf = assets.get_image(img)
        assert surf is not None, f"Failed to load image: {img}"
    print("  -> Assets images loaded OK.")

    for snd in ["drill", "dig_pop", "rock_clink", "coin", "gem", "sell", "refuel", "upgrade", "low_energy"]:
        assets.play_sound(snd)
    print("  -> Assets sounds triggered OK.")

    # Test 2: Game initialization & New Game
    print("Testing Game state & New Game...")
    game = Game(screen)
    game.new_game()
    assert game.vehicle is not None
    assert game.world is not None
    print(f"  -> Vehicle start position: ({game.vehicle.x}, {game.vehicle.y})")
    print(f"  -> Vehicle grid position: {game.vehicle.grid_pos()}")

    # Test 3: Simulation Loop (120 frames)
    print("Testing movement and digging simulation...")
    # Move DOWN into the mine
    for _ in range(30):
        game.vehicle.update(0.016, game.world, (0, 1), game.particles)
        game.particles.update(0.016)
        game.draw()

    print(f"  -> Position after moving down: ({game.vehicle.x:.1f}, {game.vehicle.y:.1f})")

    # Dig into solid dirt to the right
    col, row = game.vehicle.grid_pos()
    dirt_target_col = col + 1
    dirt_target_row = row
    game.world.tiles[dirt_target_row][dirt_target_col] = S.T_DIRT
    game.world.hp[dirt_target_row][dirt_target_col] = 4.0
    game.world.max_hp[dirt_target_row][dirt_target_col] = 4.0
    game.world.resource[dirt_target_row][dirt_target_col] = S.RES_GOLD

    print(f"  -> Starting drill on tile ({dirt_target_col}, {dirt_target_row}), initial HP: {game.world.hp[dirt_target_row][dirt_target_col]}")

    # Simulate pressing RIGHT to drill the tile
    dug = False
    for frame in range(60):
        game.vehicle.update(0.016, game.world, (1, 0), game.particles)
        game.particles.update(0.016)
        game.draw()
        if game.world.tiles[dirt_target_row][dirt_target_col] == S.T_EMPTY:
            dug = True
            print(f"  -> Block broken successfully at frame {frame}! Tile is now T_EMPTY.")
            break

    assert dug, "Block was not broken within 60 frames!"
    assert game.vehicle.cargo[S.RES_GOLD] > 0, "Resource was not collected into cargo!"
    print(f"  -> Cargo collected: {game.vehicle.cargo}")

    # Test 4: UI Rendering (Menu, Contracts, HUD, Shop, Pause, Victory)
    print("Testing UI Rendering for all states...")
    ui.draw_main_menu(screen, False, (100, 100))
    ui.draw_main_menu(screen, True, (100, 100))

    import missions
    contracts = missions.get_three_contract_options()
    assert len(contracts) == 3
    assert contracts[0].difficulty == "easy"
    assert contracts[1].difficulty == "medium"
    assert contracts[2].difficulty == "hard"
    ui.draw_contract_menu(screen, contracts, (100, 100))
    ui.draw_shop_menu(screen, game.vehicle, (100, 100))
    ui.draw_pause_menu(screen, (100, 100))
    ui.draw_end_screen(screen, "ทดสอบ", "คำอธิบาย", game.vehicle, (100, 100), mission=game.mission)
    how_buttons = ui.draw_how_to_play(screen, (100, 100))
    assert "close" in how_buttons
    ui.draw_quick_controls_bar(screen)

    # Test menu button presence
    m_btns = ui.draw_main_menu(screen, False, (100, 100))
    assert "how_to_play" in m_btns
    p_btns = ui.draw_pause_menu(screen, (100, 100))
    assert "how_to_play" in p_btns
    print("  -> UI rendering across all menus, HUD, and How to Play passed OK.")

    # Test 5: Composite Mission Progression & Victory
    print("Testing Composite Mission Progression and Victory...")
    test_bp = {
        "id": "test_m",
        "difficulty": "easy",
        "title": "ภารกิจทดสอบ",
        "desc": "ทดสอบระบบ",
        "goals": {
            "diamonds": 1,
            "gold": 2,
            "depth": 10,
        },
    }
    m = missions.Mission(test_bp)
    game.mission = m
    assert not game.mission.is_completed()

    # Progress goals
    game.mission.add_mined_resource(S.RES_DIAMOND)
    game.mission.add_mined_resource(S.RES_GOLD)
    game.mission.add_mined_resource(S.RES_GOLD)
    game.mission.update_from_game(game.vehicle, 12)
    assert game.mission.is_completed(), "All goals should be met!"
    print("  -> Composite Mission goals met correctly.")

    # Test 6: Save and Load with Mission
    print("Testing Save and Load with Mission...")
    game.save_and_quit()
    assert SM.save_exists(), "Save file does not exist!"
    game.load_game()
    assert game.mission is not None
    assert game.mission.id == "test_m"
    assert game.mission.is_completed()
    print("  -> Save and Load with Mission passed OK.")

    # Test 7: Customization Assets Verification
    print("Testing Customization Assets (Vehicles, Drills, Non-Square Icons)...")
    assert assets.get_image("res_fuel") is not None
    for vtid in S.VEHICLE_TYPES:
        for cid in S.VEHICLE_COLORS:
            img_key = f"vehicle_{vtid}_{cid}"
            surf = assets.get_image(img_key)
            assert surf is not None, f"Missing vehicle sprite: {img_key}"
            assert surf.get_width() == 42 and surf.get_height() == 42

    for dhid in S.DRILL_HEADS:
        for ddir in ["down", "up", "left", "right"]:
            d_key = f"drill_{dhid}_{ddir}"
            surf = assets.get_image(d_key)
            assert surf is not None, f"Missing drill sprite: {d_key}"
            assert surf.get_width() == 24 and surf.get_height() == 24
    print("  -> All 32 vehicle sprites, 20 drill head sprites, and non-square fuel canister verified OK.")

    # Test 8: Chassis Stat Modifiers & Drill Head Mechanics
    print("Testing Chassis Stat Modifiers & Drill Head Mechanics...")
    v_std = Vehicle(2, 2, vehicle_type="standard", drill_head="spiral")
    v_scout = Vehicle(2, 2, vehicle_type="scout", drill_head="spiral")
    v_titan = Vehicle(2, 2, vehicle_type="titan", drill_head="spiral")
    v_hover = Vehicle(2, 2, vehicle_type="hover", drill_head="spiral")

    # Scout should have higher speed and lower capacity than Standard
    assert v_scout.speed > v_std.speed, "Scout must be faster than Standard!"
    assert v_scout.max_capacity < v_std.max_capacity, "Scout must have smaller capacity!"

    # Titan should have higher capacity and extra energy
    assert v_titan.max_capacity > v_std.max_capacity, "Titan must have larger capacity!"
    assert v_titan.max_energy > v_std.max_energy, "Titan must have extra energy!"

    # Drill Heads Mechanics:
    # 1. Titanium Diamond can dig rock at Level 1 without rock_min_drill_level restriction
    v_spiral = Vehicle(2, 2, drill_head="spiral")
    v_diamond = Vehicle(2, 2, drill_head="diamond")
    assert not v_spiral.can_drill_rock(), "Standard spiral drill at Lv1 cannot drill rock!"
    assert v_diamond.can_drill_rock(), "Titanium Diamond drill MUST bypass rock requirement at Lv1!"

    # 2. Plasma Cutter has +65% drilling power
    v_plasma = Vehicle(2, 2, drill_head="plasma")
    assert v_plasma.power > v_std.power * 1.5, "Plasma cutter must have elevated drilling power!"

    # 3. Magnetic Vortex has bonus sell multiplier
    v_vortex = Vehicle(2, 2, drill_head="vortex")
    v_std.cargo[S.RES_GOLD] = 1
    v_std.cargo_count = 1
    v_vortex.cargo[S.RES_GOLD] = 1
    v_vortex.cargo_count = 1
    earned_std = v_std.sell_cargo()
    earned_vortex = v_vortex.sell_cargo()
    assert earned_vortex > earned_std, "Magnetic Vortex must yield more coins from selling cargo!"

    # 4. Seismic Hammer has reach = 2 immediately
    v_seismic = Vehicle(2, 2, drill_head="seismic")
    assert v_seismic.drill_reach == 2, "Seismic Hammer must have reach 2 from Tier 1!"
    print("  -> Vehicle chassis modifiers and drill head abilities verified OK.")

    # Test 9: Garage Menu UI, Surface Shop Access & Progression/Coin Unlocks
    print("Testing Garage Menu UI, Surface Shop Access & Progression/Coin Unlocks...")
    # Render all 3 garage tabs
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="color")
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="type")
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="drill")

    # Verify Garage button is removed from Main Menu
    test_game = Game(screen)
    assert test_game.state == "menu"
    test_game.draw()
    assert "garage" not in test_game.buttons, "Garage button must not appear on Main Menu!"

    # Start a new game and verify default starter loadout
    test_game.new_game()
    assert test_game.vehicle.color_id == "yellow"
    assert test_game.vehicle.vehicle_type == "standard"
    assert test_game.vehicle.drill_head == "spiral"
    assert test_game.vehicle.unlocked_colors == {"yellow"}
    assert test_game.vehicle.unlocked_types == {"standard"}
    assert test_game.vehicle.unlocked_drills == {"spiral"}

    # Park at surface shop and press E to open SHOP -> GARAGE
    test_game.vehicle.x = S.SHOP_COL * S.TILE + S.TILE / 2.0
    test_game.vehicle.y = (S.SURFACE_ROW - 1) * S.TILE + S.TILE / 2.0
    e_evt = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
    test_game.handle_event(e_evt)
    assert test_game.state == "shop", "Pressing E at surface shop must open SHOP!"
    test_game.draw()
    assert "tab_garage" in test_game.buttons
    assert "emergency_refuel" not in test_game.buttons, "Emergency fuel airdrop must be removed from Shop!"

    # Transition SHOP -> GARAGE
    click_gar = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["tab_garage"].center)
    test_game.handle_event(click_gar)
    assert test_game.state == "garage", "Must transition to GARAGE from surface SHOP!"
    test_game.draw()

    # In GARAGE: switch to tab_type
    assert "tab_type" in test_game.buttons
    click_type_tab = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["tab_type"].center)
    test_game.handle_event(click_type_tab)
    assert test_game.garage_tab == "type"
    test_game.draw()

    # 1) Attempt to select locked 'titan' without meeting requirement (requires capacity/energy Lv.3)
    assert "type_titan" in test_game.buttons
    click_titan = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["type_titan"].center)
    test_game.handle_event(click_titan)
    assert test_game.vehicle.vehicle_type == "standard", "Locked chassis must not equip before meeting requirement!"

    # 2) Meet requirement (capacity Lv.3) but insufficient coins (< 300 G)
    test_game.vehicle.levels["capacity"] = 3
    test_game.vehicle.coins = 100
    test_game.handle_event(click_titan)
    assert test_game.vehicle.vehicle_type == "standard", "Locked chassis must not unlock without enough coins!"

    # 3) Provide enough coins (350 G) -> should unlock, deduct 300 G, and equip 'titan'
    test_game.vehicle.coins = 350
    test_game.handle_event(click_titan)
    assert test_game.vehicle.vehicle_type == "titan", "Titan must be unlocked and equipped!"
    assert test_game.vehicle.coins == 50, f"Expected 50 coins remaining after 300 G purchase, got {test_game.vehicle.coins}"
    assert "titan" in test_game.vehicle.unlocked_types

    # Switch to tab_drill and test 'diamond' drill head unlock (requires 3 diamonds & power Lv.2+ & 450 G)
    click_drill_tab = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["tab_drill"].center)
    test_game.handle_event(click_drill_tab)
    assert test_game.garage_tab == "drill"
    test_game.draw()

    click_diamond = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["drill_diamond"].center)
    test_game.handle_event(click_diamond)
    assert test_game.vehicle.drill_head == "spiral", "Diamond drill must remain locked before collecting 3 diamonds!"

    test_game.vehicle.total_diamonds_collected = 3
    test_game.vehicle.levels["power"] = 2
    test_game.vehicle.coins = 500
    test_game.handle_event(click_diamond)
    assert test_game.vehicle.drill_head == "diamond", "Diamond drill must unlock and equip once conditions + coins are met!"
    assert test_game.vehicle.coins == 50
    assert "diamond" in test_game.vehicle.unlocked_drills

    # Click apply -> returns to SHOP
    assert "apply" in test_game.buttons
    click_apply = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["apply"].center)
    test_game.handle_event(click_apply)
    assert test_game.state == "shop", "Must return to previous state (SHOP) after apply!"
    print("  -> Garage surface shop access, progression conditions, and coin purchases verified OK.")

    # Test 10: Customization & Unlocks Save & Load Persistence
    print("Testing Customization & Unlocks Save & Load Persistence...")
    test_game.vehicle.max_depth_reached = 42
    test_game.vehicle.unlocked_colors.add("carbon")
    test_game.vehicle.color_id = "carbon"
    test_game.vehicle.recalc_stats()
    test_game.save_and_quit()

    loaded_game = Game(screen)
    loaded_game.load_game()
    assert loaded_game.vehicle.color_id == "carbon"
    assert loaded_game.vehicle.vehicle_type == "titan"
    assert loaded_game.vehicle.drill_head == "diamond"
    assert loaded_game.vehicle.max_depth_reached == 42
    assert loaded_game.vehicle.total_diamonds_collected == 3
    assert "titan" in loaded_game.vehicle.unlocked_types
    assert "diamond" in loaded_game.vehicle.unlocked_drills

    # Starting a brand new game must reset to default starter loadout
    fresh_game = Game(screen)
    fresh_game.new_game()
    assert fresh_game.vehicle.color_id == "yellow"
    assert fresh_game.vehicle.vehicle_type == "standard"
    assert fresh_game.vehicle.drill_head == "spiral"
    print("  -> Customization & unlock progression saved, restored, and reset on new game accurately.")

    # Test 11: Classic Endless Mode & Floor Unlocking
    print("Testing Classic Endless Mode & Floor Unlocking...")
    c_game = Game(screen)
    c_game.new_game_classic()
    assert c_game.game_mode == "classic"
    assert c_game.unlocked_floor == 1
    assert c_game.mission is None

    # Verify barrier placement at Floor 1 max_depth (depth 20 -> row 23)
    b_row_flr1 = S.SURFACE_ROW + S.CLASSIC_FLOORS[0]["max_depth"]
    for c in range(S.COLS):
        assert c_game.world.tiles[b_row_flr1][c] == S.T_BARRIER, f"Row {b_row_flr1} col {c} must be T_BARRIER"
        assert c_game.world.is_solid(c, b_row_flr1), f"Row {b_row_flr1} must be solid"

    # Vehicle trying to drill barrier cannot break it
    c_game.vehicle.x = 2 * S.TILE
    c_game.vehicle.y = (b_row_flr1 - 1) * S.TILE
    c_game.vehicle.update(0.016, c_game.world, (0, 1), c_game.particles)
    assert not c_game.vehicle.is_drilling, "Drilling barrier must be blocked!"
    assert c_game.world.tiles[b_row_flr1][2] == S.T_BARRIER

    # Near barrier detection
    barrier_detected = c_game.get_barrier_near_vehicle()
    assert barrier_detected is not None
    next_floor_num, flr_info, b_row = barrier_detected
    assert next_floor_num == 2
    assert b_row == b_row_flr1

    # Insufficient funds to unlock floor 2
    c_game.vehicle.coins = 50
    cost_flr2 = flr_info["unlock_cost"]
    assert not c_game.unlock_next_floor()
    assert c_game.unlocked_floor == 1
    assert c_game.world.tiles[b_row_flr1][2] == S.T_BARRIER

    # Give enough coins and unlock floor 2
    c_game.vehicle.coins = cost_flr2 + 100
    res_unlock = c_game.unlock_next_floor()
    assert res_unlock
    assert c_game.unlocked_floor == 2
    assert c_game.vehicle.coins == 100
    for c in range(S.COLS):
        assert c_game.world.tiles[b_row_flr1][c] == S.T_EMPTY, f"Row {b_row_flr1} must now be opened (T_EMPTY)"

    # Test Shop floor tab rendering & verify all rects stay strictly inside shop panel
    c_game.shop_tab = "floor"
    shop_buttons = ui.draw_shop_menu(screen, c_game.vehicle, (100, 100),
                                     game_mode=c_game.game_mode,
                                     unlocked_floor=c_game.unlocked_floor,
                                     active_tab=c_game.shop_tab)
    assert "tab_floor" in shop_buttons
    assert "unlock_floor" in shop_buttons
    shop_panel_rect = pygame.Rect(S.SCREEN_W // 2 - 260, 60, 520, 580)
    for bkey, brect in shop_buttons.items():
        assert shop_panel_rect.contains(brect), f"Shop button '{bkey}' {brect} overflows shop panel {shop_panel_rect}!"

    # Test Save & Load persistence for Classic Mode
    c_game.save_and_quit()
    c_loaded = Game(screen)
    c_loaded.load_game()
    assert c_loaded.game_mode == "classic"
    assert c_loaded.unlocked_floor == 2
    assert c_loaded.world.tiles[b_row_flr1][2] == S.T_EMPTY
    # Next barrier (Floor 2 max depth: 45 -> row 48) should still be locked
    b_row_flr2 = S.SURFACE_ROW + S.CLASSIC_FLOORS[1]["max_depth"]
    assert c_loaded.world.tiles[b_row_flr2][2] == S.T_BARRIER

    # Verify Floor 7 is the final floor and continuous endless mining afterwards
    assert getattr(S, "MAX_CLASSIC_FLOORS", 7) == 7
    assert len(S.CLASSIC_FLOORS) == 7
    assert S.CLASSIC_FLOORS[6]["floor"] == 7
    c_game.unlocked_floor = 6
    c_game.vehicle.coins = 5000
    assert c_game.unlock_next_floor(), "Should unlock Floor 7 successfully"
    assert c_game.unlocked_floor == 7
    assert not c_game.unlock_next_floor(), "Floor 7 is the final floor; no further unlocks permitted"
    assert c_game.get_barrier_near_vehicle() is None, "No barriers should be detected when Floor 7 is unlocked"

    # Verify no barriers exist anywhere in Floor 7 or below (continuous blocks)
    for r in range(S.SURFACE_ROW + 201, min(c_game.world.rows, S.SURFACE_ROW + 350)):
        for c in range(S.COLS):
            assert c_game.world.tiles[r][c] != S.T_BARRIER, f"Row {r} col {c} in Floor 7 must not be T_BARRIER"

    # Verify Shop floor tab shows completed state without unlock button
    c_game.shop_tab = "floor"
    shop_buttons_f7 = ui.draw_shop_menu(screen, c_game.vehicle, (100, 100),
                                        game_mode=c_game.game_mode,
                                        unlocked_floor=7,
                                        active_tab="floor")
    assert "close" in shop_buttons_f7
    assert "unlock_floor" not in shop_buttons_f7, "Unlock button must not be present when all floors are unlocked"

    # Verify HUD shows completed state
    ui.draw_hud(screen, c_game.vehicle, depth=250, mouse_pos=(100, 100),
                game_mode="classic", unlocked_floor=7)

    print("  -> Classic mode barrier mechanics, unlock flow, Floor 7 final cap, and persistence verified OK.")

    # ==================== Test HUD Cleanliness, Stalled Behavior, Dive Count & Vector Goal Icons ====================
    print("Testing HUD Cleanliness, Stalled Behavior, Single-Count Gravity Slam & Vector Goal Icons...")
    hud_buttons = ui.draw_hud(screen, c_game.vehicle, depth=100,
                              mouse_pos=(100, 100),
                              game_mode=c_game.game_mode,
                              unlocked_floor=c_game.unlocked_floor)
    assert "drone" not in hud_buttons, "HUD must not provide removed 'drone' button"
    assert "shop" not in hud_buttons, "HUD must not provide removed remote 'shop' button"

    import missions as M
    for gkey in ["diamonds", "gold", "depth", "drill_lv", "tier", "coins", "fuel", "dives"]:
        lbl = M.format_goal_label(gkey, 5)
        prog = M.format_goal_progress(gkey, 2, 5)
        ui.draw_icon_goal(screen, gkey, (10, 10, 16, 16))
        for bad_ch in ["💎", "🪙", "⬇️", "⛏", "📦", "💰", "⛽", "💥"]:
            assert bad_ch not in lbl and bad_ch not in prog, f"Emoji found in mission text for {gkey}"

    # Verify Gravity Slam counts only once per dive impact across multiple drilling frames
    m_dive = Game(screen)
    m_dive.new_game()
    col_d, row_d = m_dive.vehicle.grid_pos()
    m_dive.world.tiles[row_d + 1][col_d] = S.T_ROCK
    m_dive.world.hp[row_d + 1][col_d] = 18.0
    m_dive.world.max_hp[row_d + 1][col_d] = 18.0
    m_dive.vehicle.levels["power"] = 2
    m_dive.vehicle.recalc_stats()
    m_dive.vehicle.grav_charge = 1.0
    dive_counter = [0]
    m_dive.vehicle.on_dive_performed = lambda: dive_counter.__setitem__(0, dive_counter[0] + 1)
    for _ in range(15):
        m_dive.vehicle.update(0.016, m_dive.world, (0, 1), m_dive.particles, shift_pressed=True)
    assert dive_counter[0] == 1, f"Expected 1 dive count per slam impact, got {dive_counter[0]}"

    # Verify Mission Mode stalled state underground triggers GAME_OVER
    m_dive.vehicle.y = (S.SURFACE_ROW + 15) * S.TILE
    m_dive.vehicle.energy = 0.0
    m_dive.vehicle.stalled = True
    m_dive.update(0.016)
    assert m_dive.state == "game_over", "Mission mode must trigger GAME_OVER when stalled underground"

    # Verify Classic Mode stalled state underground also triggers GAME_OVER
    c_game.state = PLAYING
    c_game.vehicle.y = (S.SURFACE_ROW + 20) * S.TILE
    c_game.vehicle.coins = 0
    c_game.vehicle.cargo = {S.RES_COIN: 0, S.RES_GOLD: 0, S.RES_DIAMOND: 0}
    c_game.vehicle.cargo_count = 0
    c_game.vehicle.energy = 0.0
    c_game.vehicle.stalled = True
    c_game.update(0.016)
    assert c_game.state == "game_over", "Classic mode must also trigger GAME_OVER when stalled underground"
    print("  -> HUD cleanliness, stalled behavior, single-count Gravity Slam, and vector goal icons verified OK.")

    # ==================== Test 12: Contiguous Drill Raycast (No Phantom Damage on Floating Blocks) ====================
    print("Testing Contiguous Drill Raycast & Floating Block Protection...")
    from particles import ParticleSystem
    from world import World
    w_test = World()
    ps_test = ParticleSystem()
    v_aoe = Vehicle(4, 5, drill_head="seismic")  # drill_reach = 2
    assert v_aoe.drill_reach >= 2

    # จัดเตรียมแถวทดสอบที่ row 6:
    # col 4: บล็อกหลัก (SOLID DIRT)
    # col 5: ช่องว่างอากาศ (EMPTY AIR)
    # col 6: บล็อกลอยเดี่ยวๆ (FLOATING DIRT)
    # col 3: บล็อกติดกันฝั่งซ้าย (ADJACENT CONNECTED DIRT)
    w_test.tiles[6][4] = S.T_DIRT
    w_test.hp[6][4] = 10.0
    w_test.max_hp[6][4] = 10.0

    w_test.tiles[6][5] = S.T_EMPTY
    w_test.hp[6][5] = 0.0

    w_test.tiles[6][6] = S.T_DIRT
    w_test.hp[6][6] = 10.0
    w_test.max_hp[6][6] = 10.0

    w_test.tiles[6][3] = S.T_DIRT
    w_test.hp[6][3] = 10.0
    w_test.max_hp[6][3] = 10.0

    v_aoe.facing = (0, 1)  # เจาะลงล่าง -> perp_axis = "x" (กระจายแนวนอน)
    v_aoe._handle_drilling(4, 6, w_test, 0.5, ps_test)

    # 1. บล็อกหลักต้องโดนดาเมจ
    assert w_test.hp[6][4] < 10.0, "Main target block must take damage"
    # 2. บล็อกติดกัน (col 3) ต้องโดนดาเมจเพราะเชื่อมต่อกัน
    assert w_test.hp[6][3] < 10.0, "Directly connected adjacent block must take damage"
    # 3. บล็อกลอย (col 6) ต้องไม่โดนดาเมจเลย เพราะมีอากาศคั่นกลางที่ col 5!
    assert w_test.hp[6][6] == 10.0, "Floating isolated block across empty air must NOT take damage!"
    print("  -> Contiguous drill raycast verified OK (isolated blocks protected from phantom damage).")

    # Clean up test save
    if SM.save_exists():
        SM.delete_save()

    pygame.quit()
    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_tests()

