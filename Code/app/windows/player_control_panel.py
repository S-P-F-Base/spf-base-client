import dearpygui.dearpygui as dpg

from Code.tools import APIManager, ViewportResizeManager

from .base_window import BaseWindow


class PlayerControlPanel(BaseWindow):
    _tag = "PlayerControlPanel"
    _p_data: list[dict] = []
    _btns_ids: list[int] = []

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])
        btn_width = window_width // 3 - 10

        for btn in cls._btns_ids:
            if dpg.does_item_exist(btn):
                dpg.set_item_width(btn, btn_width)

    # ---------- list rendering ----------

    @classmethod
    def _render_btns(cls) -> None:
        if not dpg.does_item_exist("player_group"):
            return

        dpg.delete_item("player_group", children_only=True)
        cls._btns_ids.clear()

        group_id = dpg.add_group(parent="player_group", horizontal=True)
        group_use = 0

        for value in cls._p_data:
            if group_use >= 3:
                group_id = dpg.add_group(parent="player_group", horizontal=True)
                group_use = 0

            u_id = value.get("id")
            steam_id = value.get("steam_id", "None value")
            discord_name = value.get("data", {}).get("discord_name") or None

            btn_id = dpg.add_button(
                parent=group_id,
                label=discord_name if discord_name else steam_id,
                user_data=u_id,
                callback=cls._edit_modal_window,
            )
            group_use += 1
            cls._btns_ids.append(btn_id)  # type: ignore

    # ---------- lifecycle ----------

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.focus_item(cls._tag)
            return

        cls._p_data = APIManager.player_control.get()

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
                dpg.add_button(
                    label="Создать игрока", callback=cls._create_modal_window
                )
                dpg.add_spacer(width=8)
                dpg.add_button(label="Обновить", callback=cls._refresh)

            dpg.add_separator()
            dpg.add_group(tag="player_group")

        cls._render_btns()
        super().create()

    @classmethod
    def _refresh(cls) -> None:
        cls._p_data = APIManager.player_control.get()
        cls._render_btns()
        ViewportResizeManager.invoke()

    # ---------- modal lifecycle helpers ----------

    @classmethod
    def _on_modal_delete(cls) -> None:
        if dpg.does_item_exist(cls._tag + "_modal_create"):
            dpg.delete_item(cls._tag + "_modal_create")
        ViewportResizeManager.remove_callback(cls._tag + "_modal_create")

        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.delete_item(cls._tag + "_modal_edit")
        ViewportResizeManager.remove_callback(cls._tag + "_modal_edit")

    # ---------- create modal ----------

    @classmethod
    def _on_modal_create_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag + "_modal_create"):
            return

        window_width, window_h = cls._setup_window(
            app_data, [0.8, 0.55], [0.1, 0.2], cls._tag + "_modal_create"
        )

        if dpg.does_item_exist("create_discord_name"):
            dpg.set_item_width("create_discord_name", window_width - 16)
        if dpg.does_item_exist("create_steam_url"):
            dpg.set_item_width("create_steam_url", window_width - 16)

        if dpg.does_item_exist("create_btns"):
            children = dpg.get_item_children("create_btns", 1)
            if children:
                for child in children:
                    dpg.set_item_width(child, (window_width - 23) // 2)
            dpg.set_item_pos("create_btns", [7, window_h - 19 - 12])

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
            dpg.add_text("Создание игрока")

            dpg.add_input_text(
                tag="create_discord_name",
                hint="Discord name (опционально)",
            )
            dpg.add_input_text(
                tag="create_steam_url",
                hint="Steam profile URL (обязательно)",
            )

            with dpg.group(horizontal=True, tag="create_btns"):
                dpg.add_button(label="Создать", callback=cls._create_player)
                dpg.add_button(
                    label="Отменить",
                    callback=lambda: dpg.delete_item(cls._tag + "_modal_create"),
                )

        ViewportResizeManager.add_callback(
            cls._tag + "_modal_create", cls._on_modal_create_resize
        )
        ViewportResizeManager.invoke()

    @classmethod
    def _create_player(cls) -> None:
        discord_name = dpg.get_value("create_discord_name").strip()
        steam_url = dpg.get_value("create_steam_url").strip()
        if not steam_url:
            raise RuntimeError("Steam URL is required")

        APIManager.player_control.create(discord_name=discord_name, steam_url=steam_url)
        cls._refresh()
        if dpg.does_item_exist(cls._tag + "_modal_create"):
            dpg.delete_item(cls._tag + "_modal_create")

    # ---------- edit modal ----------

    @classmethod
    def _on_modal_edit_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag + "_modal_edit"):
            return

        window_width, window_h = cls._setup_window(
            app_data, [0.85, 0.8], [0.075, 0.1], cls._tag + "_modal_edit"
        )

        for tag in ("edit_discord_name", "edit_mb_limit", "edit_mb_taken"):
            if dpg.does_item_exist(tag):
                dpg.set_item_width(tag, window_width - 16)

        if dpg.does_item_exist("bl_table"):
            dpg.set_item_width("bl_table", window_width - 16)

        if dpg.does_item_exist("notes_scroller"):
            dpg.set_item_width("notes_scroller", window_width - 16)
            dpg.set_item_height("notes_scroller", max(150, window_h // 3))

        if dpg.does_item_exist("edit_btns"):
            children = dpg.get_item_children("edit_btns", 1)
            if children:
                each = (window_width - 30) // len(children)
                for child in children:
                    dpg.set_item_width(child, each)

    @classmethod
    def _find_player(cls, u_id: int) -> dict | None:
        for p in cls._p_data:
            if p.get("id") == u_id:
                return p

        return None

    @classmethod
    def _edit_modal_window(cls, sender, app_data, user_data):
        u_id: int = user_data
        pdata = cls._find_player(u_id)
        if not pdata:
            return

        data = pdata.get("data", {}) or {}
        notes = data.get("note", []) or []
        blacklist: dict[str, bool] = data.get("blacklist", {}) or {}

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
            dpg.add_text(
                f"Редактирование игрока: id={u_id} | steam_id={pdata.get('steam_id', '')}"
            )

            dpg.add_input_text(
                tag="edit_discord_name",
                default_value=data.get("discord_name", ""),
                hint="Discord name (опционально)",
            )

            cur_limit = float(data.get("mb_limit") or 0.0)
            cur_taken = float(data.get("mb_taken") or 0.0)
            dpg.add_separator()
            dpg.add_text(f"Текущие лимиты: limit={cur_limit} | taken={cur_taken}")

            dpg.add_input_text(
                tag="edit_mb_limit",
                hint="mb_limit: =N / +N / -N или просто N",
            )
            dpg.add_input_text(
                tag="edit_mb_taken",
                hint="mb_taken: =N / +N / -N или просто N (можно > лимита)",
            )
            dpg.add_separator()

            dpg.add_text("Чёрный список:")
            with dpg.table(
                tag="bl_table",
                policy=dpg.mvTable_SizingStretchProp,
                resizable=True,
                borders_outerH=True,
                borders_outerV=True,
                borders_innerH=True,
                borders_innerV=True,
                header_row=True,
            ):
                dpg.add_table_column(label="Флаг")
                dpg.add_table_column(label="Значение")

                for k, v in blacklist.items():
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(k)
                        with dpg.table_cell():
                            dpg.add_checkbox(tag=f"bl_flag__{k}", default_value=bool(v))

            dpg.add_separator()
            dpg.add_text("Заметки:")
            with dpg.child_window(
                tag="notes_scroller",
                autosize_x=False,
                autosize_y=False,
                horizontal_scrollbar=True,
            ):
                if not notes:
                    dpg.add_text("Заметок нет.")
                else:
                    for idx, note in enumerate(notes):
                        status = note.get("status", "")
                        text = note.get("text") or note.get("value") or ""
                        author = note.get("author") or ""
                        last_author = note.get("last_status_envoke_author") or ""

                        with dpg.group(horizontal=False):
                            header = f"[{idx}] status={status}"
                            if author:
                                header += f" | by {author}"
                            if last_author:
                                header += f" | status by {last_author}"
                            dpg.add_text(header)

                            txt_id = dpg.add_text(text, wrap=600)
                            with dpg.tooltip(txt_id):
                                dpg.add_text(text, wrap=600)

                            with dpg.group(horizontal=True):
                                dpg.add_combo(
                                    items=["active", "deleted"],
                                    default_value=status,
                                    tag=f"note_status_input__{idx}",
                                    width=160,
                                )

                                dpg.add_button(
                                    label="Сменить статус",
                                    user_data=(u_id, idx),
                                    callback=lambda s, a, ud: cls._change_note_status(
                                        ud[0], ud[1]
                                    ),
                                )

                            dpg.add_separator()

            dpg.add_text("Добавить заметку:")
            dpg.add_input_text(
                tag="add_note_text", multiline=True, height=80, hint="Текст заметки"
            )
            dpg.add_button(
                label="Добавить заметку",
                user_data=u_id,
                callback=lambda s, a, uid: cls._add_note(uid),
            )

            dpg.add_separator()
            with dpg.group(horizontal=True, tag="edit_btns"):
                dpg.add_button(
                    label="Сохранить",
                    user_data=u_id,
                    callback=lambda s, a, uid: cls._save_player(uid),
                )
                dpg.add_button(
                    label="Закрыть",
                    callback=lambda: dpg.delete_item(cls._tag + "_modal_edit"),
                )

        ViewportResizeManager.add_callback(
            cls._tag + "_modal_edit", cls._on_modal_edit_resize
        )

    # ---------- actions ----------

    @classmethod
    def _collect_blacklist(cls) -> dict[str, bool]:
        result: dict[str, bool] = {}
        if not dpg.does_item_exist("bl_table"):
            return result

        rows = dpg.get_item_children("bl_table", 1) or []
        for row in rows:
            cells = dpg.get_item_children(row, 1) or []
            if len(cells) < 2:
                continue

            cell0_children = dpg.get_item_children(cells[0], 1) or []
            cell1_children = dpg.get_item_children(cells[1], 1) or []
            if not cell0_children or not cell1_children:
                continue

            key_widget = cell0_children[0]
            cb_widget = cell1_children[0]

            info_key = dpg.get_item_info(key_widget)
            info_cb = dpg.get_item_info(cb_widget)
            if (
                info_key["type"] == "mvAppItemType::mvText"
                and info_cb["type"] == "mvAppItemType::mvCheckbox"
            ):
                key_text = dpg.get_value(key_widget)
                result[str(key_text)] = bool(dpg.get_value(cb_widget))

        return result

    @classmethod
    def _save_player(cls, u_id: int) -> None:
        discord_name = dpg.get_value("edit_discord_name").strip()
        blacklist = cls._collect_blacklist()

        mb_limit_raw = (
            dpg.get_value("edit_mb_limit").strip()
            if dpg.does_item_exist("edit_mb_limit")
            else ""
        )
        mb_taken_raw = (
            dpg.get_value("edit_mb_taken").strip()
            if dpg.does_item_exist("edit_mb_taken")
            else ""
        )

        mb_limit = mb_limit_raw if mb_limit_raw else None
        mb_taken = mb_taken_raw if mb_taken_raw else None

        APIManager.player_control.edit(
            u_id=u_id,
            discord_name=discord_name or None,
            blacklist=blacklist or None,
            mb_limit=mb_limit or None,
            mb_taken=mb_taken or None,
        )

        cls._refresh()
        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.delete_item(cls._tag + "_modal_edit")

    @classmethod
    def _add_note(cls, u_id: int) -> None:
        text = dpg.get_value("add_note_text").strip()
        if not text:
            raise RuntimeError("Note text is required")

        APIManager.player_control.add_note(u_id=u_id, text=text)
        cls._p_data = APIManager.player_control.get()
        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.delete_item(cls._tag + "_modal_edit")

        cls._edit_modal_window(None, None, u_id)

    @classmethod
    def _change_note_status(cls, u_id: int, index: int) -> None:
        tag = f"note_status_input__{index}"
        if not dpg.does_item_exist(tag):
            raise RuntimeError("Status input not found")

        status = dpg.get_value(tag).strip()
        if not status:
            raise RuntimeError("New status is required")

        APIManager.player_control.change_note_status(
            u_id=u_id, index=index, status=status
        )
        cls._p_data = APIManager.player_control.get()
        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.delete_item(cls._tag + "_modal_edit")

        cls._edit_modal_window(None, None, u_id)
