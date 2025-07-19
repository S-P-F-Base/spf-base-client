import dearpygui.dearpygui as dpg

from .base_window import BaseWindow


class WindowAuth(BaseWindow):
    _tag = "WindowAuth"
    _is_login: bool = True
    _see_password: bool = True

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        _, _, width, height = app_data

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

            dpg.add_input_text(tag="login_text", hint="Логин")

            dpg.add_input_text(
                tag="password_text",
                hint="Пароль",
                password=cls._see_password,
            )
            dpg.add_checkbox(
                tag="see_password",
                label="Посмотреть пароль",
                callback=cls._toggle_see_password,
            )

            dpg.add_button(tag="login_btn", label="Войти", callback=cls._enter)
            dpg.add_button(
                tag="switch_btn", label="Сменить на регистрацию", callback=cls._switch
            )

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
            )
            dpg.set_value("text_header", "Регистрация")
            dpg.set_item_label("switch_btn", "Сменить на авторизацию")
            dpg.set_item_label("login_btn", "Зарегестироваться")

        cls._invoce_resize()

    @classmethod
    def _enter(cls) -> None: ...

    @classmethod
    def _toggle_see_password(cls) -> None:
        cls._see_password = not cls._see_password

        dpg.configure_item("password_text", password=cls._see_password)
        if dpg.does_item_exist("password_text_2"):
            dpg.configure_item("password_text_2", password=cls._see_password)
