import re

def parse_price(text):
    """Парсим '10 000 ₽' -> 10000"""
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0

def collect_prices_from_all_pages(page):
    """Вспомогательный метод для сбора цен со всех страниц"""
    prices = []
    page_num = 1
    main_block = page.locator("main").first

    while True:
        price_elements = main_block.locator("text=₽").all()

        for el in price_elements:
            try:
                price_text = el.inner_text().strip()
                if price_text:
                    price = parse_price(price_text)
                    if price > 0:
                        prices.append(price)
            except:
                continue

        # Проверяем кнопку "Следующая страница"
        next_button = page.locator('button[aria-label="Следующая страница"]').first

        # Если кнопка невидима или disabled - выходим
        if not next_button.is_visible() or next_button.get_attribute("disabled") is not None:
            break

        next_button.click()
        page.wait_for_timeout(2500)
        page.wait_for_load_state("networkidle", timeout=30000)
        page_num += 1

    return prices

def check_category_from_all_pages(category: str, page) -> bool:
    """Возвращает True, если все карточки на всех страницах содержат категорию"""
    page_num = 1
    main_block = page.locator("main").first

    while True:
        # Ищем только карточки
        cards = main_block.locator("div:has(h3)").all()

        for card in cards:
            card_text = card.inner_text().strip()
            if category.lower() not in card_text.lower():
                return False

        next_button = page.locator('button[aria-label="Следующая страница"]').first
        if not next_button.is_visible() or next_button.get_attribute("disabled") is not None:
            break

        next_button.click()
        page.wait_for_timeout(2500)
        page.wait_for_load_state("networkidle", timeout=30000)
        page_num += 1

    return True

def get_total_ads_count(page):
    """Получает общее количество объявлений"""
    # Ищем текст с информацией о пагинации, например: "Показано 1–10 из 16 объявлений"
    pagination_info = page.locator("text=/Показано.*?из.*?объявлений/i").first
    text = pagination_info.inner_text()

    # Ищем число после "из" (например, "из 16")
    match = re.search(r'из\s+(\d+)', text)
    return int(match.group(1))

def check_all_ads_urgent(page) -> bool:
    """
    Проверяет, что все отображаемые объявления имеют метку "Срочно".
    Возвращает True, если все объявления срочные или объявлений нет.
    """
    page_num = 1
    main_block = page.locator("main").first

    while True:
        # Ищем только карточки
        cards = main_block.locator("div:has(h3)").all()

        for card in cards:
            card_text = card.inner_text().strip()
            if "Срочно".lower() not in card_text.lower():
                return False

        next_button = page.locator('button[aria-label="Следующая страница"]').first
        if not next_button.is_visible() or next_button.get_attribute("disabled") is not None:
            break

        next_button.click()
        page.wait_for_timeout(2500)
        page.wait_for_load_state("networkidle", timeout=30000)
        page_num += 1

    return True

def is_dark_theme_active(page) -> bool:
    html = page.locator("html")
    theme = html.get_attribute("data-theme")

    if theme:
        return theme == "dark"

    # fallback
    body = page.locator("body")
    bg = body.evaluate("el => getComputedStyle(el).backgroundColor")
    nums = [int(x) for x in bg.replace("rgb(", "").replace(")", "").split(",")]
    
    return sum(nums) / 3 < 128