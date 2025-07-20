import atexit

import dearpygui.dearpygui as dpg

from Code.tools import (
    APIManager,
    Config,
    FontManager,
    TextureManager,
    TimerManager,
    ViewportResizeManager,
)

from .windows import WindowAuth, WindowLeftPanel


class Core:
    @classmethod
    def _setup(cls) -> None:
        dpg.create_context()
        dpg.create_viewport(
            title="S.P.F. Base client",
            width=600,
            height=300,
        )

        FontManager.load_fonts()
        TextureManager.load_static_img()

        Config.load()
        atexit.register(Config.save)

        TimerManager.initialize()
        atexit.register(TimerManager.stop)

        APIManager.setup()

        dpg.set_viewport_resize_callback(ViewportResizeManager.invoke)

        if APIManager.try_auth_viva_refresh():
            APIManager.update_cur_user()
            WindowLeftPanel.create()
        else:
            WindowAuth.create()

        dpg.setup_dearpygui()
        dpg.show_viewport()

    @classmethod
    def run(cls) -> None:
        cls._setup()
        dpg.start_dearpygui()
        dpg.destroy_context()

    @classmethod
    def stop(cls) -> None:
        dpg.stop_dearpygui()
