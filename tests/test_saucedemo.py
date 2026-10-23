"""Lab 9 - Bộ test tự động bằng Selenium cho website https://www.saucedemo.com/

SauceDemo là website demo được xây dựng chuyên cho việc học/thực hành
automation testing. Tài khoản dùng trong bài được công bố công khai ngay
trên trang đăng nhập của website:
    - standard_user / secret_sauce   (tài khoản chuẩn)
    - locked_out_user / secret_sauce (tài khoản bị khoá, dùng cho test lỗi)

Gồm 06 test case:
    TC01 - Đăng nhập thành công
    TC02 - Đăng nhập thất bại (sai mật khẩu + tài khoản bị khoá)
    TC03 - Thêm sản phẩm vào giỏ hàng
    TC04 - Xoá sản phẩm khỏi giỏ hàng
    TC05 - Sắp xếp sản phẩm theo giá tăng dần
    TC06 - Checkout hoàn chỉnh và đăng xuất

Mỗi test đều chụp ảnh màn hình thật bằng driver.save_screenshot() tại
bước kiểm chứng và lưu vào thư mục screenshots/.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from conftest import BASE_URL, take_screenshot

VALID_USER = "standard_user"
LOCKED_USER = "locked_out_user"
PASSWORD = "secret_sauce"
BACKPACK_ID = "sauce-labs-backpack"
BACKPACK_NAME = "Sauce Labs Backpack"


def login(driver, username, password):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 15)
    wait.until(EC.visibility_of_element_located((By.ID, "user-name"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "login-button").click()


def login_success(driver):
    login(driver, VALID_USER, PASSWORD)
    WebDriverWait(driver, 15).until(EC.url_contains("inventory"))


# ---------------------------------------------------------------- TC01
def test_tc01_login_success(driver):
    """TC01: Đăng nhập thành công với standard_user -> vào trang inventory."""
    login_success(driver)

    assert "inventory" in driver.current_url
    items = driver.find_elements(By.CLASS_NAME, "inventory_item")
    assert len(items) == 6, f"Mong đợi 6 sản phẩm, thấy {len(items)}"
    title = driver.find_element(By.CLASS_NAME, "title").text
    assert title == "Products"

    take_screenshot(driver, "tc01-login-success.png")


# ---------------------------------------------------------------- TC02
def test_tc02_login_failure(driver):
    """TC02: Đăng nhập thất bại phải hiện thông báo lỗi rõ ràng.

    Kiểm tra 2 trường hợp: sai mật khẩu và tài khoản bị khoá (locked_out_user).
    """
    # Trường hợp 1: sai mật khẩu
    login(driver, VALID_USER, "wrong_password")
    wait = WebDriverWait(driver, 15)
    error = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-test="error"]'))
    )
    assert "Username and password do not match" in error.text
    assert "inventory" not in driver.current_url
    take_screenshot(driver, "tc02-login-wrong-password.png")

    # Trường hợp 2: tài khoản bị khoá
    login(driver, LOCKED_USER, PASSWORD)
    error = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-test="error"]'))
    )
    assert "locked out" in error.text.lower()
    take_screenshot(driver, "tc02-login-locked-out.png")


# ---------------------------------------------------------------- TC03
def test_tc03_add_to_cart(driver):
    """TC03: Thêm sản phẩm vào giỏ -> badge giỏ hàng = 1 và sản phẩm có trong giỏ."""
    login_success(driver)

    driver.find_element(By.ID, f"add-to-cart-{BACKPACK_ID}").click()

    badge = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
    )
    assert badge.text == "1"

    driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
    WebDriverWait(driver, 10).until(EC.url_contains("cart"))
    cart_items = driver.find_elements(By.CLASS_NAME, "cart_item")
    assert len(cart_items) == 1
    name = driver.find_element(By.CLASS_NAME, "inventory_item_name").text
    assert name == BACKPACK_NAME

    take_screenshot(driver, "tc03-add-to-cart.png")


# ---------------------------------------------------------------- TC04
def test_tc04_remove_from_cart(driver):
    """TC04: Xoá sản phẩm khỏi giỏ -> giỏ trống, badge biến mất."""
    login_success(driver)
    driver.find_element(By.ID, f"add-to-cart-{BACKPACK_ID}").click()
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
    )
    driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
    WebDriverWait(driver, 10).until(EC.url_contains("cart"))
    assert len(driver.find_elements(By.CLASS_NAME, "cart_item")) == 1

    driver.find_element(By.ID, f"remove-{BACKPACK_ID}").click()

    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CLASS_NAME, "cart_item")) == 0
    )
    assert len(driver.find_elements(By.CLASS_NAME, "cart_item")) == 0
    badges = driver.find_elements(By.CLASS_NAME, "shopping_cart_badge")
    assert len(badges) == 0 or not badges[0].is_displayed()

    take_screenshot(driver, "tc04-remove-from-cart.png")


# ---------------------------------------------------------------- TC05
def test_tc05_sort_by_price_low_to_high(driver):
    """TC05: Sắp xếp theo giá tăng dần (Price: low to high) -> thứ tự giá đúng."""
    login_success(driver)

    select = Select(driver.find_element(By.CLASS_NAME, "product_sort_container"))
    select.select_by_value("lohi")

    WebDriverWait(driver, 10).until(
        lambda d: d.find_elements(By.CLASS_NAME, "inventory_item_name")[0].text
        == "Sauce Labs Onesie"
    )
    # Chờ toàn bộ giá hiển thị xong trên giao diện trước khi kiểm chứng/chụp ảnh
    WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located(
            (By.CLASS_NAME, "inventory_item_price")
        )
    )
    price_texts = [
        el.text for el in driver.find_elements(By.CLASS_NAME, "inventory_item_price")
    ]
    prices = [float(t.replace("$", "")) for t in price_texts]
    assert prices == sorted(prices), f"Giá chưa tăng dần: {prices}"
    # Sản phẩm rẻ nhất của SauceDemo là $7.99, đắt nhất là $49.99
    assert prices[0] == 7.99 and prices[-1] == 49.99

    take_screenshot(driver, "tc05-sort-price-low-to-high.png")


# ---------------------------------------------------------------- TC06
def test_tc06_checkout_complete_and_logout(driver):
    """TC06: Checkout hoàn chỉnh -> 'Thank you for your order!', sau đó đăng xuất."""
    login_success(driver)
    driver.find_element(By.ID, f"add-to-cart-{BACKPACK_ID}").click()
    driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
    WebDriverWait(driver, 10).until(EC.url_contains("cart"))

    driver.find_element(By.ID, "checkout").click()
    wait = WebDriverWait(driver, 15)
    wait.until(EC.url_contains("checkout-step-one"))
    driver.find_element(By.ID, "first-name").send_keys("Hiep")
    driver.find_element(By.ID, "last-name").send_keys("Luu")
    driver.find_element(By.ID, "postal-code").send_keys("100000")
    driver.find_element(By.ID, "continue").click()

    wait.until(EC.url_contains("checkout-step-two"))
    # Kiểm tra tổng tiền gồm giá sản phẩm $29.99 + thuế
    total = driver.find_element(By.CLASS_NAME, "summary_total_label").text
    assert "Total: $32.39" in total, f"Tổng tiền không đúng: {total}"
    take_screenshot(driver, "tc06-checkout-overview.png")

    driver.find_element(By.ID, "finish").click()
    header = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, "complete-header"))
    )
    assert header.text == "Thank you for your order!"
    take_screenshot(driver, "tc06-checkout-complete.png")

    # Đăng xuất: mở menu burger -> Logout -> quay về trang đăng nhập
    driver.find_element(By.ID, "react-burger-menu-btn").click()
    logout = wait.until(
        EC.element_to_be_clickable((By.ID, "logout_sidebar_link"))
    )
    logout.click()
    wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    assert driver.current_url.rstrip("/") == BASE_URL.rstrip("/")
    assert driver.find_element(By.ID, "user-name").is_displayed()

    take_screenshot(driver, "tc06-logout.png")
