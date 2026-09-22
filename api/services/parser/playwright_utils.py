from playwright.sync_api import sync_playwright


def get_page(url):
    """
    Универсальное открытие страницы в Playwright.
    Не содержит никаких селекторов конкретных сайтов.
    """

    print("=" * 50)
    print("PLAYWRIGHT START")
    print("=" * 50)

    p = sync_playwright().start()

    browser = p.chromium.launch(
        headless=False,      # потом можно сделать True
        slow_mo=500
    )

    context = browser.new_context(
        locale="ru-RU",
        viewport={
            "width": 1366,
            "height": 768,
        },
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        ),
    )

    page = context.new_page()

    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    print("OPEN:", url)

    response = page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    print("STATUS:", response.status if response else None)
    print("TITLE :", page.title())
    print("URL   :", page.url)

    return p, browser, page


def close_page(p, browser):
    """
    Корректное закрытие браузера.
    """

    browser.close()
    p.stop()

def wait_page_loaded(page, timeout=10000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except:
        pass