import dearpygui.dearpygui as dpg

from .config import Config


class FontManager:
    @classmethod
    def load_fonts(cls):
        font_path = Config.get_data_dir_str() + "\\fonts\\Monocraft\\Monocraft.otf"

        with dpg.font_registry():
            with dpg.font(font_path, 13) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

                # Greek character range
                dpg.add_font_range(0x0391, 0x03C9)

                # Range of upper and lower numerical indices
                dpg.add_font_range(0x2070, 0x209F)

        dpg.bind_font(default_font)
