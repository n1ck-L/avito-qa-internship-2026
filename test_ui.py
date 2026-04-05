import pytest
from helpers import *

BASE_URL = "https://cerulean-praline-8e5aa6.netlify.app"

''' Тест доступности сервиса '''
def test_page_loads_list(page):
    """Простая проверка загрузки главной страницы через прокси"""

    # Переходим на сайт
    page.goto_with_wait(BASE_URL)

    # Делаем скриншот для отладки
    # page.screenshot(path="test_page_loads_list.png", full_page=True)

    # Базовые проверки
    assert BASE_URL in page.url, f"Страница не загрузилась. Ожидали {BASE_URL}, получили {page.url}"
    assert page.title() != "", "Страница не загрузилась. Заголовок страницы пустой"
    assert page.locator("body").is_visible(), "Страница не загрузилась. Body невидим"

''' Десктопная версия сайта '''

@pytest.fixture(scope="class")
def price_filter_page(page):
    page.goto_with_wait(BASE_URL)
    
    min_input = page.get_by_placeholder("От").first
    max_input = page.get_by_placeholder("До").first
    
    return {
        "page": page,
        "min_input": min_input,
        "max_input": max_input
    }

class TestPriceFilterRange:

    def test_price_range_results(self, price_filter_page):
        """Фильтр по корректному диапазону цен показывает только товары в диапазоне"""
        
        page = price_filter_page["page"]
        min_input = price_filter_page["min_input"]
        max_input = price_filter_page["max_input"]

        min_price = 10000
        max_price = 50000

        min_input.scroll_into_view_if_needed()
        min_input.fill(str(min_price))

        max_input.scroll_into_view_if_needed()
        max_input.fill(str(max_price))

        page.keyboard.press("Enter")

        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Извлекаем цены со всех страниц
        prices = collect_prices_from_all_pages(page)

        out_of_range = [p for p in prices if not (min_price <= p <= max_price)]
        
        assert len(out_of_range) == 0, f"Есть цены вне диапазона {min_price}-{max_price}₽: {out_of_range}"


    @pytest.mark.parametrize("min_price, max_price", [
        (10000, 0),
        (-1, -1),
        (100, -1),
        (-1, 1000),
    ])
    def test_incorrect_price_range(self, price_filter_page, min_price, max_price):
        """Некорректный диапазон цен - должен показываться блок 'Объявления не найдены'"""
        
        page = price_filter_page["page"]
        min_input = price_filter_page["min_input"]
        max_input = price_filter_page["max_input"]

        # Заполняем и применяем фильтр
        min_input.scroll_into_view_if_needed()
        min_input.fill(str(min_price))

        max_input.scroll_into_view_if_needed()
        max_input.fill(str(max_price))

        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Проверки пустой страницы
        main_block = page.locator("main").first

        # Нет ни одной цены
        assert main_block.locator("text=₽").count() == 0, \
            f"Ожидалось 0 объявлений для ({min_price}, {max_price}), но найдены цены"

        # Только один основной блок
        assert main_block.locator("div").count() == 1, \
            f"Ожидался ровно 1 блок на странице, а найдено больше"

        # Блок "Объявления не найдены" видим
        empty_block = main_block.locator("div").first
        assert empty_block.is_visible(), "Блок 'Объявления не найдены' не появился"

        assert empty_block.locator("p").filter(has_text="Объявления не найдены").is_visible(), \
            "Не найден текст 'Объявления не найдены'"

        # Кнопка сброса фильтров присутствует
        assert empty_block.locator("button").filter(has_text="Сбросить фильтры").is_visible(), \
            "Кнопка 'Сбросить фильтры' отсутствует"
            

@pytest.fixture(scope="class")
def listing_page(page):
    page.goto_with_wait(BASE_URL)
    sort_select = page.locator("label:has-text('Сортировать по') + select")
    order_select = page.locator("label:has-text('Порядок') + select")
    
    return {
        "page": page,
        "sort_select": sort_select,
        "order_select": order_select
    }

class TestSortByPrice:

    def test_sort_select_exist(self, listing_page):
        """Проверка наличия селекта Соритровать по"""
        sort_select = listing_page['sort_select']
        assert sort_select.count() > 0, "Селект 'Сортировать по' не найден"

    def test_order_select_exist(self, listing_page):
        """Проверка наличия селекта Порядок"""
        order_select = listing_page['order_select']
        assert order_select.count() > 0, "Селект 'Порядок' не найден"

    def test_sort_options_exist(self, listing_page):
        """Проверка наличия категории Цене в селекте Сортировать по"""
        sort_select = listing_page['sort_select']
        options = sort_select.locator("option").all_inner_texts()
        assert "Цене" in options, f"Ожидали 'Цене' в опциях, получили: {options}"

    def test_order_options_exist(self, listing_page):
        """Проверка наличия категорий По возрастанию и По убыванию в селекте Порядок"""
        order_select = listing_page['order_select']
        options = order_select.locator("option").all_inner_texts()
        assert "По возрастанию" in options, f"Ожидали 'По возрастанию' в опциях, получили: {options}"
        assert "По убыванию" in options, f"Ожидали 'По убыванию' в опциях, получили: {options}"

    def test_sort_by_price_ascending(self, listing_page):
        """Сортировка по возрастанию цены"""
        
        # Устанавливаем нужный option
        sort_select = listing_page['sort_select']
        sort_select.select_option(label="Цене")

        # Устанавливаем нужный option
        order_select = listing_page['order_select']
        order_select.select_option(label="По возрастанию")

        page = listing_page['page']
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Извлекаем цены со всех страниц
        prices = collect_prices_from_all_pages(page)
        
        # Проверяем, что цены отсортированы по возрастанию
        sorted_prices = sorted(prices)
        assert prices == sorted_prices, f"Цены не отсортированы по возрастанию"


    def test_sort_by_price_descending(self, listing_page):
        """Сортировка по убыванию цены"""
        
        # Устанавливаем нужный option
        sort_select = listing_page['sort_select']
        sort_select.select_option(label="Цене")

        # Устанавливаем нужный option
        order_select = listing_page['order_select']
        order_select.select_option(label="По убыванию")

        page = listing_page['page']
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Извлекаем цены со всех страниц
        prices = collect_prices_from_all_pages(page)
        
        # Проверяем, что цены отсортированы по убыванию
        sorted_prices = sorted(prices, reverse=True)
        assert prices == sorted_prices, f"Цены не отсортированы по убыванию"


    def test_sort_stability_on_refresh(self, listing_page):
        """Стабильность сортировки при обновлении"""
        
        # Устанавливаем нужный option
        sort_select = listing_page['sort_select']
        sort_select.select_option(label="Цене")

        # Устанавливаем нужный option
        order_select = listing_page['order_select']
        order_select.select_option(label="По возрастанию")

        page = listing_page['page']
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Сохраняем цены до обновления
        prices_before = collect_prices_from_all_pages(page)

        # Обновляем страницу
        page.reload()

        # Возвращаемся на первую странциу
        next_button = page.locator('button[aria-label="Первая страница"]').first
        next_button.click()
        page.wait_for_timeout(2500)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Проверяем, что селекты сохранили значения 
        sort_select_after = page.locator("label:has-text('Сортировать по') + select")
        order_select_after = page.locator("label:has-text('Порядок') + select")

        selected_sort_label = sort_select_after.locator("option:checked").inner_text()
        selected_order_label = order_select_after.locator("option:checked").inner_text()
        assert selected_sort_label == "Цене", "Параметр сортировки не сохранился"
        assert selected_order_label == "По возрастанию", "Параметр порятка не сохранился"

        # Если сортировка сохранилась - проверяем порядок цен
        prices_after = collect_prices_from_all_pages(page)
        assert prices_before == prices_after, "Сортировка не сохранилась после обновления"


@pytest.fixture(scope="class")
def category_prepare(page):
    page.goto_with_wait(BASE_URL)

    category_select = page.locator("label:has-text('Категория') + select")

    all_options = category_select.locator("option").all_inner_texts()
    categories = [opt for opt in all_options if opt not in ["Все", "Все категории", ""]]

    return { 
        "page": page,
        "category_select": category_select,
        "categories": categories
    }

class TestCategoryFilter:

    def test_category_exist(self, category_prepare):
        """Проверка наличия Категории"""
        category_select = category_prepare['category_select']
        assert category_select.count() > 0, "Селект 'Категория' не найден"
    
    def test_category_options_exist(self, category_prepare):
        """Проверка наличия опций категорий"""
        categories = category_prepare['categories']
        assert len(categories) > 0, f"Ожидали категории, получили"

    def test_filter_by_single_category(self, category_prepare):
        """Фильтрация по одной категории"""
        
        # Получаем список категорий исключая "Все"
        categories = category_prepare['categories']
        assert len(categories) > 0, "Нет доступных категорий для тестирования"
        
        page = category_prepare['page']
        category_select = category_prepare['category_select']
        
        # Проверяем каждую категорию
        for category in categories:
            # Выбираем категорию
            category_select.select_option(label=category)
            
            page.wait_for_timeout(1000)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Проверяем, что есть объявления
            main_block = page.locator("main").first
            has_ads = main_block.locator("text=₽").count() > 0
            
            if has_ads:
                assert check_category_from_all_pages(category, page), f"Не все карточки соответсвуют категории {category}"

        # Возвращаемся на первую странциу
        next_button = page.locator('button[aria-label="Первая страница"]').first
        next_button.click()
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)
        

    def test_change_category(self, category_prepare):
        """Смена категории"""

        category_select = category_prepare['category_select']

        # Получаем доступные категории
        categories = category_prepare['categories']
        assert len(categories) >= 2, "Недостаточно категорий для теста смены"
        
        category_a = categories[0]
        category_b = categories[1]
        
        # Выбираем категорию A
        category_select.select_option(label=category_a)

        page = category_prepare['page']
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)
        
        # Меняем на категорию B
        category_select.select_option(label=category_b)
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)
        
        # Проверяем, что список обновился
        current_category = category_select.locator("option:checked").inner_text()
        assert current_category == category_b, f"Категория не сменилась: {current_category}"
        assert check_category_from_all_pages(category_b, page), f"Категория не сменилась"

        # Возвращаемся на первую странциу
        next_button = page.locator('button[aria-label="Первая страница"]').first
        next_button.click()
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)


    def test_reset_category_filter(self, category_prepare):
        """Сброс фильтра категории"""

        # Сбрасываем категорию
        category_select = category_prepare['category_select']
        category_select.select_option(label="Все категории")

        page = category_prepare['page']
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Получаем изначальное количество объявлений
        initial_count = get_total_ads_count(page)
        
        # Выбираем категорию
        categories = category_prepare['categories']
        assert len(categories) > 0, "Нет категорий для теста"
        
        category = categories[0]
        category_select.select_option(label=category)
        page.wait_for_timeout(1000)
        
        # Сбрасываем категорию
        category_select.select_option(label="Все категории")
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)
        
        # Проверяем, что отображаются все объявления
        reset_count = get_total_ads_count(page)
        
        # После сброса должно быть больше или равно объявлений
        assert reset_count == initial_count, f"Сброс не работает: {reset_count} != {initial_count}"
        
        # Проверяем, что селект сбросился на "Все"
        selected = category_select.locator("option:checked").inner_text()
        assert selected in ["Все", "Все категории"], f"Категория не сбросилась: {selected}"


@pytest.fixture(scope="class")
def urgent_toggle_prepare(page):
    page.goto_with_wait(BASE_URL)
    label = page.locator("label").filter(has_text="срочные")
    toggle = label.locator("input[type='checkbox']")

    return {
        "page": page,
        "toggle": toggle,
        "label": label
    }

class TestUrgentToggle:

    def test_urgent_toggle_exists(self, urgent_toggle_prepare):
        """Проверка наличия тогла 'Только срочные' на странице."""
        toggle = urgent_toggle_prepare["toggle"]
        assert toggle.count() > 0, "Тогл 'Только срочные' не найден"

    def test_turn_on_urgent_only(self, urgent_toggle_prepare):
        """Включение фильтра Только срочные"""
        page = urgent_toggle_prepare["page"]
        label = urgent_toggle_prepare["label"]
        toggle = urgent_toggle_prepare["toggle"]

        # Включаем тогл
        label.click(force=True)
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Проверяем, что установился тогл
        assert toggle.is_checked(), "Тогл не установлен"

        # Проверяем, что отображаются только срочные объявления
        assert check_all_ads_urgent(page), "После включения тогла показаны не только срочные объявления"


    def test_turn_off_urgent_only(self, urgent_toggle_prepare):
        """Выключение тогла"""
        page = urgent_toggle_prepare["page"]
        label = urgent_toggle_prepare["label"]
        toggle = urgent_toggle_prepare["toggle"]

        # Включаем тогл
        if not toggle.is_checked():
            label.click(force=True)
            page.wait_for_timeout(1000)
            page.wait_for_load_state("networkidle", timeout=30000)

        # Выключаем тогл
        label.click(force=True)
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Проверяем, что тогл выключен
        assert not toggle.is_checked(), "Тогл не установлен"

        # Проверяем, что отображаются только срочные объявления
        assert not check_all_ads_urgent(page), "После выключения тогла показаны только срочные объявления"


@pytest.fixture(scope="class")
def stats_page(page):
    page.goto_with_wait(BASE_URL)
    
    # Переход в раздел "Статистика"
    stats_button = page.locator('span:has-text("Статистика")').first
    stats_button.click(force=True)
    page.wait_for_timeout(2000)
    page.wait_for_load_state("networkidle", timeout=30000)

    # page.screenshot(path="test_page_loads_list.png", full_page=True)

    # Основные элементы управления таймером и обновлением
    refresh_button = page.locator('button:has-text("Обновить"), button[title*="Обновить"]').first
    stop_timer_button = page.locator('button:has-text("Отключить"), button[title*="Отключить"]').first
    start_timer_button = page.locator('button:has-text("Включить"), button[title*="Включить"]').first

    # Текст таймера: "Обновление через: 4:49"
    timer_label = page.get_by_text("Обновление через:").first
    timer_value = timer_label.locator("..").get_by_text(re.compile(r"\d+:\d{2}")).first

    # Прогресс-бар
    progress_container = page.locator('div:has(> div[style*="width"])').filter(
        has=page.locator('div[style*="width:"]')
    ).first
    progress_fill = progress_container.locator('div[style*="width"]').first
    
    return {
        "page": page,
        "refresh_button": refresh_button,
        "stop_timer_button": stop_timer_button,
        "start_timer_button": start_timer_button,
        "timer_value": timer_value,
        "progress_fill": progress_fill,
    }

class TestStatsTimer:

    def test_refresh_button_exists(self, stats_page):
        """Проверка наличия кнопки 'Обновить' на странице"""
        refresh_button = stats_page['refresh_button']
        assert refresh_button.count() > 0, "Кнопка 'Обновить' не найдена"

    def test_timer_manage_button_exists(self, stats_page):
        """Проверка наличия кнопки управления таймером на странице"""
        stop_timer_button = stats_page['stop_timer_button']
        start_timer_button = stats_page['start_timer_button']
        assert stop_timer_button.count() > 0 or start_timer_button.count() > 0, \
            "Кнопка управления таймером не найдена"
        
    def test_manual_refresh_works(self, stats_page):
        """Ручное обновление статистики кнопкой 'Обновить'"""
        
        page = stats_page["page"]
        refresh_button = stats_page["refresh_button"]
        timer_value = stats_page["timer_value"]
        progress_fill = stats_page["progress_fill"]

        page.wait_for_timeout(1000)

        refresh_button.click(force=True)
        current_timer_value = timer_value.inner_text()
        style_value = progress_fill.get_attribute("style")
        current_progress_value = re.search(r"width:\s*([\d.]+)%", style_value).group(1)

        assert current_timer_value == "5:00", f"Данные таймера не обновились после нажатия кнопки 'Обновить': {current_timer_value}"
        assert current_progress_value  == "0", f"Данные прогресс-бара не обновились после нажатия кнопки 'Обновить': {current_progress_value}"

    def test_stop_timer_works(self, stats_page):
        """Остновка таймера"""
        
        page = stats_page["page"]
        stop_timer_button = stats_page["stop_timer_button"]
        timer_value = stats_page["timer_value"]
        progress_fill = stats_page["progress_fill"]

        stop_timer_button.click(force=True)

        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        no_auto_div = page.locator('div:has-text("Автообновление выключено")').first

        assert no_auto_div.count() > 0, f"Не появился блок с сообщением 'Автообновление выключено'"
        assert not timer_value.is_visible(), f"Таймер не остановился"
        assert not progress_fill.is_visible(), f"Прогресс-бар виден"

    def test_start_timer_works(self, stats_page):
        """Запуск таймера"""
        
        page = stats_page["page"]
        stop_timer_button = stats_page["stop_timer_button"]
        start_timer_button = stats_page["start_timer_button"]
        timer_value = stats_page["timer_value"]
        progress_fill = stats_page["progress_fill"]

        if stop_timer_button.is_visible():
            stop_timer_button.click(force=True)
            page.wait_for_timeout(1000)
            page.wait_for_load_state("networkidle", timeout=30000)

        start_timer_button.click(force=True)

        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)
        no_auto_div = page.locator('div:has-text("Автообновление выключено")').first

        page.screenshot(path="test_page_loads_list.png", full_page=True)

        assert not no_auto_div.is_visible(), f"Остался блок с сообщением 'Автообновление выключено'"
        assert timer_value.is_visible(), f"Таймер не запустился"
        assert progress_fill.is_visible(), f"Прогресс-бар остался"
    

''' Мобильная версия сайта '''

@pytest.fixture(scope="class")
def mobile_prepare(mobile_page):
    mobile_page.goto_with_wait(BASE_URL)
    toggle_dark = mobile_page.locator('button[aria-label*="Switch"], button[title*="Switch"], button:has-text("Темная")').first
    toggle_light = mobile_page.locator('button[aria-label*="Switch"], button[title*="Switch"], button:has-text("Светлая")').first

    return {
        "page": mobile_page,
        "toggle_dark": toggle_dark,
        "toggle_light": toggle_light
    }

class TestThemeSwitchMobile:

    def test_dark_theme_toggle_exists(self, mobile_prepare):
        """Проверка наличия тогла переключения темы на мобильной версии"""
        toggle_dark = mobile_prepare["toggle_dark"]
        toggle_light = mobile_prepare["toggle_light"]

        assert toggle_dark.count() > 0 or toggle_light.count() > 0, "Тогл переключения темы не найден на мобильной версии"

    def test_enable_dark_theme_on_mobile(self, mobile_prepare):
        """Включение тёмной темы"""
        page = mobile_prepare['page']
        toggle = mobile_prepare['toggle_dark']
        
        # Включаем тёмную тему
        toggle.click(force=True)
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        assert is_dark_theme_active(page), "Тёмная тема не применилась на мобильном устройстве"

    def test_disable_dark_theme_on_mobile(self, mobile_prepare):
        """Включение светлой темы"""
        page = mobile_prepare['page']
        toggle_light = mobile_prepare['toggle_light']
        toggle_dark = mobile_prepare['toggle_dark']

        if not toggle_light.is_visible():
            toggle_dark.click(force=True)
            page.wait_for_timeout(1000)
            page.wait_for_load_state("networkidle", timeout=30000)
        
        # Включаем светлой тему
        toggle_light.click(force=True)
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        assert not is_dark_theme_active(page), "Светлая тема не применилась на мобильном устройстве"

    def test_refresh_theme_on_mobile(self, mobile_prepare):
        """Сохранение темы"""
        page = mobile_prepare['page']
        toggle_light = mobile_prepare['toggle_light']
        toggle_dark = mobile_prepare['toggle_dark']

        if toggle_light.is_visible():
            toggle = toggle_light
        else:
            toggle = toggle_dark

        toggle.click(force=True)
        is_dark = False if toggle == toggle_dark else True  # после клика поемняется тема, поэтому инвертируем
        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle", timeout=30000)

        page.reload()
        page.wait_for_timeout(1000) 
        page.wait_for_load_state("networkidle", timeout=30000)
        
        if is_dark:
            assert is_dark_theme_active(page), "Тёмная тема не сохранилась на мобильном устройстве после обновления"
        else:
            assert not is_dark_theme_active(page), "Светлая тема не сохранилась на мобильном устройстве после обновления"
