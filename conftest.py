"""Cấu hình dùng chung cho toàn bộ test suite Lab 9 - Selenium.

- Khởi tạo Chrome WebDriver ở chế độ headless (máy chạy test là VM Linux
  không có màn hình thật).
- Ảnh chụp màn hình được lấy bằng driver.save_screenshot() - tức là ảnh
  render thật của trình duyệt tại thời điểm kiểm chứng, không phải ảnh vẽ lại.
- Workaround mạng sandbox: VM này ra Internet qua egress proxy có chứng chỉ
  MITM và có xác thực (giống Lab 8). Chrome không hỗ trợ nhúng user:pass vào
  --proxy-server nên conftest tự chạy một relay nội bộ (xem proxy_relay.py)
  để gắn Proxy-Authorization khi forward lên proxy thật, đồng thời truyền
  --ignore-certificate-errors cho chứng chỉ MITM của proxy. Trên máy cá
  nhân thông thường, không có proxy thì các tuỳ chọn này tự tắt.
"""
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from proxy_relay import ProxyRelay

BASE_URL = "https://www.saucedemo.com/"
PROJECT_ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"


@pytest.fixture(scope="session")
def proxy_url():
    """Trả về địa chỉ proxy mà Chrome dùng được, hoặc None nếu không cần proxy."""
    raw = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )
    if not raw:
        yield None
        return
    parsed = urlparse(raw)
    if parsed.username:
        # Proxy có xác thực -> Chrome không dùng trực tiếp được, chạy relay
        relay = ProxyRelay(raw).start()
        yield relay.url
        relay.stop()
    else:
        yield raw


@pytest.fixture(scope="function")
def driver(proxy_url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,900")
    options.add_argument("--ignore-certificate-errors")
    if proxy_url:
        options.add_argument(f"--proxy-server={proxy_url}")

    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    drv.set_page_load_timeout(60)
    yield drv
    drv.quit()


def take_screenshot(driver, filename: str) -> Path:
    """Chụp màn hình thật của trình duyệt và lưu vào thư mục screenshots/."""
    # Chờ ngắn để trình duyệt vẽ xong khung hình cuối (tránh chụp trúng lúc
    # trang đang re-render, khung hình chưa kịp sơn chữ/ảnh lên màn hình).
    import time

    time.sleep(1.0)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / filename
    driver.save_screenshot(str(path))
    return path
