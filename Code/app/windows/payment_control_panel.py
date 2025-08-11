import json

import dearpygui.dearpygui as dpg

from Code.tools import APIManager, ViewportResizeManager

from .base_window import BaseWindow


class PaymentControlPanel(BaseWindow):
    _tag = "PaymentControlPanel"
    _rows: list[dict] = []

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_w, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])

        if dpg.does_item_exist("pay_table"):
            dpg.set_item_width("pay_table", window_w - 16)

        for tag in ("create_player_id", "create_items_json", "create_comm_key"):
            if dpg.does_item_exist(tag):
                dpg.set_item_width(tag, window_w - 16)

    @classmethod
    def _on_modal_delete(cls) -> None:
        if dpg.does_item_exist(cls._tag + "_create"):
            dpg.delete_item(cls._tag + "_create")

        ViewportResizeManager.remove_callback(cls._tag + "_create")

    @classmethod
    def _on_modal_create_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag + "_create"):
            return

        window_w, window_h = cls._setup_window(
            app_data, [0.8, 0.6], [0.1, 0.2], cls._tag + "_create"
        )

        for tag in ("create_player_id", "create_comm_key", "create_items_json"):
            if dpg.does_item_exist(tag):
                dpg.set_item_width(tag, window_w - 16)

        if dpg.does_item_exist("create_btns"):
            children = dpg.get_item_children("create_btns", 1)
            if children:
                each = (window_w - 23) // len(children)
                for child in children:
                    dpg.set_item_width(child, each)

    @classmethod
    def _refresh(cls) -> None:
        try:
            cls._rows = APIManager.payment_control.list()

        except Exception as e:
            cls._rows = []
            if dpg.does_item_exist("pay_status_line"):
                dpg.set_value("pay_status_line", f"Ошибка: {e}")

        cls._render_table()
        ViewportResizeManager.invoke()

    @classmethod
    def _render_table(cls) -> None:
        if not dpg.does_item_exist("pay_table"):
            return

        dpg.delete_item("pay_table", children_only=True)

        with dpg.table_row(parent="pay_table"):
            for h in ("u_id", "status", "player_id", "total", "items", "actions"):
                dpg.add_text(h)

        for row in cls._rows:
            u_id = row.get("u_id", "")
            status = row.get("status", "")
            player_id = row.get("player_id", "")
            total = row.get("total", "")
            snapshot_len = row.get("snapshot_len", 0)

            with dpg.table_row(parent="pay_table"):
                dpg.add_text(u_id)
                dpg.add_text(status)
                dpg.add_text(player_id)
                dpg.add_text(total)
                dpg.add_text(str(snapshot_len))

                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Cancel",
                        enabled=(status not in ("cancelled", "declined", "done")),
                        user_data=u_id,
                        callback=lambda s, a, uid: cls._cancel(uid),
                    )
                    dpg.add_button(
                        label="Delete",
                        user_data=u_id,
                        callback=lambda s, a, uid: cls._delete(uid),
                    )

    @classmethod
    def _cancel(cls, u_id: str) -> None:
        try:
            APIManager.payment_control.edit(u_id=u_id, status="cancelled")
            if dpg.does_item_exist("pay_status_line"):
                dpg.set_value("pay_status_line", f"Отменено: {u_id}")
        except Exception as e:
            if dpg.does_item_exist("pay_status_line"):
                dpg.set_value("pay_status_line", f"Ошибка отмены: {e}")
        cls._refresh()

    @classmethod
    def _delete(cls, u_id: str) -> None:
        try:
            APIManager.payment_control.delete(u_id)
            if dpg.does_item_exist("pay_status_line"):
                dpg.set_value("pay_status_line", f"Удалено: {u_id}")

        except Exception as e:
            if dpg.does_item_exist("pay_status_line"):
                dpg.set_value("pay_status_line", f"Ошибка удаления: {e}")

        cls._refresh()

    @classmethod
    def _open_create_modal(cls) -> None:
        if dpg.does_item_exist(cls._tag + "_create"):
            dpg.focus_item(cls._tag + "_create")
            return

        with dpg.window(
            tag=cls._tag + "_create",
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            on_close=cls._on_modal_delete,
            pos=[0, 0],
            no_scrollbar=True,
            modal=True,
        ):
            dpg.add_text("Создать платёж")

            dpg.add_input_text(tag="create_player_id", hint="player_id (обязательно)")
            dpg.add_input_text(
                tag="create_comm_key",
                hint="commission_key (например, AC)",
                default_value="AC",
            )
            dpg.add_combo(
                tag="create_status",
                items=["pending", "cancelled", "declined", "done"],
                default_value="pending",
                width=180,
            )

            dpg.add_text("items (JSON list of dicts):")
            dpg.add_input_text(
                tag="create_items_json",
                multiline=True,
                height=160,
                default_value='[{"service_u_id": "...", "count": 1}, ...]',
            )

            with dpg.group(horizontal=True, tag="create_btns"):
                dpg.add_button(label="Создать", callback=cls._create_payment)
                dpg.add_button(
                    label="Отмена",
                    callback=lambda: dpg.delete_item(cls._tag + "_create"),
                )

        ViewportResizeManager.add_callback(
            cls._tag + "_create", cls._on_modal_create_resize
        )
        ViewportResizeManager.invoke()

    @classmethod
    def _create_payment(cls) -> None:
        player_id = (dpg.get_value("create_player_id") or "").strip()
        comm_key = (dpg.get_value("create_comm_key") or "").strip() or "AC"
        status = dpg.get_value("create_status") or "pending"
        items_raw = dpg.get_value("create_items_json") or ""

        if not player_id:
            raise RuntimeError("player_id is required")

        try:
            items = json.loads(items_raw) if items_raw.strip() else []
            if not isinstance(items, list):
                raise ValueError("items must be a JSON list")

        except Exception as e:
            raise RuntimeError(f"Invalid items JSON: {e}")

        try:
            res = APIManager.payment_control.create(
                player_id=player_id,
                items=items,
                commission_key=comm_key,
                status=status,
            )
            msg = f"Создан платёж {res.get('u_id')} на сумму {res.get('total')}"
            if dpg.does_item_exist("pay_status_line"):
                dpg.set_value("pay_status_line", msg)

        except Exception as e:
            if dpg.does_item_exist("pay_status_line"):
                dpg.set_value("pay_status_line", f"Ошибка создания: {e}")

        if dpg.does_item_exist(cls._tag + "_create"):
            dpg.delete_item(cls._tag + "_create")
        ViewportResizeManager.remove_callback(cls._tag + "_create")

        cls._refresh()

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
            with dpg.group(horizontal=True):
                dpg.add_button(label="Создать платёж", callback=cls._open_create_modal)
                dpg.add_spacer(width=8)
                dpg.add_button(label="Обновить", callback=cls._refresh)
                dpg.add_spacer(width=16)
                dpg.add_text("", tag="pay_status_line")

            dpg.add_separator()

            with dpg.table(
                tag="pay_table",
                policy=dpg.mvTable_SizingStretchProp,
                resizable=True,
                borders_outerH=True,
                borders_outerV=True,
                borders_innerH=True,
                borders_innerV=True,
                header_row=False,
            ):
                pass

        cls._refresh()
        super().create()
