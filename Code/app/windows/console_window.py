import dearpygui.dearpygui as dpg

from Code.tools import APIManager

from .base_window import BaseWindow


class ConsolePanel(BaseWindow):
    _tag = "ConsolePanel"

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        _, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

    @classmethod
    def _send_debug_request(cls) -> None:
        method = dpg.get_value("debug_method")
        url = dpg.get_value("debug_url").strip()
        body_text = dpg.get_value("debug_body").strip()

        try:
            kwargs = {}
            if method == "POST" and body_text:
                import json

                kwargs["json"] = json.loads(body_text)

            result = APIManager._requests(method, url, **kwargs)
            dpg.set_value("debug_response", str(result))

        except Exception as e:
            dpg.set_value("debug_response", f"Ошибка: {str(e)}")

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
            dpg.add_text("URL (без https://spf-base.ru/):")
            dpg.add_input_text(tag="debug_url", width=600)

            dpg.add_text("Метод запроса:")
            dpg.add_combo(("GET", "POST"), default_value="GET", tag="debug_method")

            dpg.add_text("JSON тело запроса (только для POST):")
            dpg.add_input_text(tag="debug_body", multiline=True, height=100, width=600)

            dpg.add_button(label="Отправить запрос", callback=cls._send_debug_request)

            dpg.add_text("Ответ:", tag="debug_response_label")
            dpg.add_input_text(
                tag="debug_response",
                multiline=True,
                readonly=True,
                width=600,
                height=200,
            )
        super().create()
