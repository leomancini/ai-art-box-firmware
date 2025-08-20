#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any

import pygame


def _default_labels() -> Dict[str, List[str]]:
    values = [str(i) for i in range(6)]
    return {"first": values.copy(), "second": values.copy(), "third": values.copy()}


def _coerce_string_list(values: Any, expected_len: int = 6) -> Optional[List[str]]:
    if not isinstance(values, list) or len(values) != expected_len:
        return None
    coerced: List[str] = [str(v) for v in values]
    return coerced


def load_labels_file(path: Path) -> Dict[str, List[str]]:
    """
    Load labels from JSON in one of the forms:
      1) {"first": [..6..], "second": [..6..], "third": [..6..]}
      2) [ [..6..], [..6..], [..6..] ]   # first, second, third
      3) {"0": [..6..], "1": [..6..], "2": [..6..]}
    Returns default numeric labels on any validation failure.
    """
    import json
    import re

    default = _default_labels()
    raw_text: str
    try:
        raw_text = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Failed to read labels file '{path}': {exc}", file=sys.stderr)
        return default

    data: Any
    try:
        # Try parse as pure JSON first
        data = json.loads(raw_text)
    except Exception:
        # Try to extract an array from JS like: const slotOptions = [ ... ];
        try:
            # Find first '[' and last ']' to capture the array literal
            start_idx = raw_text.find("[")
            end_idx = raw_text.rfind("]")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                array_text = raw_text[start_idx : end_idx + 1]
                data = json.loads(array_text)
            else:
                raise ValueError("No JSON array found in labels file")
        except Exception as exc2:
            print(f"Labels file '{path}' not valid JSON/JS array: {exc2}. Using defaults.", file=sys.stderr)
            return default

    # Case 1: dict with first/second/third (case-insensitive)
    if isinstance(data, dict):
        lowered = {str(k).lower(): v for k, v in data.items()}
        if {"first", "second", "third"}.issubset(lowered.keys()):
            first = _coerce_string_list(lowered.get("first"))
            second = _coerce_string_list(lowered.get("second"))
            third = _coerce_string_list(lowered.get("third"))
            if first and second and third:
                return {"first": first, "second": second, "third": third}

        # Case 3: dict with "0","1","2"
        if {"0", "1", "2"}.issubset(lowered.keys()):
            first = _coerce_string_list(lowered.get("0"))
            second = _coerce_string_list(lowered.get("1"))
            third = _coerce_string_list(lowered.get("2"))
            if first and second and third:
                return {"first": first, "second": second, "third": third}

    # Case 2: list of three lists
    if isinstance(data, list) and len(data) == 3:
        first = _coerce_string_list(data[0])
        second = _coerce_string_list(data[1])
        third = _coerce_string_list(data[2])
        if first and second and third:
            return {"first": first, "second": second, "third": third}

    print(f"Labels file '{path}' is not in a recognized format; using defaults.", file=sys.stderr)
    return default


class PygameImageViewer:
    """
    Image viewer using Pygame, mapping keyboard groups to three digits (0..5) to
    load files named "d0-d1-d2.jpeg" from a directory. Keys:

    - First digit:  Q W E R T Y → 0..5
    - Second digit: A S D F G H → 0..5
    - Third digit:  Z X C V B N → 0..5
    """

    def __init__(self, images_directory: Path, window_size: Tuple[int, int], labels: Optional[Dict[str, List[str]]] = None) -> None:
        self.images_directory: Path = images_directory
        self.window_width, self.window_height = window_size

        self.first_digit: int = 0
        self.second_digit: int = 0
        self.third_digit: int = 0

        self.labels: Dict[str, List[str]] = labels if labels is not None else _default_labels()

        self.key_to_digit_mapping: Dict[int, Tuple[int, int]] = self._build_key_mapping()
        self.surface_cache: Dict[Path, pygame.Surface] = {}

        pygame.init()
        pygame.display.set_caption("AI Art Box Viewer (Pygame)")
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        
        # Set custom window icon
        try:
            icon_path = get_resource_path("AI_Art_Box_Viewer.icns")
            if icon_path.exists():
                # For .icns files, we need to convert to a format pygame can use
                # Let's create a simple icon from the icon generation script
                icon_surface = self._create_icon_surface()
                pygame.display.set_icon(icon_surface)
        except Exception as e:
            print(f"Could not set custom icon: {e}", file=sys.stderr)
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        
        # Crossfade settings
        self.enable_crossfade: bool = True
        self.crossfade_duration: float = 0.3  # seconds
        self.crossfade_fps: int = 60
        self._last_scaled_surface: Optional[pygame.Surface] = None
        self._last_blit_rect: Optional[pygame.Rect] = None

        self._render()

    @staticmethod
    def _build_key_mapping() -> Dict[int, Tuple[int, int]]:
        mapping: Dict[int, Tuple[int, int]] = {}

        first_keys = "qwerty"
        second_keys = "asdfgh"
        third_keys = "zxcvbn"

        for value, char in enumerate(first_keys):
            mapping[getattr(pygame, f"K_{char}")] = (0, value)

        for value, char in enumerate(second_keys):
            mapping[getattr(pygame, f"K_{char}")] = (1, value)

        for value, char in enumerate(third_keys):
            mapping[getattr(pygame, f"K_{char}")] = (2, value)

        return mapping

    def _create_icon_surface(self) -> pygame.Surface:
        """Create a pygame surface for the window icon from the custom icon"""
        try:
            # Try to load the custom icon file
            icon_path = get_resource_path("Mac App Icon.jpeg")
            if icon_path.exists():
                # Load the original jpeg and scale it down
                icon_size = 32
                original_surface = pygame.image.load(str(icon_path))
                scaled_surface = pygame.transform.scale(original_surface, (icon_size, icon_size))
                return scaled_surface
        except Exception as e:
            print(f"Could not load custom icon: {e}")
        
        # Fallback: create a simple icon
        icon_size = 32
        surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        surface.fill((40, 44, 52, 255))
        border_width = 1
        pygame.draw.rect(surface, (100, 150, 255, 255), 
                        (border_width, border_width, icon_size - 2*border_width, icon_size - 2*border_width), 
                        border_width)
        return surface

    def _current_filename(self) -> str:
        return f"{self.first_digit}-{self.second_digit}-{self.third_digit}.jpeg"

    def _current_image_path(self) -> Path:
        return self.images_directory / self._current_filename()

    def _load_surface(self, path: Path) -> Optional[pygame.Surface]:
        if path in self.surface_cache:
            return self.surface_cache[path]
        if not path.exists():
            return None
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
            self.surface_cache[path] = surface
            return surface
        except Exception as exc:
            print(f"Failed to load image '{path}': {exc}", file=sys.stderr)
            return None

    def _render(self) -> None:
        self.screen.fill((0, 0, 0))

        image_path = self._current_image_path()
        surface = self._load_surface(image_path)

        if surface is None:
            message = f"Missing: {image_path.name}"
            text_surface = self.font.render(message, True, (220, 220, 220))
            rect = text_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(text_surface, rect)
            pygame.display.set_caption(f"AI Art Box Viewer (Pygame) — {self._current_filename()}")
            pygame.display.flip()
            # Do not update last surface on missing image
            return

        scaled_surface, blit_rect = self._get_scaled_surface_and_rect(surface)

        performed_crossfade = False
        if self.enable_crossfade and self._last_scaled_surface is not None and self._last_blit_rect is not None:
            try:
                self._crossfade(self._last_scaled_surface, self._last_blit_rect, scaled_surface, blit_rect)
                performed_crossfade = True
            except Exception:
                performed_crossfade = False

        if not performed_crossfade:
            self.screen.fill((0, 0, 0))
            self.screen.blit(scaled_surface, blit_rect)
            pygame.display.set_caption(f"AI Art Box Viewer (Pygame) — {self._current_filename()}")
            self._draw_labels_overlay()
            pygame.display.flip()

        # Cache for next transition
        self._last_scaled_surface = scaled_surface
        self._last_blit_rect = blit_rect

    def _get_scaled_surface_and_rect(self, surface: pygame.Surface) -> Tuple[pygame.Surface, pygame.Rect]:
        target_w, target_h = self.screen.get_size()
        img_w, img_h = surface.get_size()
        scale = min(target_w / img_w, target_h / img_h)
        scaled_w = max(1, int(img_w * scale))
        scaled_h = max(1, int(img_h * scale))
        scaled_surface = pygame.transform.smoothscale(surface, (scaled_w, scaled_h))
        blit_rect = scaled_surface.get_rect(center=(target_w // 2, target_h // 2))
        return scaled_surface, blit_rect

    def _crossfade(self, old_surface: pygame.Surface, old_rect: pygame.Rect, new_surface: pygame.Surface, new_rect: pygame.Rect) -> None:
        duration = max(0.0, float(self.crossfade_duration))
        if duration == 0:
            self.screen.fill((0, 0, 0))
            self.screen.blit(new_surface, new_rect)
            pygame.display.set_caption(f"AI Art Box Viewer (Pygame) — {self._current_filename()}")
            self._draw_labels_overlay()
            pygame.display.flip()
            return
        frames = max(1, int(self.crossfade_fps * duration))
        for i in range(frames + 1):
            alpha = int(255 * (i / frames))
            self.screen.fill((0, 0, 0))
            self.screen.blit(old_surface, old_rect)
            if alpha >= 255:
                self.screen.blit(new_surface, new_rect)
            else:
                temp = new_surface.copy()
                temp.set_alpha(alpha)
                self.screen.blit(temp, new_rect)
            pygame.display.set_caption(f"AI Art Box Viewer (Pygame) — {self._current_filename()}")
            self._draw_labels_overlay()
            pygame.display.flip()
            pygame.event.pump()
            self.clock.tick(self.crossfade_fps)

    def _draw_labels_overlay(self) -> None:
        lines = [
            self.labels['first'][self.first_digit],
            self.labels['second'][self.second_digit],
            self.labels['third'][self.third_digit],
        ]

        text_surfaces: List[pygame.Surface] = [self.font.render(line, True, (240, 240, 240)) for line in lines]
        padding = 10
        gap = 4
        widths = [s.get_width() for s in text_surfaces]
        fixed_line_height = self.font.get_height()
        box_w = max(widths) + padding * 2
        box_h = len(text_surfaces) * fixed_line_height + gap * (len(text_surfaces) - 1) + padding * 2

        box_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surface.fill((0, 0, 0, 160))

        for idx, s in enumerate(text_surfaces):
            y = padding + idx * (fixed_line_height + gap)
            # Center text vertically within the fixed row height
            y_offset = max(0, (fixed_line_height - s.get_height()) // 2)
            box_surface.blit(s, (padding, y + y_offset))

        # Top-left corner placement
        self.screen.blit(box_surface, (10, 10))

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    # Reset crossfade cache on resize
                    self._last_scaled_surface = None
                    self._last_blit_rect = None
                    self._render()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE,):
                        running = False
                    elif event.key in self.key_to_digit_mapping:
                        digit_index, digit_value = self.key_to_digit_mapping[event.key]
                        if digit_index == 0:
                            self.first_digit = digit_value
                        elif digit_index == 1:
                            self.second_digit = digit_value
                        else:
                            self.third_digit = digit_value
                        self._render()

            self.clock.tick(60)

        pygame.quit()


def get_resource_path(relative_path: str) -> Path:
    """Get the absolute path to a resource file, works for both development and bundled app"""
    if hasattr(sys, '_MEIPASS'):
        # Running in a bundled app (PyInstaller)
        return Path(sys._MEIPASS) / relative_path
    elif hasattr(sys, 'frozen'):
        # Running in a bundled app (py2app)
        # sys.executable points to the MacOS binary, so we need to go up to Resources
        bundle_dir = Path(sys.executable).parent.parent / 'Resources'
        return bundle_dir / relative_path
    else:
        # Running in development
        return Path(__file__).parent / relative_path

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pygame viewer for 'd0-d1-d2.jpeg' images with QWERTY/ASDFGH/ZXCVBN controls.")
    parser.add_argument(
        "--images",
        type=str,
        default=str(get_resource_path("images")),
        help="Directory containing 216 jpegs named like '0-0-0.jpeg' ... '5-5-5.jpeg'",
    )
    parser.add_argument("--width", type=int, default=1024, help="Initial window width")
    parser.add_argument("--height", type=int, default=768, help="Initial window height")
    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help=(
            "Path to labels file. Formats supported: "
            "{'first':[...6...],'second':[...6...],'third':[...6...]}, "
            "[['..6..'],['..6..'],['..6..']], or {'0':[...],'1':[...],'2':[...]} "
            "or a JS file containing a const like: const slotOptions = [[...],[...],[...]];"
        ),
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    images_directory = Path(args.images).expanduser().resolve()
    if not images_directory.exists():
        print(
            f"Image directory does not exist: {images_directory}\n"
            "Create it and add files like '0-0-0.jpeg', or pass a different path via --images.",
            file=sys.stderr,
        )
        sys.exit(1)

    labels_data: Optional[Dict[str, List[str]]] = None
    # Determine labels path, preferring explicit flag
    candidate_paths: List[Path] = []
    if args.labels:
        candidate_paths.append(Path(args.labels).expanduser().resolve())
    else:
        # Try common defaults in images dir then script dir
        for base in (images_directory, get_resource_path(""), Path(__file__).parent):
            candidate_paths.append(base / "labels.json")
            candidate_paths.append(base / "labels.js")

    for candidate in candidate_paths:
        if candidate.exists():
            labels_data = load_labels_file(candidate)
            break
    if labels_data is None and args.labels:
        print(f"Labels file not found: {candidate_paths[0]}. Using defaults.", file=sys.stderr)

    app = PygameImageViewer(images_directory=images_directory, window_size=(args.width, args.height), labels=labels_data)
    app.run()


if __name__ == "__main__":
    main()


