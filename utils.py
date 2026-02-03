# utils.py - Логирование работы бота
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,  # можно DEBUG для ещё более подробного вывода
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
