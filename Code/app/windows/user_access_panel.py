import logging

import dearpygui.dearpygui as dpg

from Code.tools import APIError, APIManager, Config, UserAccess

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
    def update_user_list(cls) -> None:
        cls._user_list = sorted(APIManager.user_control_get_all() + ["SomeDude"])

    @classmethod
    def render_btns(cls) -> None:
        for item in cls._group_ids:
            if dpg.does_item_exist(item):
                dpg.delete_item(item)

        cur_item = 0
        cur_group = dpg.add_group(horizontal=True, parent=cls._tag)
        cls._group_ids.append(cur_group)
        for item in cls._user_list:
            if cur_item >= 3:
                cur_group = dpg.add_group(horizontal=True, parent=cls._tag)
                cls._group_ids.append(cur_group)
                cur_item = 0

            dpg.add_button(
                label=item,
                user_data=item,
                parent=cur_group,
                callback=lambda s, a, u: _UserInfoCard.create_user_card(u),
            )
            cur_item += 1

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.focus_item(cls._tag)
            return

        cls.update_user_list()

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
            cls.render_btns()

        cls._setup_resize()


class _UserInfoCard(BaseWindow):
    _tag = "_UserInfoCard"
    _cur_user = ""

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, window_hight = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

    @classmethod
    def render_access_checkboxes(
        cls,
        parent: str,
        access_value: int,
        prefix: str = "chk_",
    ) -> None:
        for access in UserAccess:
            if access == UserAccess.NO_ACCESS:
                continue

            dpg.add_checkbox(
                label=access.name.replace("_", " ").title(),
                tag=f"{prefix}{access.name}",
                default_value=bool(access_value & access.value),
                parent=parent,
            )

    @classmethod
    def collect_access_from_checkboxes(cls, prefix: str = "chk_") -> int:
        access_value = 0
        for access in UserAccess:
            if access == UserAccess.NO_ACCESS:
                continue

            tag = f"{prefix}{access.name}"
            if dpg.does_item_exist(tag) and dpg.get_value(tag):
                access_value |= access.value

        return access_value

    @classmethod
    def delete_user(cls, sender, app_data, user_data) -> None:
        if not (dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)):
            cls._summon_popup(
                "Ошибка",
                "Для того чтобы удалить пользователя необходимо зажать shift. Базовоая мера предосторожности.",
            )
            return

        logger.info("Ей... Ты удалил запись. Возможно")

        UserAccessPanel.update_user_list()
        UserAccessPanel.render_btns()
        cls._on_del()

    @classmethod
    def update_user(cls, sender, app_data, user_data) -> None:
        logger.info(cls.collect_access_from_checkboxes())

        cls._on_del()

    @classmethod
    def create_user_card(cls, login: str) -> None:
        cls._on_del()

        try:
            cls._cur_user = APIManager.user_control_get_info(login)

        except APIError as err:
            if err.code == 404:
                display_text = "Пользователь не найден"
            else:
                display_text = str(err)

            cls._summon_popup(
                "Ошибка получения данных",
                display_text,
            )
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
                dpg.add_text("Выбранный пользователь:")
                dpg.add_text(cls._cur_user["login"], color=Config.accent_color)

            dpg.add_separator()
            dpg.add_text("Нет. Это не будет переведено")
            with dpg.group(tag=cls._tag + "_access"):
                cls.render_access_checkboxes(
                    cls._tag + "_access",
                    cls._cur_user["access"],
                )

            dpg.add_separator()
            with dpg.group(horizontal=True, tag=cls._tag + "_btns"):
                dpg.add_button(
                    label="Обновить",
                    width=100,
                    callback=cls.update_user,
                )
                dpg.add_button(
                    label="Удалить",
                    width=100,
                    callback=cls.delete_user,
                )
                dpg.add_button(
                    label="Закрыть",
                    width=100,
                    callback=cls._on_del,
                )

        cls._setup_resize()
