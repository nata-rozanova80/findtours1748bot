# Отдельный скрипт для ручного обновления

# update_offers.py
import logging
from db import init_db
from parser import update_all_offers

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    init_db()
    update_all_offers()
    print("Обновление предложений завершено.")
