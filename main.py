import argparse
import logging
import os
import platform
import signal
import sys

from colorama import Fore, Style, init

from Code.app import Core


def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}. Starting graceful shutdown...")

    try:
        Core.stop()

    except Exception as e:
        logging.error(f"Error during graceful shutdown: {e}")

    finally:
        sys.exit(0)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname:<7}{Style.RESET_ALL}"
        return super().format(record)


def configure_logging(debug: bool):
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"

    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(log_format)
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(
        level=log_level,
        handlers=[console_handler],
        encoding="utf-8",
    )

    logging.getLogger("websocket").setLevel(logging.WARNING)


def main():
    logging.debug("Starting program...")
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    except Exception as e:
        logging.warning(f"Failed to set up signal handlers: {e}")

    try:
        Core.run()
    except Exception as e:
        logging.error(
            f"Critical error during application execution: {e}",
            exc_info=True,
        )
    finally:
        logging.debug("Application terminated.")


if __name__ == "__main__":
    try:
        init(autoreset=True)

        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        args = parser.parse_args()

        configure_logging(args.debug)

        platform_name = platform.system()

        match platform.system():
            case "Windows":
                os.environ.update(
                    PYTHONIOENCODING="utf-8",
                    PYTHONUTF8="1",
                )

            case "Darwin":
                logging.warning(
                    "S.P.F Base client may have bugs on MacOS. Please report any issues to https://github.com/S-P-F-Base/spf-base-client/issues"
                )

        main()

    except Exception:
        logging.critical("Unhandled exception occurred.", exc_info=True)
        input()
