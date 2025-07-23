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

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

        if dpg.does_item_exist("log_page_btns_spaser"):
            dpg.set_item_width("log_page_btns_spaser", window_width - 50 - 32)

    @classmethod
    def _load_logs_by_range(cls, start_id: int, end_id: int) -> None:
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

                        dpg.add_text(str(val))
                        with dpg.tooltip(dpg.last_item()):
                            dpg.add_text(str(val))

    @classmethod
    def _get_20_log_entery(cls) -> None:
        anser = APIManager.logs.min_max_id()
        min_id, max_id = anser.values()
        if min_id is None or max_id is None:
            return

        cls._start_id = min_id
        cls._end_id = min(min_id + cls._page_size - 1, max_id)
        cls._load_logs_by_range(cls._start_id, cls._end_id)

    @classmethod
    def _change_page(cls, sender, app_data, user_data) -> None:
        if cls._start_id is None or cls._end_id is None:
            return

        if cls._max_id is None or cls._min_id is None:
            cls._min_id, cls._max_id = APIManager.logs.min_max_id().values()
            if cls._min_id is None or cls._max_id is None:
                return

        if user_data == "next":
            new_start = cls._end_id + 1
            new_end = new_start + cls._page_size - 1

            if new_start > cls._max_id:
                return

            if new_end > cls._max_id:
                new_end = cls._max_id

        else:
            new_end = cls._start_id - 1
            new_start = new_end - cls._page_size + 1

            if new_end < cls._min_id:
                return

            if new_start < cls._min_id:
                new_start = cls._min_id

        cls._start_id = new_start
        cls._end_id = new_end
        cls._load_logs_by_range(cls._start_id, cls._end_id)

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
            dpg.add_text("Логи сервера")
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

        cls._get_20_log_entery()
        super().create()
