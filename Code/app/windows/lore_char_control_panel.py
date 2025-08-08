import dearpygui.dearpygui as dpg

from Code.tools import APIManager, ViewportResizeManager

from .base_window import BaseWindow


class LoreCharControlPanel(BaseWindow):
    _tag = "LoreCharControlPanel"
    _btns_ids = []
    _lore_data = {}

    @staticmethod
    def _status_label(status: str) -> str:
        match status:
            case "free":
                return "Доступен"
            case "taken":
                return "Занят"
            case "blocked":
                return "Заблокирован"
            case _:
                return "Доступен"

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

        btn_width = window_width // 3 - 10

        for btn in cls._btns_ids:
            if not dpg.does_item_exist(btn):
                continue

            dpg.set_item_width(btn, btn_width)

    @classmethod
    def _render_btns(cls) -> None:
        if not dpg.does_item_exist("lore_char_group"):
            return

        dpg.delete_item("lore_char_group", children_only=True)
        cls._btns_ids.clear()

        group_id = dpg.add_group(parent="lore_char_group", horizontal=True)
        group_use = 0
        for key, value in cls._lore_data.items():
            if group_use >= 3:
                group_id = dpg.add_group(parent="lore_char_group", horizontal=True)
                group_use = 0

            btn_id = dpg.add_button(
                parent=group_id,
                label=value["name"],
                user_data=key,
                callback=cls._edit_modal_window,
            )
            group_use += 1
            cls._btns_ids.append(btn_id)

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.focus_item(cls._tag)
            return

        cls._lore_data = APIManager.lore_char_control.get()

        with dpg.window(
            tag=cls._tag,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_del,
            pos=[0, 0],
            no_scrollbar=True,
        ):
            dpg.add_button(
                label="Создать лорного персонажа",
                callback=cls._create_modal_window,
            )
            dpg.add_separator()
            dpg.add_text("Все доступные лорные персонажи:")
            dpg.add_group(tag="lore_char_group")
            cls._render_btns()

        super().create()

    @classmethod
    def _on_modal_delete(cls) -> None:
        dpg.delete_item(cls._tag + "_modal_create")
        dpg.delete_item(cls._tag + "_modal_edit")
        ViewportResizeManager.remove_callback(cls._tag + "_modal_create")
        ViewportResizeManager.remove_callback(cls._tag + "_modal_edit")

    @classmethod
    def _on_modal_create_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag + "_modal_create"):
            return

        window_width, window_hight = cls._setup_window(
            app_data,
            [0.8, 0.7],
            [0.1, 0.1],
            cls._tag + "_modal_create",
        )

        window_width_btn = window_width - 23
        if dpg.does_item_exist("create_btns"):
            children = dpg.get_item_children("create_btns", 1)
            if children:
                for child in children:
                    dpg.set_item_width(child, window_width_btn // 2)

            dpg.set_item_pos("create_btns", [7, window_hight - 19 - 12])

        if dpg.does_item_exist("create_lore_name"):
            dpg.set_item_width("create_lore_name", window_width - 140 - 24)

        if dpg.does_item_exist("create_lore_wiki"):
            dpg.set_item_width("create_lore_wiki", window_width - 16)

    @classmethod
    def _on_modal_edit_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag + "_modal_edit"):
            return

        window_width, window_hight = cls._setup_window(
            app_data,
            [0.8, 0.7],
            [0.1, 0.1],
            cls._tag + "_modal_edit",
        )

        window_width_btn = window_width - 30
        if dpg.does_item_exist("edit_btns"):
            children = dpg.get_item_children("edit_btns", 1)
            if children:
                for child in children:
                    dpg.set_item_width(child, window_width_btn // 3)

            dpg.set_item_pos("edit_btns", [7, window_hight - 19 - 12])

        if dpg.does_item_exist("edit_lore_name"):
            dpg.set_item_width("edit_lore_name", window_width - 140 - 24)

        if dpg.does_item_exist("edit_lore_wiki"):
            dpg.set_item_width("edit_lore_wiki", window_width - 16)

    @classmethod
    def _create(cls) -> None:
        name: str = dpg.get_value("create_lore_name")
        status = dpg.get_value("create_lore_status")
        wiki = dpg.get_value("create_lore_wiki")

        name = name.strip()
        key = name.lower().replace(" ", "_")
        wiki = wiki.strip()
        match status:
            case "Доступен":
                status = "free"

            case "Занят":
                status = "taken"

            case "Заблокирован":
                status = "blocked"

        APIManager.lore_char_control.create(key, name, status, wiki)
        cls._lore_data = APIManager.lore_char_control.get()
        cls._render_btns()
        dpg.delete_item(cls._tag + "_modal_create")
        ViewportResizeManager.invoke()

    @classmethod
    def _edit(cls, key: str) -> None:
        name = dpg.get_value("edit_lore_name").strip()
        status = dpg.get_value("edit_lore_status")
        wiki = dpg.get_value("edit_lore_wiki").strip()

        match status:
            case "Доступен":
                status = "free"
            case "Занят":
                status = "taken"
            case "Заблокирован":
                status = "blocked"

        APIManager.lore_char_control.edit(key, name, status, wiki)
        cls._lore_data = APIManager.lore_char_control.get()
        cls._render_btns()
        dpg.delete_item(cls._tag + "_modal_edit")
        ViewportResizeManager.invoke()

    @classmethod
    def _delete(cls, key: str) -> None:
        APIManager.lore_char_control.delete(key)
        cls._lore_data = APIManager.lore_char_control.get()
        cls._render_btns()
        dpg.delete_item(cls._tag + "_modal_edit")
        ViewportResizeManager.invoke()

    @classmethod
    def _create_modal_window(cls) -> None:
        if dpg.does_item_exist(cls._tag + "_modal_create"):
            dpg.focus_item(cls._tag + "_modal_create")
            return

        with dpg.window(
            tag=cls._tag + "_modal_create",
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_modal_delete,
            pos=[0, 0],
            no_scrollbar=True,
            modal=True,
        ):
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    hint="Имя лорного персонажа",
                    tag="create_lore_name",
                    on_enter=True,
                    callback=lambda: dpg.focus_item("create_lore_wiki"),
                )
                dpg.add_combo(
                    ["Доступен", "Занят", "Заблокирован"],
                    default_value="Доступен",
                    tag="create_lore_status",
                    width=140,
                )

            dpg.add_input_text(
                hint="Ссылка на wiki (опционально)",
                tag="create_lore_wiki",
            )

            with dpg.group(horizontal=True, tag="create_btns"):
                dpg.add_button(
                    label="Создать",
                    callback=cls._create,
                )
                dpg.add_button(
                    label="Отменить",
                    callback=lambda: dpg.delete_item(cls._tag + "_modal_create"),
                )

        ViewportResizeManager.add_callback(
            cls._tag + "_modal_create",
            cls._on_modal_create_resize,
        )

    @classmethod
    def _edit_modal_window(cls, sender, app_data, user_data):
        key = user_data
        char_data = cls._lore_data.get(key)
        if not char_data:
            return

        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.focus_item(cls._tag + "_modal_edit")
            return

        with dpg.window(
            tag=cls._tag + "_modal_edit",
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_modal_delete,
            pos=[0, 0],
            no_scrollbar=True,
            modal=True,
        ):
            dpg.add_text(f"Редактирование персонажа: {char_data['name']}")

            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    hint="Новое имя",
                    tag="edit_lore_name",
                    default_value=char_data["name"],
                    on_enter=True,
                    callback=lambda: dpg.focus_item("edit_lore_wiki"),
                )
                dpg.add_combo(
                    ["Доступен", "Занят", "Заблокирован"],
                    default_value=cls._status_label(char_data.get("status", "free")),
                    tag="edit_lore_status",
                    width=140,
                )

            dpg.add_input_text(
                hint="Ссылка на wiki (опционально)",
                tag="edit_lore_wiki",
                default_value=char_data.get("wiki", ""),
            )

            with dpg.group(horizontal=True, tag="edit_btns"):
                dpg.add_button(
                    label="Сохранить",
                    callback=lambda: cls._edit(key),
                )
                dpg.add_button(
                    label="Удалить",
                    callback=lambda: cls._delete(key),
                )
                dpg.add_button(
                    label="Отменить",
                    callback=lambda: dpg.delete_item(cls._tag + "_modal_edit"),
                )

        ViewportResizeManager.add_callback(
            cls._tag + "_modal_edit",
            cls._on_modal_edit_resize,
        )
