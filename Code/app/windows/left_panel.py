import dearpygui.dearpygui as dpg

from Code.tools import APIManager, ViewportResizeManager

from .base_window import BaseWindow


class WindowLeftPanel(BaseWindow):
    _tag = "WindowLeftPanel"

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        _, _, width, height = app_data
        window_width = width * 0.22

        dpg.set_item_width(cls._tag, int(window_width))
        dpg.set_item_height(cls._tag, height)

    @classmethod
    def _logout(cls) -> None:
        cls._on_del()

        APIManager.logout()

        from .auth import WindowAuth

        WindowAuth.create()
        dpg.render_dearpygui_frame()
        ViewportResizeManager.invoke()

    @classmethod
    def create(cls) -> None:
        with dpg.window(
            tag=cls._tag,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_del,
            pos=[0, 0],
        ):
            dpg.add_text(str(APIManager.cur_user), wrap=0)
            dpg.add_button(label="Выйти", callback=cls._logout)

        cls._setup_resize()
