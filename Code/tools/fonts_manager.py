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
                
                # ←, →
                dpg.add_font_chars([0x2190, 0x2192])

        dpg.bind_font(default_font)
