import math

import dearpygui.dearpygui as dpg

from .config import Config
from .timer_manager import TimerManager


class ThemesManager:
    theme_att_id = 0

    @classmethod
    def load_themes(cls) -> None:
        with dpg.theme() as main:
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [170, 170, 170])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [51, 51, 55])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [51, 51, 55])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [51, 51, 55])

        with dpg.theme(tag="theme_attention"):
            with dpg.theme_component(dpg.mvButton):
                cls.theme_att_id = dpg.add_theme_color(
                    dpg.mvThemeCol_Button, (60, 60, 60, 255)
                )

        dpg.bind_theme(main)

        TimerManager.add_timer("theme_attention", cls._attention_theme_ch, 0.02)

    @classmethod
    def _lerp_color(
        cls,
        c1: list[int],
        c2: list[int],
        t: float,
    ) -> tuple[int, int, int, int]:
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))  # type: ignore

    @classmethod
    def _attention_theme_ch(cls) -> None:
        t = dpg.get_total_time()
        pulse = (math.sin(t * 2 * math.pi * 0.5) + 1) / 2

        base = [int(c * 0.6) if i < 3 else c for i, c in enumerate(Config.accent_color)]
        final = Config.accent_color

        color = cls._lerp_color(base, final, pulse)
        dpg.set_value(cls.theme_att_id, color)
