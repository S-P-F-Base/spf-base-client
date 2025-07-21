import dearpygui.dearpygui as dpg

from Code.tools import APIManager, UserAccess, ViewportResizeManager

from .base_window import BaseWindow
from .user_access_panel import UserAccessPanel


class WindowLeftPanel(BaseWindow):
    _tag = "WindowLeftPanel"
    _btns_list = [
        (
            "Управление правами",
            "_btn_user_access",
            UserAccessPanel.create,
            UserAccess.READ_USER.value | UserAccess.CONTROL_USER.value,
        ),
        (
            "Управление сервером",
            "_btn_server_access",
            None,
            UserAccess.READ_GAME_SERVER.value | UserAccess.CONTROL_GAME_SERVER.value,
        ),
        (
            "Управление игроками",
            "_btn_player_control",
            None,
            UserAccess.READ_PLAYER.value | UserAccess.CONTROL_PLAYER.value,
        ),
        (
            "Оплата доната",
            "_btn_payment_give",
            None,
            UserAccess.READ_PAYMENT.value | UserAccess.GIVE_PAYMENT.value,
        ),
        (
            "Управление донат услугами",
            "_btn_payment_access",
            None,
            UserAccess.READ_PAYMENT.value | UserAccess.CONTROL_PAYMENT.value,
        ),
    ]

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        _, _, width, height = app_data
        window_width = width * 0.33

        dpg.set_item_width(cls._tag, int(window_width))
        dpg.set_item_height(cls._tag, height)

        margin_x = int(window_width - 16)
        init_pos_x, init_pos_y = 8, 8
        for item in cls._btns_list:
            _, tag_pref, _, _ = item
            tag = cls._tag + tag_pref

            if dpg.does_item_exist(tag) and dpg.is_item_shown(tag):
                dpg.set_item_pos(tag, [init_pos_x, init_pos_y])
                dpg.set_item_width(tag, margin_x)

                init_pos_y += 22

        if dpg.does_item_exist(cls._tag + "_btn_logout"):
            dpg.set_item_pos(cls._tag + "_btn_logout", [8, height - 28])

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
            for item in cls._btns_list:
                name, tag_pref, func, access = item
                dpg.add_button(
                    label=name,
                    tag=cls._tag + tag_pref,
                    callback=func,  # type: ignore
                    show=APIManager.has_access(access),
                )

            with dpg.group(horizontal=True, tag=cls._tag + "_btn_logout"):
                dpg.add_button(
                    label="Выйти",
                    callback=cls._logout,
                )
                dpg.add_button(label="?")

        cls._setup_resize()
