import logging
import sqlite3

import requests
from bs4 import BeautifulSoup

from config import DB_PATH
from parser_tez import get_offers_from_tez, get_offers_from_1001tur

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

ANEX_URL = "https://anextour.ru/actions"
CORAL_URL = "https://www.coral.ru/poleznaya-informatsiya/offers/hot-offers/"

def get_offers_from_coral():
    logger.info("Старт парсинга Coral: %s", CORAL_URL)

    resp = requests.get(CORAL_URL, headers=HEADERS, timeout=15)
    logger.info("Ответ Coral: status=%s, length=%d", resp.status_code, len(resp.text))
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    offers = []

    # Ищем карточки напрямую по классу promo-card card coral
    cards = soup.select("li.promo-card.card.coral")
    logger.info("Найдено %d карточек акций Coral (li.promo-card.card.coral)", len(cards))

    if not cards:
        # На случай, если li нет, но есть article с promo-card__title
        cards = soup.select("article .promo-card__content")
        logger.info("Резервный поиск: найдено %d блоков promo-card__content", len(cards))

    for card in cards:
        title_el = card.select_one("h5.promo-card__title")
        link_el = card.select_one("a.promo-card__link[href]")
        if not title_el or not link_el:
            href_debug = link_el.get("href") if link_el else None
            logger.debug("Пропущена карточка без title или link, href=%s", href_debug)
            continue

        title = title_el.get_text(strip=True)
        href = link_el.get("href", "").strip()
        if not href:
            continue

        if href.startswith("/"):
            link = "https://www.coral.ru" + href
        else:
            link = href

        offers.append(
            {
                "title": title,
                "link": link,
                "source": "Coral",
            }
        )
        logger.debug("Акция Coral: %s (%s)", title, link)

    logger.info("Парсинг Coral завершён, найдено %d акций", len(offers))
    return offers

def get_offers_from_anex():
    logger.info("Старт парсинга ANEX: %s", ANEX_URL)

    resp = requests.get(ANEX_URL, headers=HEADERS, timeout=15)
    logger.info("Ответ ANEX: status=%s, length=%d", resp.status_code, len(resp.text))
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # ВРЕМЕННО: сохраним первые 500 символов, чтобы увидеть, что реально пришло
    logger.debug("Начало HTML: %s", resp.text[:500].replace("\n", " "))

    offers = []

    ul = soup.select_one("ul#action-cards")
    if not ul:
        logger.warning("Не найден ul#action-cards на странице ANEX")
        return offers

    cards = ul.select("li a[href]")
    logger.info("Найдено %d карточек акций ANEX", len(cards))

    for a in cards:
        href = a.get("href")
        logger.debug("Карточка href=%s", href)

        title_el = a.select_one("h3")
        if not title_el:
            logger.debug("Пропущена карточка без h3: %s", href)
            continue

        title = title_el.get_text(strip=True)
        link = (href or "").strip()
        if not link:
            logger.debug("Пропущена карточка без ссылки")
            continue

        if link.startswith("/"):
            link = "https://anextour.ru" + link

        offers.append(
            {
                "title": title,
                "link": link,
                "source": "ANEX",
            }
        )
        logger.debug("Акция ANEX: %s (%s)", title, link)

    logger.info("Парсинг ANEX завершён, найдено %d акций", len(offers))
    return offers



def save_offers(offers):
    """
    Сохраняет список предложений в БД (локально, пока без db.py).
    Ожидает список словарей с ключами title, link, source.
    """
    if not offers:
        logger.info("save_offers: список пуст, ничего не сохраняем")
        return

    logger.info("save_offers: сохраняем %d предложений", len(offers))
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        for offer in offers:
            logger.debug(
                "Сохраняем предложение: %s (%s)",
                offer["title"],
                offer["link"],
            )
            cur.execute(
                """
                INSERT OR IGNORE INTO offers (title, link, source)
                VALUES (?, ?, ?)
                """,
                (
                    offer["title"],
                    offer["link"],
                    offer.get("source", "ANEX"),
                ),
            )
        conn.commit()
        logger.info("save_offers: коммит успешен")
    finally:
        conn.close()


def update_all_offers():
    """
    Обновляет БД свежими предложениями со всех источников.
    Сейчас: ANEX (пока пустой) + Coral.
    """
    all_offers = []

    # ANEX (оставляем, даже если сейчас возвращает 0)
    # try:
    #     anex_offers = get_offers_from_anex()
    #     all_offers.extend(anex_offers)
    # except Exception as e:
    #     logger.exception("Ошибка при парсинге ANEX: %s", e)

    # Coral
    try:
        coral_offers = get_offers_from_coral()
        all_offers.extend(coral_offers)
    except Exception as e:
        logger.exception("Ошибка при парсинге Coral: %s", e)

    if all_offers:
        save_offers(all_offers)
    else:
        logger.warning("update_all_offers: парсеры вернули пустой список")

    # tez
    try:
        tez_offers = get_offers_from_tez()
        all_offers.extend(tez_offers)
    except Exception as e:
        logger.exception("Ошибка при парсинге Tez: %s", e)

    if all_offers:
        save_offers(all_offers)
    else:
        logger.warning("update_all_offers: парсеры вернули пустой список")

    # 1001 tour
    try:
        tur1001_offers = get_offers_from_1001tur()
        all_offers.extend(tur1001_offers)
    except Exception as e:
        logger.exception("Ошибка при парсинге 1001tur: %s", e)

    if all_offers:
        save_offers(all_offers)
    else:
        logger.warning("update_all_offers: парсеры вернули пустой список")