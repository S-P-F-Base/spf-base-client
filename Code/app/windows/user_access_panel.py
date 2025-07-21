import logging

import dearpygui.dearpygui as dpg

from Code.tools import APIManager

from .base_window import BaseWindow

logger = logging.getLogger(__name__)


class UserAccessPanel(BaseWindow):
    _tag = "WindowUserAccessPanel"
    _user_list = []

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        _, _, width, height = app_data
        window_width = width - int(width * 0.33)

        dpg.set_item_width(cls._tag, window_width)
        dpg.set_item_height(cls._tag, height)
        dpg.set_item_pos(cls._tag, [int(width * 0.33), 0])

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.focus_item(cls._tag)
            return

        cls._user_list = sorted(APIManager.user_control_get_all())

        with dpg.window(
            tag=cls._tag,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_del,
            pos=[0, 0],
        ):
            dpg.add_text(str(cls._user_list), wrap=0)

        cls._setup_resize()
