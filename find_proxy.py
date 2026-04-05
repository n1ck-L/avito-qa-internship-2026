import re
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def get_fast_ru_https_proxies(max_speed_ms: int = 200):
    """
    Парсит proxymania.su и возвращает быстрые RU HTTPS и SOCKS5 прокси
    """

    url = "https://proxymania.su/free-proxy?type=&country=RU&speed="

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        html = resp.text
    except:
        return []

    rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL | re.IGNORECASE)

    proxies = []

    for row in rows:
        row_lower = row.lower()
        if "russia" not in row_lower and "🇷🇺" not in row:
            continue

        # IP:PORT
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})', row)
        if not ip_match:
            continue
        proxy_str = ip_match.group(1)

        # Тип
        type_match = re.search(r'(HTTPS?|SOCKS5)', row, re.IGNORECASE)
        proxy_type = type_match.group(1).upper() if type_match else "HTTP"

        # Скорость
        speed_match = re.search(r'(\d+)\s*ms', row)
        speed = int(speed_match.group(1)) if speed_match else 999

        if proxy_type in ("HTTPS", "HTTP") and speed <= max_speed_ms:
            proxies.append(f"http://{proxy_str}")
        elif proxy_type in ("SOCKS5") and speed <= max_speed_ms:
            proxies.append(f"socks5://{proxy_str}")

    return proxies[:25]  # берём максимум 25 самых быстрых


def find_working_proxy(target_url: str = "https://cerulean-praline-8e5aa6.netlify.app",
                       timeout_sec: int = 5) -> str | None:
    """
    Проверяет каждый прокси с таймаутом 5 секунд.
    Возвращает строку вида "http://ip:port" или None.
    """
    proxy_list = get_fast_ru_https_proxies()

    if not proxy_list:
        return None

    for proxy_url in proxy_list:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={"server": proxy_url},
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )

                context = browser.new_context(viewport={"width": 1280, "height": 720})
                page = context.new_page()
                page.set_default_timeout(timeout_sec * 1000 + 2000)  # небольшой запас

                # Пытаемся загрузить сайт за 5 секунд
                page.goto(target_url, wait_until="networkidle", timeout=timeout_sec * 1000)

                # Дополнительная проверка, что страница действительно загрузилась
                if page.locator("body").is_visible() and len(page.content()) > 500:
                    context.close()
                    browser.close()
                    return proxy_url

                context.close()
                browser.close()

        except PlaywrightTimeout:
            pass  # таймаут - пробуем следующий прокси
        except Exception:
            pass  # любая другая ошибка - следующий

    return None