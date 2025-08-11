from datetime import date, datetime, timezone
from typing import Any, Optional, Tuple

import dearpygui.dearpygui as dpg

from Code.tools import APIManager, ViewportResizeManager

from .base_window import BaseWindow


class ServiceControlPanel(BaseWindow):
    _tag = "ServiceControlPanel"
    _s_data: list[dict] = []
    _btns_ids: list[int] = []

    STATUS_UI2RAW = {
        "Активна": "on",
        "Выключена": "off",
        "Архив": "archive",
    }
    STATUS_RAW2UI = {v: k for k, v in STATUS_UI2RAW.items()}

    @classmethod
    def _on_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag):
            return

        window_width, _ = cls._setup_window(app_data, [0.67, 1], [0.33, 0])
        btn_width = window_width // 3 - 10
        for btn in cls._btns_ids:
            if dpg.does_item_exist(btn):
                dpg.set_item_width(btn, btn_width)

    @staticmethod
    def _now_time_dict() -> dict:
        now = datetime.now(timezone.utc)
        return {"hour": now.hour, "min": now.minute, "sec": now.second}

    @staticmethod
    def _iso_to_time_dict(iso: str | None) -> dict:
        if not iso:
            return {"hour": 0, "min": 0, "sec": 0}

        try:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            return {"hour": dt.hour, "min": dt.minute, "sec": dt.second}

        except Exception:
            return {"hour": 0, "min": 0, "sec": 0}

    @staticmethod
    def _iso_to_date_str(iso: str | None) -> str:
        if not iso:
            return ""

        try:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
            return dt.date().isoformat()

        except Exception:
            return ""

    @staticmethod
    def _label_for_card(svc: dict) -> str:
        d: dict = svc.get("data", {}) or {}
        return d.get("name") or "(no name)"

    @staticmethod
    def _safe_str(v: Any) -> str | None:
        if v is None:
            return None

        s = str(v).strip()
        return s if s else None

    @staticmethod
    def _today_utc() -> date:
        return datetime.now(timezone.utc).date()

    @classmethod
    def _validate_date_str(cls, s: str) -> Tuple[bool, str]:
        if not s:
            return False, "Введите дату в формате YYYY-MM-DD"

        try:
            y, m, d = s.split("-")
            dt = date(int(y), int(m), int(d))

        except Exception:
            return False, "Неверный формат. Ожидается YYYY-MM-DD"

        if dt > cls._today_utc():
            return False, "Дата не может быть позже сегодняшнего дня (UTC)"

        return True, ""

    @staticmethod
    def _compose_iso_from_date_time(date_str: str, time_dict: dict) -> Optional[str]:
        if not date_str:
            return None
        try:
            y, m, d = date_str.split("-")
            h = int(time_dict.get("hour", 0))
            mi = int(time_dict.get("min", 0))
            s = int(time_dict.get("sec", 0))
            dt = datetime(
                int(y), int(m), int(d), h, mi, s, tzinfo=timezone.utc
            ).replace(microsecond=0)
            return dt.isoformat().replace("+00:00", "Z")

        except Exception:
            return None

    @staticmethod
    def _set_enabled(tags: list[str], enabled: bool) -> None:
        for t in tags:
            if dpg.does_item_exist(t):
                dpg.configure_item(t, show=enabled)

    @classmethod
    def _render_btns(cls) -> None:
        if not dpg.does_item_exist("service_group"):
            return

        dpg.delete_item("service_group", children_only=True)
        cls._btns_ids.clear()

        group_id = dpg.add_group(parent="service_group", horizontal=True)
        group_use = 0

        for value in cls._s_data:
            if group_use >= 3:
                group_id = dpg.add_group(parent="service_group", horizontal=True)
                group_use = 0

            u_id = value.get("u_id")
            label = cls._label_for_card(value)

            btn_id = dpg.add_button(
                parent=group_id,
                label=label,
                user_data=u_id,
                callback=cls._open_edit_modal,
            )
            group_use += 1
            cls._btns_ids.append(btn_id)  # type: ignore

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._tag):
            dpg.focus_item(cls._tag)
            return

        cls._s_data = APIManager.service_control.list()

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
                dpg.add_button(label="Создать услугу", callback=cls._open_create_modal)
                dpg.add_spacer(width=8)
                dpg.add_button(label="Обновить", callback=cls._refresh)

            dpg.add_separator()
            dpg.add_group(tag="service_group")

        cls._render_btns()
        super().create()

    @classmethod
    def _refresh(cls) -> None:
        cls._s_data = APIManager.service_control.list()
        cls._render_btns()
        ViewportResizeManager.invoke()

    @classmethod
    def _on_modal_delete(cls) -> None:
        if dpg.does_item_exist(cls._tag + "_modal_create"):
            dpg.delete_item(cls._tag + "_modal_create")

        ViewportResizeManager.remove_callback(cls._tag + "_modal_create")

        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.delete_item(cls._tag + "_modal_edit")

        ViewportResizeManager.remove_callback(cls._tag + "_modal_edit")

    @classmethod
    def _on_modal_create_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag + "_modal_create"):
            return

        window_width, _ = cls._setup_window(
            app_data, [0.85, 0.8], [0.075, 0.1], cls._tag + "_modal_create"
        )

        for tag in (
            "svc_create_name",
            "svc_create_description",
            "svc_create_price_main",
            "svc_create_left_value",
        ):
            if dpg.does_item_exist(tag):
                dpg.set_item_width(tag, window_width - 16)

        if dpg.does_item_exist("svc_create_btns"):
            children = dpg.get_item_children("svc_create_btns", 1)
            if children:
                for child in children:
                    dpg.set_item_width(child, (window_width - 23) // 2)

    @classmethod
    def _on_date_input_cb(cls, sender, app_data, user_data):
        date_tag, err_tag = user_data
        s = (dpg.get_value(date_tag) or "").strip()
        ok, msg = cls._validate_date_str(s)
        dpg.configure_item(err_tag, show=not ok)
        dpg.set_value(err_tag, msg if not ok else "")

    @classmethod
    def _on_checkbox_toggle(cls, sender, app_data, user_data):
        enabled = bool(dpg.get_value(sender))
        tags: list[str] = user_data or []
        cls._set_enabled(tags, enabled)

    @classmethod
    def _open_create_modal(cls) -> None:
        if dpg.does_item_exist(cls._tag + "_modal_create"):
            dpg.focus_item(cls._tag + "_modal_create")
            return

        today = cls._today_utc().isoformat()

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
            dpg.add_text("Создание услуги")

            dpg.add_input_text(tag="svc_create_name", hint="Название (обязательно)")
            dpg.add_input_text(
                tag="svc_create_description",
                hint="Описание (опционально)",
                multiline=True,
                height=80,
            )

            dpg.add_checkbox(
                tag="svc_create_oferta_limit",
                label="Оферта лимит",
                default_value=False,
            )

            dpg.add_checkbox(
                tag="svc_create_discount_enable",
                label="Указать окончание скидки (не позже сегодня, UTC)",
                default_value=False,
                callback=cls._on_checkbox_toggle,
                user_data=["svc_create_discount_date", "svc_create_discount_time"],
            )
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="svc_create_discount_date",
                    hint="YYYY-MM-DD",
                    default_value=today,
                    callback=cls._on_date_input_cb,
                    user_data=("svc_create_discount_date", "svc_create_discount_err"),
                    show=False,
                )
                dpg.add_time_picker(
                    tag="svc_create_discount_time",
                    default_value=cls._now_time_dict(),
                    hour24=True,
                    show=False,
                )
            dpg.add_text(
                tag="svc_create_discount_err",
                default_value="",
                color=(255, 120, 120),
                show=False,
            )

            dpg.add_checkbox(
                tag="svc_create_sell_enable",
                label="Указать окончание продажи (не позже сегодня, UTC)",
                default_value=False,
                callback=cls._on_checkbox_toggle,
                user_data=["svc_create_sell_date", "svc_create_sell_time"],
            )
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="svc_create_sell_date",
                    hint="YYYY-MM-DD",
                    default_value=today,
                    callback=cls._on_date_input_cb,
                    user_data=("svc_create_sell_date", "svc_create_sell_err"),
                    show=False,
                )
                dpg.add_time_picker(
                    tag="svc_create_sell_time",
                    default_value=cls._now_time_dict(),
                    hour24=True,
                    show=False,
                )
            dpg.add_text(
                tag="svc_create_sell_err",
                default_value="",
                color=(255, 120, 120),
                show=False,
            )

            dpg.add_input_text(
                tag="svc_create_price_main",
                hint="Базовая цена (напр. 500.00) - обязательно",
            )
            dpg.add_input_int(
                label="Скидка",
                tag="svc_create_discount_value",
                default_value=0,
                min_value=0,
                max_value=100,
            )

            dpg.add_combo(
                tag="svc_create_status",
                items=list(cls.STATUS_UI2RAW.keys()),
                default_value="Выключена",
                width=220,
                label="Статус",
            )

            dpg.add_checkbox(
                tag="svc_create_left_enable",
                label="Указать лимит покупок",
                default_value=False,
                callback=cls._on_checkbox_toggle,
                user_data=["svc_create_left_value"],
            )
            dpg.add_input_int(
                tag="svc_create_left_value",
                min_value=0,
                default_value=0,
                show=False,
                step=1,
            )

            with dpg.group(horizontal=True, tag="svc_create_btns"):
                dpg.add_button(label="Создать", callback=cls._create_service)
                dpg.add_button(
                    label="Отменить",
                    callback=lambda: dpg.delete_item(cls._tag + "_modal_create"),
                )

        ViewportResizeManager.add_callback(
            cls._tag + "_modal_create", cls._on_modal_create_resize
        )
        ViewportResizeManager.invoke()

    @classmethod
    def _create_service(cls) -> None:
        name = (dpg.get_value("svc_create_name") or "").strip()
        if not name:
            raise RuntimeError("Name is required")

        price_main = (dpg.get_value("svc_create_price_main") or "").strip()
        if not price_main:
            raise RuntimeError("Price is required")

        description = cls._safe_str(dpg.get_value("svc_create_description"))
        discount_value = int(dpg.get_value("svc_create_discount_value") or 0)

        status_ui = (dpg.get_value("svc_create_status") or "Выключена").strip()
        status = cls.STATUS_UI2RAW.get(status_ui, "off")

        oferta_limit = bool(dpg.get_value("svc_create_oferta_limit"))

        discount_date_iso = None
        if dpg.get_value("svc_create_discount_enable"):
            date_str = (dpg.get_value("svc_create_discount_date") or "").strip()
            ok, msg = cls._validate_date_str(date_str)
            if not ok:
                raise RuntimeError(msg)

            tdict = dpg.get_value("svc_create_discount_time") or cls._now_time_dict()
            discount_date_iso = cls._compose_iso_from_date_time(date_str, tdict)
            if not discount_date_iso:
                raise RuntimeError("Invalid discount date/time")

        sell_time_iso = None
        if dpg.get_value("svc_create_sell_enable"):
            date_str = (dpg.get_value("svc_create_sell_date") or "").strip()
            ok, msg = cls._validate_date_str(date_str)
            if not ok:
                raise RuntimeError(msg)

            tdict = dpg.get_value("svc_create_sell_time") or cls._now_time_dict()
            sell_time_iso = cls._compose_iso_from_date_time(date_str, tdict)
            if not sell_time_iso:
                raise RuntimeError("Invalid sell end date/time")

        if bool(dpg.get_value("svc_create_left_enable")):
            left = int(dpg.get_value("svc_create_left_value") or 0)

        else:
            left = None

        APIManager.service_control.create(
            name=name,
            description=description or "",
            price_main=price_main,
            discount_value=discount_value,
            discount_date=discount_date_iso,
            status=status,  # type: ignore
            left=left,
            sell_time=sell_time_iso,
            oferta_limit=oferta_limit,
        )

        cls._refresh()
        if dpg.does_item_exist(cls._tag + "_modal_create"):
            dpg.delete_item(cls._tag + "_modal_create")

    @classmethod
    def _on_modal_edit_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._tag + "_modal_edit"):
            return

        window_width, _ = cls._setup_window(
            app_data, [0.85, 0.8], [0.075, 0.1], cls._tag + "_modal_edit"
        )

        for tag in (
            "svc_edit_name",
            "svc_edit_description",
            "svc_edit_price_main",
            "svc_edit_left_value",
        ):
            if dpg.does_item_exist(tag):
                dpg.set_item_width(tag, window_width - 16)

        if dpg.does_item_exist("svc_edit_btns"):
            children = dpg.get_item_children("svc_edit_btns", 1)
            if children:
                each = (window_width - 30) // len(children)
                for child in children:
                    dpg.set_item_width(child, each)

    @classmethod
    def _find_service(cls, u_id: str) -> dict | None:
        for s in cls._s_data:
            if s.get("u_id") == u_id:
                return s

        return None

    @classmethod
    def _open_edit_modal(cls, sender, app_data, user_data):
        u_id: str = user_data
        sdata = cls._find_service(u_id)
        if not sdata:
            return

        full = APIManager.service_control.get(u_id)
        data = (full.get("data") or sdata.get("data")) or {}
        final_price = full.get("final_price") or sdata.get("final_price") or "0.00"

        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.focus_item(cls._tag + "_modal_edit")
            return

        creation_iso = data.get("creation_date")
        dd_iso = data.get("discount_date")
        st_iso = data.get("sell_time")

        dd_date = cls._iso_to_date_str(dd_iso) or cls._today_utc().isoformat()
        dd_time = cls._iso_to_time_dict(dd_iso if dd_iso else None)

        st_date = cls._iso_to_date_str(st_iso) or cls._today_utc().isoformat()
        st_time = cls._iso_to_time_dict(st_iso if st_iso else None)

        left_val = data.get("left")
        left_enable_default = left_val is not None
        left_default_int = int(left_val or 0)

        status_ui_default = cls.STATUS_RAW2UI.get(
            data.get("status", "off"), "Выключена"
        )

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
                f"Редактирование услуги: u_id={u_id} | final_price={final_price}"
            )
            dpg.add_text(f"Создана: {creation_iso or '-'} (UTC)")

            dpg.add_input_text(
                tag="svc_edit_name",
                default_value=data.get("name", ""),
                hint="Название (обязательно)",
            )
            dpg.add_input_text(
                tag="svc_edit_description",
                default_value=data.get("description", ""),
                hint="Описание",
                multiline=True,
                height=80,
            )

            dpg.add_checkbox(
                tag="svc_edit_oferta_limit",
                label="Оферта лимит",
                default_value=bool(data.get("oferta_limit", False)),
            )

            dpg.add_checkbox(
                tag="svc_edit_discount_enable",
                label="Указать окончание скидки (не позже сегодня, UTC)",
                default_value=bool(dd_iso),
                callback=cls._on_checkbox_toggle,
                user_data=["svc_edit_discount_date", "svc_edit_discount_time"],
            )
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="svc_edit_discount_date",
                    hint="YYYY-MM-DD",
                    default_value=dd_date,
                    callback=cls._on_date_input_cb,
                    user_data=("svc_edit_discount_date", "svc_edit_discount_err"),
                    show=bool(dd_iso),
                )
                dpg.add_time_picker(
                    tag="svc_edit_discount_time",
                    default_value=dd_time,
                    hour24=True,
                    show=bool(dd_iso),
                )
            dpg.add_text(
                tag="svc_edit_discount_err",
                default_value="",
                color=(255, 120, 120),
                show=False,
            )

            dpg.add_checkbox(
                tag="svc_edit_sell_enable",
                label="Указать окончание продажи (не позже сегодня, UTC)",
                default_value=bool(st_iso),
                callback=cls._on_checkbox_toggle,
                user_data=["svc_edit_sell_date", "svc_edit_sell_time"],
            )
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="svc_edit_sell_date",
                    hint="YYYY-MM-DD",
                    default_value=st_date,
                    callback=cls._on_date_input_cb,
                    user_data=("svc_edit_sell_date", "svc_edit_sell_err"),
                    show=bool(st_iso),
                )
                dpg.add_time_picker(
                    tag="svc_edit_sell_time",
                    default_value=st_time,
                    hour24=True,
                    show=bool(st_iso),
                )
            dpg.add_text(
                tag="svc_edit_sell_err",
                default_value="",
                color=(255, 120, 120),
                show=False,
            )

            dpg.add_input_text(
                tag="svc_edit_price_main",
                default_value=data.get("price_main", ""),
                hint="Базовая цена (строкой)",
            )
            dpg.add_input_int(
                tag="svc_edit_discount_value",
                default_value=int(data.get("discount_value", 0) or 0),
                min_value=0,
                max_value=100,
                label="Скидка",
            )

            dpg.add_combo(
                tag="svc_edit_status",
                items=list(cls.STATUS_UI2RAW.keys()),
                default_value=status_ui_default,
                width=220,
                label="Статус",
            )

            dpg.add_checkbox(
                tag="svc_edit_left_enable",
                label="Указать лимит покупок",
                default_value=left_enable_default,
                callback=cls._on_checkbox_toggle,
                user_data=["svc_edit_left_value"],
            )
            dpg.add_input_int(
                tag="svc_edit_left_value",
                min_value=0,
                default_value=left_default_int,
                show=left_enable_default,
                step=1,
            )

            dpg.add_separator()
            with dpg.group(horizontal=True, tag="svc_edit_btns"):
                dpg.add_button(
                    label="Сохранить",
                    user_data=u_id,
                    callback=lambda s, a, uid: cls._save_service(uid),
                )
                dpg.add_button(
                    label="Удалить",
                    user_data=u_id,
                    callback=lambda s, a, uid: cls._delete_service(uid),
                )
                dpg.add_button(
                    label="Закрыть",
                    callback=lambda: dpg.delete_item(cls._tag + "_modal_edit"),
                )

        ViewportResizeManager.add_callback(
            cls._tag + "_modal_edit", cls._on_modal_edit_resize
        )

    @classmethod
    def _collect_edit_payload(cls) -> dict[str, Any]:
        payload: dict[str, Any] = {}

        name = (dpg.get_value("svc_edit_name") or "").strip()
        if not name:
            raise RuntimeError("Name is required")
        payload["name"] = name

        payload["description"] = dpg.get_value("svc_edit_description") or ""
        payload["oferta_limit"] = bool(dpg.get_value("svc_edit_oferta_limit"))

        if dpg.get_value("svc_edit_discount_enable"):
            date_str = (dpg.get_value("svc_edit_discount_date") or "").strip()
            ok, msg = cls._validate_date_str(date_str)
            if not ok:
                raise RuntimeError(msg)
            tdict = dpg.get_value("svc_edit_discount_time") or cls._now_time_dict()
            payload["discount_date"] = cls._compose_iso_from_date_time(date_str, tdict)
            if not payload["discount_date"]:
                raise RuntimeError("Invalid discount date/time")

        else:
            payload["discount_date"] = None

        if dpg.get_value("svc_edit_sell_enable"):
            date_str = (dpg.get_value("svc_edit_sell_date") or "").strip()
            ok, msg = cls._validate_date_str(date_str)
            if not ok:
                raise RuntimeError(msg)
            tdict = dpg.get_value("svc_edit_sell_time") or cls._now_time_dict()
            payload["sell_time"] = cls._compose_iso_from_date_time(date_str, tdict)
            if not payload["sell_time"]:
                raise RuntimeError("Invalid sell end date/time")

        else:
            payload["sell_time"] = None

        price_main = (dpg.get_value("svc_edit_price_main") or "").strip()
        if not price_main:
            raise RuntimeError("Price is required")
        payload["price_main"] = price_main

        payload["discount_value"] = int(dpg.get_value("svc_edit_discount_value") or 0)

        status_ui = (dpg.get_value("svc_edit_status") or "Выключена").strip()
        payload["status"] = cls.STATUS_UI2RAW.get(status_ui, "off")

        if bool(dpg.get_value("svc_edit_left_enable")):
            payload["left"] = int(dpg.get_value("svc_edit_left_value") or 0)

        else:
            payload["left"] = None

        return payload

    @classmethod
    def _save_service(cls, u_id: str) -> None:
        payload = cls._collect_edit_payload()
        payload["u_id"] = u_id
        APIManager.service_control.edit(**payload)
        cls._refresh()
        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.delete_item(cls._tag + "_modal_edit")

    @classmethod
    def _delete_service(cls, u_id: str) -> None:
        APIManager.service_control.delete(u_id)
        cls._refresh()
        if dpg.does_item_exist(cls._tag + "_modal_edit"):
            dpg.delete_item(cls._tag + "_modal_edit")
