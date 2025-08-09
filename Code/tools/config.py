import json
import logging
import os
import platform
import shutil
from atexit import register
from copy import deepcopy
from pathlib import Path
from platform import system
from typing import Any, Final

logger = logging.getLogger(__name__)


class Config:
    _root_dir: Path = Path(__file__).resolve().parents[2]
    _config_data: dict[str, Any] = {}

    app_version: Final[str] = "v0.2.1"
    _config_serl_ver: Final[str] = "1"

    # region colors
    accent_color: Final[list[int]] = [255, 165, 0, 255]

    # endregion

    @classmethod
    def get_save_dir(cls) -> Path:
        system_name = platform.system()

        if system_name == "Windows":
            local_app_data = os.getenv("LOCALAPPDATA")
            if local_app_data:
                return Path(local_app_data) / "S.P.F Base client"
            else:
                return Path.home() / "AppData/Local/S.P.F Base client"

        elif system_name == "Darwin":
            return Path.home() / "Library/Application Support/S.P.F Base client"

        else:
            return Path.home() / ".config/S.P.F Base client"

    @classmethod
    def get_save_file(cls) -> Path:
        save_fold = cls.get_save_dir()
        save_file = save_fold / "config.json"

        if not save_fold.exists():
            save_fold.mkdir(parents=True, exist_ok=True)

        if not save_file.exists():
            save_file.write_text("{}", encoding="utf-8")

        return save_file

    @classmethod
    def get_refresh_token_form_file(cls) -> str | None:
        save_fold = cls.get_save_dir()
        save_file = save_fold / ".refresh_token"

        if not save_fold.exists():
            save_fold.mkdir(parents=True, exist_ok=True)

        if not save_file.exists():
            return None

        return save_file.read_text(encoding="utf-8")

    @classmethod
    def set_refresh_token_to_file(cls, value: str) -> None:
        save_fold = cls.get_save_dir()
        save_file = save_fold / ".refresh_token"

        if not save_fold.exists():
            save_fold.mkdir(parents=True, exist_ok=True)

        save_file.write_text(value, encoding="utf-8")

    @classmethod
    def get_data_dir_str(cls) -> str:
        path = cls._root_dir / "Data"
        path_str = str(path)

        if system() == "Windows" and not path_str.isascii():
            # Since our DPG does not digest non-ascii path's,
            # we create a folder in the root of the disk where the script is located
            # and then delete it when we finish our work
            temp_folder = Path(path.anchor) / "spf_temp_data"
            temp_folder.mkdir(exist_ok=True)

            shutil.copytree(path, temp_folder, dirs_exist_ok=True)

            def clean_up_font_fold():
                try:
                    shutil.rmtree(temp_folder)

                except Exception:
                    pass

            register(clean_up_font_fold)
            path_str = str(temp_folder)

        @classmethod
        def tmp(cls) -> str:
            return path_str

        cls.get_data_dir_str = tmp
        return path_str

    @classmethod
    def get_data_path(cls) -> Path:
        return cls._root_dir / "Data"

    @classmethod
    def get_root_path(cls) -> Path:
        return cls._root_dir

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._config_data.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls._config_data[key] = value

    @classmethod
    def save(cls) -> None:
        cls._serialization()

    @classmethod
    def load(cls) -> None:
        cls._deserialization()

    # region serialization
    @classmethod
    def _serialization(cls) -> None:
        data_to_dump = deepcopy(cls._config_data)
        data_to_dump["_config_serl_ver"] = cls._config_serl_ver

        for key, value in list(data_to_dump.items()):
            if isinstance(value, Path):
                data_to_dump[key] = "__PATH__::" + str(value)

        save_file = cls.get_save_file()
        save_file.write_text(json.dumps(data_to_dump), encoding="utf-8")

    # endregion

    # region deserialization
    @classmethod
    def _deserialization(cls) -> None:
        save_file = cls.get_save_file()
        data_to_process = json.loads(save_file.read_text(encoding="utf-8"))
        serl_ver = data_to_process.get("_config_serl_ver", None)

        if serl_ver is None:
            return

        func_name = f"_des_v{serl_ver}"
        if not hasattr(cls, func_name):
            logger.error(f"Config version {serl_ver} cannot be processed")
            return

        func = getattr(cls, func_name)

        if callable(func):
            func(data_to_process)

        else:
            logger.error(f"{func_name} is not a function")

    @classmethod
    def _des_v1(cls, data: dict) -> None:
        data.pop("_config_serl_ver")

        for key, value in list(data.items()):
            if isinstance(value, str) and value.startswith("__PATH__::"):
                data[key] = Path(value.removeprefix("__PATH__::"))

        cls._config_data = data

    # endregion
