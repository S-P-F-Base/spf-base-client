import logging

import dearpygui.dearpygui as dpg

from Code.tools import APIManager

from .base_window import BaseWindow

logger = logging.getLogger(__name__)


class UserAccessPanel(BaseWindow):
    _tag = "WindowUserAccessPanel"
    _user_list = []
    _group_ids = []

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

        if dpg.does_item_exist("search_input"):
            dpg.set_item_width("search_input", window_width - 16)

        window_width_btn = window_width - 30
        for item in cls._group_ids:
            btns = dpg.get_item_children(item, 1)
            if not btns:
                continue

            for btn in btns:
                dpg.set_item_width(btn, window_width_btn // 3)

    @classmethod
    def _on_search(cls, sender, app_data, user_data) -> None:
        search = app_data.strip().lower()

        for group_id in cls._group_ids:
            buttons = dpg.get_item_children(group_id, 1)
            if not buttons:
                continue

            visible = False
            for btn in buttons:
                label = dpg.get_item_label(btn).lower()  # type: ignore
                has = search in label

                dpg.configure_item(btn, show=has)
                if has:
                    visible = True

            dpg.configure_item(group_id, show=visible)

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
            no_scrollbar=True,
        ):
            dpg.add_text("Управление пользователями")
            dpg.add_separator()

            dpg.add_input_text(
                hint="Поиск...",
                callback=cls._on_search,
                tag="search_input",
            )

            dpg.add_separator()
            cur_item = 0
            cur_group = dpg.add_group(horizontal=True, parent=cls._tag)
            cls._group_ids.append(cur_group)
            for item in cls._user_list:
                if cur_item >= 3:
                    cur_group = dpg.add_group(horizontal=True, parent=cls._tag)
                    cls._group_ids.append(cur_group)
                    cur_item = 0

                dpg.add_button(label=item, user_data=item, parent=cur_group)
                cur_item += 1

        cls._setup_resize()
