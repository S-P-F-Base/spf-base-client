import re

import dearpygui.dearpygui as dpg

from Code.tools import APIManager

from .base_window import BaseWindow
from .left_panel import WindowLeftPanel


class WindowAuth(BaseWindow):
    _tag = "WindowAuth"
    _is_login: bool = True
    _see_password: bool = True

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        _, _, width, height = app_data

        # region img
        size = min(width, height)
        size = int(size * 0.5)
        if dpg.does_item_exist("logo_light"):
            dpg.configure_item(
                "logo_light",
                width=size * 2,
                height=size * 2,
                pos=[-size // 2, -size // 2],
            )

        if dpg.does_item_exist("logo"):
            dpg.configure_item(
                "logo",
                width=size,
                height=size,
            )
        # endregion

        width_middle = width // 2

        # region header
        if dpg.does_item_exist("text_header"):
            dpg.set_item_pos("text_header", [width_middle - 49, 0])
        # endregion

        # region input-text
        input_text_size = int(width * 0.6)
        input_text_size_half = input_text_size // 2
        temp = 28
        for item in ["login_text", "password_text", "password_text_2"]:
            if dpg.does_item_exist(item):
                dpg.set_item_width(item, input_text_size)
                dpg.set_item_pos(item, [width_middle - input_text_size_half, temp])
                dpg.show_item(item)

            temp += 22

        # endregion

        # region checkbox
        if dpg.does_item_exist("see_password"):
            dpg.set_item_pos(
                "see_password",
                [width_middle + input_text_size_half + 4, 50],
            )
        # endregion

        # region btn's
        if dpg.does_item_exist("login_btn"):
            if cls._is_login:
                login_bth_width = 53
            else:
                login_bth_width = 170

            dpg.set_item_pos("login_btn", [width_middle - login_bth_width // 2, 102])

        if dpg.does_item_exist("switch_btn"):
            login_bth_width = dpg.get_item_rect_size("switch_btn")[0]
            dpg.set_item_pos("switch_btn", [width_middle - login_bth_width // 2, 124])

        # endregion

    @classmethod
    def create(cls) -> None:
        with dpg.window(
            tag=cls._tag,
            on_close=cls._on_del,
            label="Example Window",
        ):
            dpg.add_image(
                "light_img",
                tag="logo_light",
                width=512,
                height=512,
                pos=[-128, -128],
            )
            dpg.add_image(
                "logo_img",
                tag="logo",
                width=256,
                height=256,
                pos=[0, 0],
            )

            dpg.add_text("Авторизация", tag="text_header")

            dpg.add_input_text(
                tag="login_text",
                hint="Логин",
                callback=lambda: dpg.focus_item("password_text"),
                on_enter=True,
            )

            dpg.add_input_text(
                tag="password_text",
                hint="Пароль",
                password=cls._see_password,
                callback=lambda: dpg.focus_item("password_text_2")
                if dpg.does_item_exist("password_text_2")
                else cls._enter(),
                on_enter=True,
            )
            dpg.add_checkbox(
                tag="see_password",
                callback=cls._toggle_see_password,
            )

            dpg.add_button(
                tag="login_btn",
                label="Войти",
                callback=cls._enter,
            )
            dpg.add_button(
                tag="switch_btn",
                label="Сменить на регистрацию",
                callback=cls._switch,
            )

        dpg.focus_item("login_text")
        dpg.set_primary_window(cls._tag, True)
        cls._setup_resize()

    @classmethod
    def _switch(cls) -> None:
        cls._is_login = not cls._is_login

        if cls._is_login:
            if dpg.does_item_exist("password_text_2"):
                dpg.delete_item("password_text_2")

            dpg.set_value("text_header", "Авторизация")
            dpg.set_item_label("switch_btn", "Сменить на регистрацию")
            dpg.set_item_label("login_btn", "Войти")

        else:
            dpg.add_input_text(
                tag="password_text_2",
                hint="Повтор пароля",
                password=cls._see_password,
                parent=cls._tag,
                callback=cls._enter,
                on_enter=True,
                show=False,
            )
            dpg.set_value("text_header", "Регистрация")
            dpg.set_item_label("switch_btn", "Сменить на авторизацию")
            dpg.set_item_label("login_btn", "Зарегистрироваться")

        cls._invoce_resize()

    @classmethod
    def _enter(cls) -> None:
        if cls._is_login:
            cls._auth()
        else:
            cls._register()

    @classmethod
    def _auth(cls) -> None:
        login = dpg.get_value("login_text")
        password = dpg.get_value("password_text")

        if not login:
            cls._summon_popup("Пустое поле ввода", "Логин не может быть пустым полем.")
            return

        if not password:
            cls._summon_popup("Пустое поле ввода", "Пароль не может быть пустым полем.")
            return

        try:
            APIManager.auth.login(login, password)

            APIManager.update_cur_user()

            WindowLeftPanel.create()
            cls._on_del()
        except Exception as err:
            text = {
                "Incorrect username or password": "Неверный логин или пароль",
            }.get(str(err), str(err))

            cls._summon_popup("Сервер отослал ошибку", text)

    @classmethod
    def _register(cls) -> None:
        login: str = dpg.get_value("login_text")
        password: str = dpg.get_value("password_text")
        password_2: str = dpg.get_value("password_text_2")

        if not login:
            cls._summon_popup("Пустое поле ввода", "Логин не может быть пустым полем.")
            return

        if not password:
            cls._summon_popup("Пустое поле ввода", "Пароль не может быть пустым полем.")
            return

        if password != password_2:
            cls._summon_popup(
                "Ошибка обработки пароля", "Ваши пароли не совпадают друг с другом."
            )
            return

        if not login.isascii():
            cls._summon_popup(
                "Ошибка обработки логина", "Ваш логин содержит не ascii символы."
            )
            return

        new_login = re.sub(r"\s+", "_", login.strip())

        if login != new_login:
            cls._summon_popup(
                "Ошибка обработки логина",
                "Ваш логин не подходил по стандартам. Система заменила логин.",
            )
            dpg.set_value("login_text", new_login)
            return

        try:
            APIManager.auth.register(login, password)

            APIManager.update_cur_user()

            WindowLeftPanel.create()
            cls._on_del()
        except Exception as err:
            text = {
                "Username contain non-ascii": "Логин содержит не ascii символы.",
                "Username cannot be empty": "Логин не может быть пустой строкой.",
                "User already exists": "Пользоватль с таким логином уже существует.",
            }.get(str(err), str(err))

            cls._summon_popup("Сервер отослал ошибку", text)

    @classmethod
    def _toggle_see_password(cls) -> None:
        cls._see_password = not cls._see_password

        dpg.configure_item("password_text", password=cls._see_password)
        if dpg.does_item_exist("password_text_2"):
            dpg.configure_item("password_text_2", password=cls._see_password)
