import dearpygui.dearpygui as dpg

from Code.tools import APIError, APIManager, TimerManager

from .base_window import BaseWindow

# Включен
# Включение
# Выключен
# Выключение


class ServerControlPanel(BaseWindow):
    _tag = "ServerControlPanel"
    _server_status = ""

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        _, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

    @classmethod
    def _set_btns_state(cls, enabled: bool) -> None:
        for tag in ["start_button", "stop_button"]:
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, enabled=enabled)

    @classmethod
    def _update_status(cls) -> None:
        try:
            cls._server_status = APIManager.server_control.status()["text"]
        except APIError as err:
            cls._summon_popup("Ошибка получения данных", f"Code: {err.code}; {err}")
            return

        if not dpg.does_item_exist("server_status_text"):
            return

        dpg.set_value("server_status_text", cls._server_status)

        if cls._server_status in ["Включен"]:
            color = [0, 255, 0]
            cls._set_btns_state(True)

        elif cls._server_status in ["Выключен"]:
            color = [255, 0, 0]
            cls._set_btns_state(True)

        elif cls._server_status in ["Включение", "Выключение"]:
            color = [255, 255, 0]
            cls._set_btns_state(False)

        else:
            color = [128, 128, 128]
            cls._set_btns_state(False)

        dpg.configure_item("server_status_text", color=color)

    @classmethod
    def _act(cls, sender, app_data, user_data) -> None:
        if cls._server_status == "Выключен" and user_data == "stop":
            cls._summon_popup(
                "Ошибка взаимодействия", "Вы не можете выключить выключенный сервер"
            )
            return

        if cls._server_status == "Включен" and user_data == "start":
            cls._summon_popup(
                "Ошибка взаимодействия", "Вы не можете включить включённый сервер"
            )
            return

        if user_data == "start":
            APIManager.server_control.start()

        elif user_data == "stop":
            APIManager.server_control.stop()

        cls._set_btns_state(False)

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
            dpg.add_text("Управление сервером")
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_text("Статус сервера")
                dpg.add_text(
                    "Загрузка данных...",
                    tag="server_status_text",
                    color=[255, 255, 0],
                )

            dpg.add_text(
                "В ввиду технических причин, включение и выключение сервера может занимать до 1 минуты.",
                wrap=0,
            )
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Запустить",
                    tag="start_button",
                    callback=cls._act,
                    user_data="start",
                )
                dpg.add_button(
                    label="Выключить",
                    tag="stop_button",
                    callback=cls._act,
                    user_data="stop",
                )

        TimerManager.add_timer(cls._tag, cls._update_status, 15)
        cls._update_status()
        super().create()
