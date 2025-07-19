import logging

import dearpygui.dearpygui as dpg

from Code.tools import TimerManager, ViewportResizeManager

logger = logging.getLogger(__name__)


class BaseWindow:
    _tag = ""
    _viewport_resize_tag = ""
    _timer_tag = ""

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None: ...

    @classmethod
    def _invoce_resize(cls) -> None:
        app_data = (
            dpg.get_viewport_width(),
            dpg.get_viewport_height(),
            dpg.get_viewport_client_width(),
            dpg.get_viewport_client_height(),
        )

        try:
            cls._on_resize(app_data)

        except Exception as e:
            logger.error(f"Error in callback: {e}")

    @classmethod
    def _on_del(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.delete_item(cls._tag)

        ViewportResizeManager.remove_callback(cls._tag)
        TimerManager.remove_timer(cls._tag)

    @classmethod
    def _setup_resize(cls) -> None:
        ViewportResizeManager.add_callback(cls._tag, cls._on_resize)

    @classmethod
    def create(cls) -> None: ...

    @classmethod
    def focus(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.focus_item(cls._tag)

    @classmethod
    def delete(cls) -> None:
        cls._on_del()
