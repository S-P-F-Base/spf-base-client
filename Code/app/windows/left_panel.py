import itertools
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass

import dearpygui.dearpygui as dpg

from Code.tools import (
    APIManager,
    Config,
    UserAccess,
    ViewportResizeManager,
    WebSocketClient,
)

from .base_window import BaseWindow
from .console_panel import ConsolePanel
from .logs_panel import LogPanel
from .lore_char_control_panel import LoreCharControlPanel
from .server_control_panel import ServerControlPanel
from .user_access_panel import UserAccessPanel


@dataclass
class _BtnInfo:
    name: str
    tag_postfix: str
    func: Callable[[], None] | None = None
    access: int = 0


class WindowLeftPanel(BaseWindow):
    _tag = "WindowLeftPanel"
    _btns_list = [
        _BtnInfo(
            "Управление правами",
            "_btn_user_access",
            UserAccessPanel.create,
            UserAccess.READ_USER.value | UserAccess.CONTROL_USER.value,
        ),
        _BtnInfo(
            "Управление сервером",
            "_btn_server_access",
            ServerControlPanel.create,
            UserAccess.READ_GAME_SERVER.value | UserAccess.CONTROL_GAME_SERVER.value,
        ),
        _BtnInfo(
            "Управление игроками",
            "_btn_player_control",
            None,
            UserAccess.READ_PLAYER.value | UserAccess.CONTROL_PLAYER.value,
        ),
        _BtnInfo(
            "Управление лорными персонажами",
            "_btn_char_control",
            LoreCharControlPanel.create,
            UserAccess.LORE_CHAR_CONTROL.value,
        ),
        _BtnInfo(
            "Оплата доната",
            "_btn_payment_give",
            None,
            UserAccess.READ_PAYMENT.value | UserAccess.GIVE_PAYMENT.value,
        ),
        _BtnInfo(
            "Управление донат услугами",
            "_btn_payment_access",
            None,
            UserAccess.READ_PAYMENT.value | UserAccess.CONTROL_PAYMENT.value,
        ),
        _BtnInfo(
            "Логи",
            "_btn_logs",
            LogPanel.create,
            UserAccess.READ_LOGS.value,
        ),
        _BtnInfo(
            "Консоль",
            "_btn_consol",
            ConsolePanel.create,
            UserAccess.ALL_ACCESS.value,
        ),
    ]

    _theme_names = [
        "theme_attention_0",
        "theme_attention_1",
        "theme_attention_2",
        "theme_attention_3",
        "theme_attention_4",
        "theme_attention_5",
        "theme_attention_4",
        "theme_attention_3",
        "theme_attention_2",
        "theme_attention_1",
    ]

    _theme_cycle = itertools.cycle(_theme_names)

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, window_height = cls._setup_window(app_data, [0.33, 1], [0, 0])

        margin_x = int(window_width - 16)
        init_pos_x, init_pos_y = 8, 8
        for item in cls._btns_list:
            tag = cls._tag + item.tag_postfix

            if dpg.does_item_exist(tag) and dpg.is_item_shown(tag):
                dpg.set_item_pos(tag, [init_pos_x, init_pos_y])
                dpg.set_item_width(tag, margin_x)

                init_pos_y += 22

        if dpg.does_item_exist(cls._tag + "_btn_logout"):
            dpg.set_item_pos(cls._tag + "_btn_logout", [8, window_height - 28])

    @classmethod
    def _logout(cls) -> None:
        cls._on_del()

        APIManager.auth.logout()
        WebSocketClient.disconnect()
        BaseWindow.close_all_windows()

        from .auth import WindowAuth

        WindowAuth.create()
        dpg.render_dearpygui_frame()
        ViewportResizeManager.invoke()

    @staticmethod
    def parse_version(v: str) -> tuple[int, ...]:
        v = v.removeprefix("v")
        return tuple(int(part) for part in v.split("."))

    @classmethod
    def create(cls) -> None:
        up_to_date_version = APIManager.download.version()
        if up_to_date_version is None:
            up_to_date_version = Config.app_version

        with dpg.window(
            tag=cls._tag,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_del,
            pos=[0, 0],
        ):
            for item in cls._btns_list:
                dpg.add_button(
                    label=item.name,
                    tag=cls._tag + item.tag_postfix,
                    callback=item.func,  # type: ignore
                    show=APIManager.has_access(item.access),
                    enabled=item.func is not None,
                )

            with dpg.group(horizontal=True, tag=cls._tag + "_btn_logout"):
                dpg.add_button(
                    label="Logout",
                    callback=cls._logout,
                )

                update_btn_id = dpg.add_button(
                    label="!",
                    show=cls.parse_version(Config.app_version)
                    < cls.parse_version(up_to_date_version),
                    callback=lambda: webbrowser.open_new_tab(
                        "https://spf-base.ru/download"
                    ),
                )
                if dpg.is_item_shown(update_btn_id):
                    with dpg.tooltip(update_btn_id):
                        dpg.add_text(f"Текущая версия приложения: {Config.app_version}")
                        dpg.add_text(
                            f"Доступная на сервере версия: {up_to_date_version}"
                        )

        dpg.bind_item_theme(update_btn_id, "theme_attention")
        super().create()
