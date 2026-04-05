
import os
import base64
from datetime import datetime

import pytest
from pytest_html import extras
from playwright.sync_api import sync_playwright
from find_proxy import find_working_proxy


@pytest.fixture(scope="session")
def working_proxy():
    """Возвращает строку прокси или None в зависимости от переменной окружения TEST_PROXY_MODE"""
    mode = os.environ.get("TEST_PROXY_MODE", "none")
    if mode == "none":
        return None
    if mode == "auto":
        proxy = find_working_proxy(timeout_sec=10)
        if not proxy:
            pytest.fail("Не удалось найти ни одного рабочего прокси для сайта")
        return proxy
    # mode должен быть в формате ip:port
    return mode

@pytest.fixture(scope="class")
def page(working_proxy):
    """Десктопная версия (1920x1080)"""
    with sync_playwright() as p:

        if working_proxy:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": working_proxy },
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
        else:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )

        page = context.new_page()
        page.set_default_timeout(30000)

        def goto_with_wait(url):
            return page.goto(url, wait_until="networkidle", timeout=90000)

        page.goto_with_wait = goto_with_wait

        yield page

        context.close()
        browser.close()

@pytest.fixture(scope="class")
def mobile_page(working_proxy):
    """Мобильная версия - iPhone 13"""
    with sync_playwright() as p:

        if working_proxy:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": working_proxy },
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
        else:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

        # Эмуляция iPhone 13
        device = p.devices["iPhone 13"]

        context = browser.new_context(
            **device,
        )

        page_obj = context.new_page()
        page_obj.set_default_timeout(30000)

        def goto_with_wait(url):
            return page_obj.goto(url, wait_until="networkidle", timeout=90000)

        page_obj.goto_with_wait = goto_with_wait

        yield page_obj

        context.close()
        browser.close()


""" Функии для отчета """

# Папка для отчетов
REPORT_DIR = "reports"
SCREENSHOT_DIR = os.path.join(REPORT_DIR, "screenshots")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def pytest_configure(config):
    """Настройка HTML-репорта"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = os.path.join(REPORT_DIR, f"report_{timestamp}.html")
    config.option.htmlpath = report_path
    config.option.self_contained_html = True

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук для добавления скриншота и логов при падении теста"""
    outcome = yield
    report = outcome.get_result()

    page = item.funcargs.get("page") or item.funcargs.get("mobile_page")

    if report.when == "call" and report.failed and page:
        test_name = item.name
        timestamp = datetime.now().strftime("%H-%M-%S")
        file_name = f"{test_name}_{timestamp}.png"
        file_path = os.path.join(SCREENSHOT_DIR, file_name)

        # Сохраняем скриншот
        screenshot_bytes = page.screenshot(path=file_path, full_page=True)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode()

        # Добавляем в HTML-репорт
        extra = getattr(report, "extra", [])
        extra.append(extras.image(screenshot_base64, ""))
        extra.append(extras.text(f"URL страницы: {page.url}"))

        # Добавляем только текст ошибки (без полного локатора)
        if call.excinfo is not None:
            extra.append(extras.text(str(call.excinfo.value)))
        
        report.extra = extra