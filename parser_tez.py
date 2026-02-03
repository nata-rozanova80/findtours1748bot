import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TEZ_URL = "https://www.tez-tour.travel/hot/"  # без UTM-хвоста
HOT_1001_URL = "https://www.1001tur.ru/hot/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def get_offers_from_tez():
    """
    Парсит страницу горячих туров Tez Tour и возвращает список словарей:
    {"title": str, "link": str, "source": "Tez"}
    Пока берём только заголовки разделов 'Горящие туры в ...'.
    """
    logger.info("Старт парсинга Tez: %s", TEZ_URL)

    resp = requests.get(TEZ_URL, headers=HEADERS, timeout=15)
    logger.info("Ответ Tez: status=%s, length=%d", resp.status_code, len(resp.text))
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []

    # Заголовки вида "Горящие туры в Турцию", "Горящие туры в Египет", ...
    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)
        if not text.startswith("Горящие туры"):
            continue

        title = text
        # Привяжем ссылку на общий раздел hot как fallback
        link = TEZ_URL

        offers.append(
            {
                "title": title,
                "link": link,
                "source": "Tez",
            }
        )
        logger.debug("Tez: %s (%s)", title, link)

    logger.info("Парсинг Tez завершён, найдено %d записей", len(offers))
    return offers

def get_offers_from_1001tur():
    """
    Парсит страницу 'горящих туров' 1001tur.ru и возвращает список словарей:
    {
        "title": str,  # отель + направление + дата + ночи
        "link": str,   # абсолютная ссылка на тур
        "source": "1001tur",
    }
    """
    logger.info("Старт парсинга 1001tur: %s", HOT_1001_URL)

    resp = requests.get(HOT_1001_URL, headers=HEADERS, timeout=15)
    logger.info("Ответ 1001tur: status=%s, length=%d", resp.status_code, len(resp.text))
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []

    cards = soup.select("a.top-offers__item.top-offers-item-tour")
    logger.info("Найдено %d карточек туров 1001tur", len(cards))

    for a in cards:
        href = a.get("href", "").strip()
        if not href:
            continue

        # href вида //www.1001tur.ru/dayoffer/...
        if href.startswith("//"):
            link = "https:" + href
        elif href.startswith("/"):
            link = "https://www.1001tur.ru" + href
        else:
            link = href

        hotel_el = a.select_one(".top-offers-item-tour__hotelname span")
        location_el = a.select_one(".top-offers-item-tour__location")
        date_el = a.select_one(".top-offers-item-tour__from")
        nights_el = a.select_one(".top-offers-item-tour__duration")
        price_new_el = a.select_one(".top-offers-item-tour__prices-new")

        hotel = hotel_el.get_text(strip=True) if hotel_el else ""
        location = location_el.get_text(strip=True) if location_el else ""
        date_text = date_el.get_text(strip=True) if date_el else ""
        nights_text = nights_el.get_text(strip=True) if nights_el else ""
        price_new = price_new_el.get_text(strip=True) if price_new_el else ""

        # Собираем компактный заголовок
        # Пример: "Nirvana Dolce Vita 5*, Турция, Текирова — 09.05.2026, 8 дней / 7 ночей, 124 455р."
        parts = []
        if hotel:
            parts.append(hotel)
        if location:
            parts.append(location)
        base_title = ", ".join(parts)

        extra = []
        if date_text:
            extra.append(date_text)
        if nights_text:
            extra.append(nights_text)
        if price_new:
            extra.append(price_new)
        if extra:
            title = f"{base_title} — " + ", ".join(extra)
        else:
            title = base_title or link

        offers.append(
            {
                "title": title,
                "link": link,
                "source": "1001tur",
            }
        )
        logger.debug("1001tur: %s (%s)", title, link)

    logger.info("Парсинг 1001tur завершён, найдено %d туров", len(offers))
    return offers