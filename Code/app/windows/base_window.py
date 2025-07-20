import logging

import dearpygui.dearpygui as dpg

from Code.tools import TimerManager, ViewportResizeManager

logger = logging.getLogger(__name__)


class BaseWindow:
    _tag = ""
    _popup_tag = _tag + "_popup"
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

    # region Popup
    @classmethod
    def _popup_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._popup_tag):
            return

        _, _, width, height = app_data
        window_width = int(width * 0.6)
        window_height = int(height * 0.4)
        dpg.set_item_pos(
            cls._popup_tag,
            [width // 2 - window_width // 2, height // 2 - window_height // 2],
        )
        dpg.set_item_width(cls._popup_tag, window_width)
        dpg.set_item_height(cls._popup_tag, window_height)

        margin_x = window_width * 0.05
        wrap = window_width - margin_x * 2

        if dpg.does_item_exist(cls._popup_tag + "_h"):
            header_size_x = dpg.get_text_size(dpg.get_value(cls._popup_tag + "_h"))[0]
            dpg.set_item_pos(
                cls._popup_tag + "_h",
                [window_width // 2 - header_size_x // 2, 0],
            )

        if dpg.does_item_exist(cls._popup_tag + "_t"):
            dpg.set_item_pos(cls._popup_tag + "_t", [margin_x, 28])
            dpg.configure_item(cls._popup_tag + "_t", wrap=wrap)

        if dpg.does_item_exist(cls._popup_tag + "_b"):
            dpg.set_item_pos(
                cls._popup_tag + "_b",
                [window_width - 38, window_height - 30],
            )

    @classmethod
    def _popup_del(cls) -> None:
        if dpg.does_item_exist(cls._popup_tag):
            dpg.delete_item(cls._popup_tag)

        ViewportResizeManager.remove_callback(cls._popup_tag)

    @classmethod
    def _summon_popup(cls, header: str, text: str) -> None:
        if dpg.does_item_exist(cls._popup_tag):
            dpg.delete_item(cls._popup_tag)

        with dpg.window(
            tag=cls._popup_tag,
            no_title_bar=True,
            modal=True,
            no_move=True,
            no_resize=True,
            no_scrollbar=True,
            on_close=cls._popup_del,
        ):
            dpg.add_text(header, wrap=0, tag=cls._popup_tag + "_h")
            dpg.add_text(text, wrap=0, tag=cls._popup_tag + "_t")
            dpg.add_button(
                label="Ок",
                callback=lambda: dpg.delete_item(cls._popup_tag),
                tag=cls._popup_tag + "_b",
            )

        dpg.render_dearpygui_frame()
        ViewportResizeManager.add_callback(cls._popup_tag, cls._popup_resize)

    # endregion
