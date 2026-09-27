# -*- coding: utf-8 -*-
"""
assets.py
โหลดและจัดการรูปภาพ (Surface) และเสียงเอฟเฟกต์ (Sound) แบบรวมศูนย์และมีแคช
"""
import os
import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
SND_DIR = os.path.join(BASE_DIR, "assets", "sounds")

_IMAGES = {}
_SOUNDS = {}
_SOUND_ENABLED = True
_LAST_PLAYED = {}


def init():
    global _SOUND_ENABLED
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            _SOUND_ENABLED = True
        except Exception:
            _SOUND_ENABLED = False


def get_image(name):
    """โหลดรูปภาพจาก assets/images/{name} คืนค่า pygame.Surface"""
    if name in _IMAGES:
        return _IMAGES[name]

    if not name.endswith(".png"):
        filename = f"{name}.png"
    else:
        filename = name

    path = os.path.join(IMG_DIR, filename)
    if os.path.isfile(path):
        try:
            surf = pygame.image.load(path).convert_alpha()
            _IMAGES[name] = surf
            return surf
        except Exception as e:
            print(f"[assets] Error loading image {path}: {e}")

    # Fallback surface
    fallback = pygame.Surface((48, 48), pygame.SRCALPHA)
    fallback.fill((200, 50, 200, 200))
    _IMAGES[name] = fallback
    return fallback


def toggle_mute():
    """สลับระหว่างเปิด/ปิดเสียงทั้งหมด"""
    global _SOUND_ENABLED
    if not pygame.mixer.get_init():
        return
    _SOUND_ENABLED = not _SOUND_ENABLED
    vol = 0.0 if not _SOUND_ENABLED else 1.0
    pygame.mixer.music.set_volume(vol)


def is_muted():
    """คืนค่า True ถ้าเสียงถูกปิดอยู่"""
    return not _SOUND_ENABLED


def play_sound(name, volume=1.0, cooldown=0.06):
    """เล่นเสียงเอฟเฟกต์ มี cooldown ป้องกันเสียงเล่นซ้อนกันถี่เกินไป"""
    global _SOUND_ENABLED
    if not _SOUND_ENABLED:
        return

    now = pygame.time.get_ticks() / 1000.0
    if name in _LAST_PLAYED and (now - _LAST_PLAYED[name]) < cooldown:
        return
    _LAST_PLAYED[name] = now

    if name not in _SOUNDS:
        if not name.endswith(".wav"):
            filename = f"{name}.wav"
        else:
            filename = name
        path = os.path.join(SND_DIR, filename)
        if os.path.isfile(path):
            try:
                snd = pygame.mixer.Sound(path)
                _SOUNDS[name] = snd
            except Exception as e:
                print(f"[assets] Error loading sound {path}: {e}")
                return
        else:
            return

    snd = _SOUNDS.get(name)
    if snd:
        snd.set_volume(volume)
        snd.play()
