import dearpygui.dearpygui as dpg


class ThemesManager:
    @classmethod
    def load_themes(cls) -> None:
        with dpg.theme() as main:
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [170, 170, 170])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [51, 51, 55])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [51, 51, 55])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [51, 51, 55])

        dpg.bind_theme(main)
