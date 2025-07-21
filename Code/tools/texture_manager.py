import dearpygui.dearpygui as dpg

from .config import Config


class TextureManager:
    _static_img_names: list[str] = [
        "\\img\\logo.png",
        "\\img\\light.png",
    ]

    @classmethod
    def load_images(cls):
        cls._load_static_img()

    @classmethod
    def _load_static_img(cls):
        data_path = Config.get_data_dir_str()
        for file in cls._static_img_names:
            x, y, _, data = dpg.load_image(data_path + file)
            with dpg.texture_registry():
                img_tag = f"{file.split('\\')[-1].split('.')[0]}_img"
                dpg.add_static_texture(x, y, data, tag=img_tag)
