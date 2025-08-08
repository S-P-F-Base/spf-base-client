from datetime import datetime

import dearpygui.dearpygui as dpg

from Code.tools import APIManager, LogType, LogTypeTranslate

from .base_window import BaseWindow


class LogPanel(BaseWindow):
    _tag = "LogPanel"
    _server_status = ""

    _start_id: int | None = None
    _end_id: int | None = None
    _page_size: int = 8
    _max_id = None
    _min_id = None

    _current_page: int = 1
    _total_pages: int = 1

    @classmethod
    def _shorten_string(cls, val: str, max_len: int = 50) -> str:
        if len(val) <= max_len:
            return val
        return val[: max_len - 3].rstrip() + "..."

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

        if dpg.does_item_exist("log_page_btns_spaser"):
            dpg.set_item_width("log_page_btns_spaser", window_width - 50 - 32)

    @classmethod
    def _load_logs_by_range(cls, start_id: int | None, end_id: int | None) -> None:
        if start_id is None or end_id is None:
            return

        logs = APIManager.logs.by_range(start_id, end_id)
        dpg.delete_item("log_table", children_only=True)

        for label in ["ID", "Тип", "Время", "Описание", "Вызвавший"]:
            dpg.add_table_column(label=label, parent="log_table")

        for log in logs:
            with dpg.table_row(parent="log_table"):
                for key in ["id", "type", "time", "value", "creator"]:
                    with dpg.table_cell():
                        val = log[key]

                        if key == "time" and isinstance(val, str):
                            dt = datetime.fromisoformat(val)
                            val = dt.strftime("%H:%M:%S %d.%m.%Y")
                        elif key == "type":
                            try:
                                type_name = LogType(val).name
                                val = LogTypeTranslate[type_name].value
                            except Exception:
                                val = str(val)
                        if key == "value":
                            dpg.add_text(cls._shorten_string(str(val)))
                        else:
                            dpg.add_text(str(val))

                        with dpg.tooltip(dpg.last_item()):
                            dpg.add_text(str(val), wrap=400)

    @classmethod
    def _update_pagination(cls) -> None:
        cls._min_id, cls._max_id = APIManager.logs.min_max_id().values()
        if cls._min_id is None or cls._max_id is None:
            cls._total_pages = 1
            cls._current_page = 1
            return

        total_logs = cls._max_id - cls._min_id + 1
        cls._total_pages = max(1, (total_logs + cls._page_size - 1) // cls._page_size)

        if cls._current_page > cls._total_pages:
            cls._current_page = cls._total_pages
        if cls._current_page < 1:
            cls._current_page = 1

    @classmethod
    def _load_logs_for_page(cls, page: int) -> None:
        cls._update_pagination()
        cls._current_page = page

        if cls._min_id is None or cls._max_id is None:
            return

        start_id = cls._min_id + (cls._current_page - 1) * cls._page_size
        end_id = min(start_id + cls._page_size - 1, cls._max_id)

        cls._start_id = start_id
        cls._end_id = end_id

        cls._load_logs_by_range(start_id, end_id)

        if dpg.does_item_exist("log_page_info"):
            dpg.set_value(
                "log_page_info",
                f"Логи сервера (Страница {cls._current_page}/{cls._total_pages})",
            )

    @classmethod
    def _change_page(cls, sender, app_data, user_data) -> None:
        cls._update_pagination()
        if user_data == "next" and cls._current_page < cls._total_pages:
            cls._load_logs_for_page(cls._current_page + 1)
        elif user_data == "prev" and cls._current_page > 1:
            cls._load_logs_for_page(cls._current_page - 1)

    @classmethod
    def _ref_log_id(cls) -> None:
        cls._update_pagination()
        cls._load_logs_for_page(cls._current_page)

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.focus_item(cls._tag)
            return

        with dpg.window(
            tag=cls._tag,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_del,
            pos=[0, 0],
            no_scrollbar=True,
        ):
            with dpg.group(horizontal=True):
                dpg.add_text(
                    f"Логи сервера (Страница {cls._current_page}/{cls._total_pages})",
                    tag="log_page_info",
                )
                dpg.add_button(label="Обновить логи", callback=cls._ref_log_id)

            with dpg.table(
                policy=dpg.mvTable_SizingStretchProp,
                borders_outerH=True,
                borders_innerV=True,
                borders_innerH=True,
                borders_outerV=True,
                tag="log_table",
            ):
                pass

            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="←", callback=cls._change_page, user_data="prev")
                dpg.add_spacer(tag="log_page_btns_spaser")
                dpg.add_button(label="→", callback=cls._change_page, user_data="next")

        cls._load_logs_for_page(1)
        super().create()
