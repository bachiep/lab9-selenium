# Lab 9 — Kiểm thử tự động với Selenium WebDriver

Mục tiêu của bài Lab 9 là tìm hiểu công cụ kiểm thử Selenium và dùng nó để viết các test case kiểm thử tự động cho một website. Đề bài yêu cầu tối thiểu 05 test case, trong bài này em xây dựng 06 test case cho website SauceDemo (Swag Labs) bằng ngôn ngữ Python, thư viện Selenium WebDriver và test runner pytest.

Các test case được chọn xoay quanh những chức năng quen thuộc nhất của một website bán hàng: đăng nhập đúng, đăng nhập sai, thêm sản phẩm vào giỏ hàng, xoá sản phẩm khỏi giỏ hàng, sắp xếp sản phẩm theo giá và thanh toán (checkout) kèm đăng xuất. Đây cũng là những luồng mà người dùng thật thao tác hằng ngày, nên nếu một trong số chúng bị lỗi thì ảnh hưởng trực tiếp đến việc sử dụng website. Toàn bộ 06 test case đều chạy đạt (passed) trong lần chạy được ghi lại ở mục 4.

## 1. Giới thiệu Selenium

### 1.1. Selenium là gì

Selenium là một bộ công cụ mã nguồn mở dùng cho kiểm thử tự động ứng dụng web, ra đời từ năm 2004 và đến nay vẫn là một trong những công cụ phổ biến nhất trong lĩnh vực này. Ý tưởng của Selenium khá đơn giản: thay vì kiểm thử viên ngồi mở trình duyệt, gõ tài khoản, bấm từng nút rồi nhìn kết quả bằng mắt, thì những thao tác đó được viết thành mã nguồn. Khi chạy test, chương trình sẽ tự mở trình duyệt, tự điền dữ liệu, tự bấm nút và tự so sánh kết quả thực tế với kết quả mong đợi. Cách làm này có hai lợi ích rõ rệt. Thứ nhất là tốc độ, một bộ test gồm nhiều trường hợp có thể chạy xong trong vài chục giây, trong khi kiểm thử thủ công tương đương phải mất nhiều phút và rất dễ bỏ sót. Thứ hai là tính lặp lại, bộ test có thể chạy lại bất cứ lúc nào, ví dụ sau mỗi lần sửa code, để kiểm tra xem chức năng cũ có bị ảnh hưởng hay không — đây chính là kiểm thử hồi quy (regression testing).

Bên cạnh lợi ích, kiểm thử tự động bằng Selenium cũng có những hạn chế cần biết. Selenium chỉ làm việc với giao diện web trên trình duyệt, không kiểm thử được ứng dụng desktop hay các lớp bên dưới như API và cơ sở dữ liệu. Test giao diện cũng thường chạy chậm hơn test ở tầng logic và dễ bị ảnh hưởng khi giao diện thay đổi, chẳng hạn lập trình viên đổi id hoặc class của một nút bấm là test có thể sai theo dù chức năng vẫn đúng. Vì vậy trong thực tế, Selenium thường được dùng cho các luồng nghiệp vụ quan trọng và ổn định, thay vì cố kiểm thử mọi chi tiết nhỏ trên giao diện.

### 1.2. Kiến trúc WebDriver

Thành phần được dùng trong bài là Selenium WebDriver. WebDriver hoạt động theo mô hình client – server dựa trên chuẩn W3C WebDriver. Đoạn mã test (viết bằng Python) đóng vai trò client, nó gửi các lệnh như "mở trang này", "tìm ô nhập có id là user-name", "bấm vào nút đăng nhập" dưới dạng HTTP request đến một chương trình trung gian gọi là driver. Với trình duyệt Chrome, driver đó là ChromeDriver. ChromeDriver nhận lệnh, điều khiển trình duyệt Chrome thật thực hiện thao tác, rồi trả kết quả về cho mã test. Nhờ kiến trúc này, cùng một đoạn mã test có thể chạy trên nhiều trình duyệt khác nhau, chỉ cần thay driver tương ứng.

```
Test script (Python + pytest)
        │  HTTP (W3C WebDriver protocol)
        ▼
ChromeDriver  ──►  Google Chrome
```

Từ phiên bản Selenium 4, việc cài đặt driver cũng thuận tiện hơn trước nhờ Selenium Manager: khi chạy test, Selenium tự nhận biết phiên bản Chrome đang có trên máy và tự chuẩn bị ChromeDriver tương ứng, người viết test không phải tải driver thủ công như trước đây. Trong bài này Chrome và ChromeDriver đều ở phiên bản 156.0.8078.47.

### 1.3. Các khái niệm chính đã sử dụng

Khái niệm đầu tiên và quan trọng nhất là **locator**, tức cách định vị một phần tử trên trang web. Selenium hỗ trợ nhiều kiểu locator như `By.ID`, `By.NAME`, `By.CLASS_NAME`, `By.CSS_SELECTOR` hay `By.XPATH`. Kinh nghiệm khi viết bài này là nên ưu tiên locator nào ổn định nhất: id thường là lựa chọn tốt nhất vì mỗi phần tử chỉ có một id duy nhất và ít thay đổi. Trên trang SauceDemo, đa số phần tử quan trọng đều có id rõ ràng như `user-name`, `password`, `login-button` hay các nút thêm vào giỏ dạng `add-to-cart-sauce-labs-backpack`, nên việc định vị khá thuận lợi. Với thông báo lỗi không có id, em dùng CSS selector theo thuộc tính `[data-test="error"]`, đây cũng là một thuộc tính sinh ra để phục vụ kiểm thử nên độ ổn định cao.

Khái niệm thứ hai là **wait** (chờ). Trang web cần thời gian để tải và để xử lý sau mỗi thao tác, nếu mã test tìm phần tử ngay khi trang chưa sẵn sàng thì sẽ gặp lỗi không tìm thấy phần tử dù trang hoàn toàn bình thường. Selenium có hai cách chờ chính là implicit wait và explicit wait. Trong bài, em chủ yếu dùng explicit wait thông qua `WebDriverWait` kết hợp với các điều kiện trong `expected_conditions`, ví dụ chờ cho đến khi URL chứa chữ "inventory", chờ ô nhập liệu hiện ra (`visibility_of_element_located`) hoặc chờ nút bấm có thể bấm được (`element_to_be_clickable`). Cách chờ theo điều kiện này tốt hơn việc dùng `time.sleep()` cố định, vì chương trình chỉ chờ đúng đến khi điều kiện thỏa mãn: trang nhanh thì test chạy nhanh, trang chậm thì test tự chờ thêm, kết quả ổn định hơn hẳn.

Khái niệm thứ ba là **assertion** (khẳng định). Một test case chỉ thật sự có ý nghĩa kiểm thử khi nó kiểm tra được kết quả, chứ không dừng ở việc thao tác xong mà không lỗi. Trong bài, mỗi test đều có các câu lệnh `assert` cụ thể: kiểm tra URL hiện tại, đếm số sản phẩm trên trang, đọc dòng chữ thông báo lỗi, kiểm tra số trên biểu tượng giỏ hàng, so sánh danh sách giá với danh sách đã sắp xếp, hay kiểm tra tổng tiền thanh toán. Nếu một assert sai, pytest sẽ đánh dấu test đó là failed và chỉ rõ giá trị thực tế khác giá trị mong đợi ở đâu.

Ngoài ra, bài còn dùng **fixture** của pytest để tránh lặp code. Việc khởi tạo trình duyệt, mở trang đăng nhập và đăng nhập thành công là các bước dùng chung cho nhiều test, nên được tách thành các hàm dùng chung trong `conftest.py` và `tests/test_saucedemo.py`. Mỗi test case chạy độc lập với một phiên trình duyệt riêng, đăng nhập lại từ đầu, nên kết quả của test này không ảnh hưởng đến test khác và khi một test bị lỗi thì dễ xác định lỗi nằm ở đâu.

## 2. Môi trường thực hiện và website được kiểm thử

Bài được thực hiện với các công cụ sau:

| Hạng mục | Phiên bản / thông tin |
|---|---|
| Ngôn ngữ | Python 3.12.3 |
| Thư viện kiểm thử | Selenium 4.51.0 |
| Test runner | pytest 9.1.1 |
| Plugin báo cáo | pytest-html 4.2.0 |
| Trình duyệt | Google Chrome 156.0.8078.47 (chế độ headless) |
| Driver | ChromeDriver 156.0.8078.47 |
| Hệ điều hành | Ubuntu 24.04 LTS |
| Ngày chạy | 23/10/2026 |
| Website kiểm thử | https://www.saucedemo.com/ |

Website được chọn là SauceDemo, tên hiển thị trên giao diện là Swag Labs. Đây là website bán hàng mẫu do Sauce Labs xây dựng để phục vụ việc học và thực hành kiểm thử tự động. Website có đầy đủ các chức năng cơ bản của một trang thương mại điện tử: đăng nhập, xem danh sách sản phẩm, sắp xếp sản phẩm, giỏ hàng, thanh toán và đăng xuất. Danh sách sản phẩm gồm 06 mặt hàng với giá từ 7.99 đến 49.99 đô la, đủ đa dạng để kiểm thử chức năng sắp xếp theo giá.

Một điểm thuận lợi của SauceDemo là các tài khoản dùng để đăng nhập được công bố ngay trên trang đăng nhập của website, bất kỳ ai cũng có thể dùng để thực hành. Trong bài em dùng hai tài khoản: `standard_user` với mật khẩu `secret_sauce` cho các luồng thành công, và `locked_out_user` (cùng mật khẩu) là tài khoản đã bị khoá, dùng cho trường hợp đăng nhập thất bại. Vì đây là tài khoản mẫu công khai nên có thể ghi trực tiếp trong báo cáo mà không lo lộ thông tin cá nhân.

## 3. Các test case đã xây dựng

Bảng dưới đây tóm tắt 06 test case. Phần trình bày chi tiết từng test case nằm ngay sau bảng.

| Mã | Tên test case | Kết quả mong đợi | Kết quả |
|---|---|---|---|
| TC01 | Đăng nhập thành công | Vào trang danh sách sản phẩm, có đủ 6 sản phẩm | Passed |
| TC02 | Đăng nhập thất bại | Hiện thông báo lỗi, không vào được trang sản phẩm | Passed |
| TC03 | Thêm sản phẩm vào giỏ hàng | Biểu tượng giỏ hàng hiện số 1, giỏ có đúng sản phẩm đã thêm | Passed |
| TC04 | Xoá sản phẩm khỏi giỏ hàng | Giỏ trống, biểu tượng giỏ hàng biến mất | Passed |
| TC05 | Sắp xếp theo giá tăng dần | Giá hiển thị tăng dần từ 7.99 đến 49.99 | Passed |
| TC06 | Checkout và đăng xuất | Đặt hàng thành công với tổng tiền 32.39, đăng xuất về trang đăng nhập | Passed |

### 3.1. TC01 — Đăng nhập thành công

Test case này kiểm tra chức năng đăng nhập trong trường hợp người dùng nhập đúng tài khoản. Chương trình mở trang chủ SauceDemo, chờ ô nhập tên đăng nhập xuất hiện, nhập `standard_user` và mật khẩu `secret_sauce`, sau đó bấm nút Login. Sau khi đăng nhập, chương trình chờ URL chuyển sang trang `inventory` rồi mới kiểm tra nội dung, vì ngay sau khi bấm nút, trang cần một khoảng thời gian ngắn để chuyển hướng.

Có ba điều kiện được kiểm tra: URL hiện tại phải chứa "inventory", tiêu đề trang phải là "Products", và số lượng sản phẩm hiển thị phải đúng bằng 6. Việc kiểm tra đồng thời cả ba điều kiện giúp chắc chắn rằng đăng nhập không chỉ chuyển trang mà còn tải đúng nội dung của trang danh sách sản phẩm. Kết quả thực tế đúng như mong đợi, test passed.

![TC01 - Đăng nhập thành công](screenshots/tc01-login-success.png)

*Hình 1: Trang danh sách sản phẩm sau khi đăng nhập thành công.*

### 3.2. TC02 — Đăng nhập thất bại

Một chức năng đăng nhập tốt không chỉ cần xử lý đúng trường hợp nhập đúng, mà còn phải xử lý đúng khi nhập sai. Vì vậy TC02 kiểm tra hai trường hợp lỗi trong cùng một test. Trường hợp thứ nhất là nhập đúng tên tài khoản nhưng sai mật khẩu (`wrong_password`). Trường hợp thứ hai là đăng nhập bằng tài khoản `locked_out_user`, tức tài khoản đã bị khoá dù mật khẩu nhập vào là đúng.

Ở cả hai trường hợp, chương trình đều chờ khung thông báo lỗi xuất hiện rồi đọc nội dung của nó. Với mật khẩu sai, thông báo phải chứa dòng "Username and password do not match". Với tài khoản bị khoá, thông báo phải nhắc đến việc tài khoản đã bị "locked out". Ngoài ra chương trình còn kiểm tra URL không chứa "inventory", tức người dùng không bị cho qua trang sản phẩm khi đăng nhập thất bại. Cả hai trường hợp đều cho kết quả đúng, test passed. Test case này cho thấy giá trị của việc kiểm thử cả trường hợp âm (negative case), vì đây là những tình huống người dùng gặp thường xuyên nhưng khi kiểm thử thủ công lại hay bị bỏ qua.

### 3.3. TC03 — Thêm sản phẩm vào giỏ hàng

Sau khi đăng nhập thành công, chương trình bấm nút Add to cart của sản phẩm Sauce Labs Backpack — chiếc ba lô có giá 29.99 đô la, cũng là sản phẩm được dùng xuyên suốt các test về giỏ hàng và thanh toán để dễ theo dõi số liệu. Ngay sau thao tác thêm, chương trình kiểm tra biểu tượng giỏ hàng ở góc phải phía trên trang: khi giỏ có hàng, trên biểu tượng này xuất hiện một con số nhỏ (badge) cho biết số lượng sản phẩm, và giá trị mong đợi ở đây là "1".

Tiếp theo, chương trình bấm vào biểu tượng giỏ hàng để mở trang giỏ hàng, kiểm tra trong giỏ có đúng 1 sản phẩm và tên sản phẩm hiển thị đúng là "Sauce Labs Backpack". Cách kiểm tra hai lớp như vậy — vừa nhìn biểu tượng ở ngoài trang danh sách, vừa mở giỏ ra xem bên trong — giúp phát hiện được cả lỗi kiểu "badge hiện số nhưng giỏ lại trống". Kết quả thực tế khớp với mong đợi, test passed.

![TC03 - Thêm vào giỏ hàng](screenshots/tc03-add-to-cart.png)

*Hình 2: Giỏ hàng sau khi thêm Sauce Labs Backpack.*

### 3.4. TC04 — Xoá sản phẩm khỏi giỏ hàng

TC04 tiếp nối TC03 nhưng đi theo hướng ngược lại: sau khi thêm sản phẩm và mở giỏ hàng, chương trình bấm nút Remove của sản phẩm đó rồi kiểm tra giỏ hàng phải trở về trạng thái trống. Điều kiện kiểm tra gồm hai ý: số phần tử sản phẩm trong giỏ (class `cart_item`) phải bằng 0, và badge trên biểu tượng giỏ hàng phải biến mất hoàn toàn hoặc không còn hiển thị.

Test case này có một chi tiết đáng chú ý về cách chờ. Sau khi bấm Remove, sản phẩm không biến mất ngay lập tức mà trang cần xử lý trong tích tắc, nên chương trình dùng `WebDriverWait` với một điều kiện tự viết (hàm lambda) để chờ cho đến khi số sản phẩm trong giỏ thực sự bằng 0 rồi mới khẳng định kết quả. Nếu kiểm tra ngay sau khi bấm nút, test rất dễ bị failed oan dù chức năng xoá vẫn đúng. Test passed trong lần chạy ghi nhận.

### 3.5. TC05 — Sắp xếp sản phẩm theo giá tăng dần

Trên trang danh sách sản phẩm có một ô chọn kiểu sắp xếp ở góc phải, gồm các lựa chọn như sắp xếp theo tên (A đến Z, Z đến A) và theo giá (thấp đến cao, cao đến thấp). TC05 chọn kiểu "Price (low to high)" thông qua lớp `Select` của Selenium với giá trị `lohi`, rồi kiểm tra thứ tự giá của toàn bộ sản phẩm.

Cách kiểm tra ở test này khác với việc chỉ nhìn sản phẩm đầu tiên. Chương trình đọc toàn bộ 6 mức giá đang hiển thị, bỏ ký hiệu "$" ở đầu và chuyển từng giá trị từ dạng chữ sang dạng số, thu được một danh sách số. Sau đó danh sách này được so sánh với chính nó sau khi sắp xếp tăng dần bằng hàm `sorted()`: hai danh sách bằng nhau nghĩa là giá trên giao diện đang tăng dần thật. Ngoài ra chương trình còn kiểm tra thêm giá đầu tiên phải là 7.99 và giá cuối cùng phải là 49.99, đúng với sản phẩm rẻ nhất (Sauce Labs Onesie) và đắt nhất trên trang. Việc chuyển giá sang số trước khi so sánh là cần thiết, vì nếu so sánh theo dạng chữ, kết quả có thể sai — ví dụ "15.99" đứng trước "7.99" theo thứ tự ký tự nhưng lại lớn hơn theo giá trị số. Kết quả thực tế đúng thứ tự tăng dần, test passed.

### 3.6. TC06 — Checkout hoàn chỉnh và đăng xuất

TC06 là test case dài nhất vì nó đi trọn một luồng mua hàng như người dùng thật. Chương trình đăng nhập, thêm Sauce Labs Backpack vào giỏ, mở giỏ hàng và bấm Checkout. Ở bước điền thông tin, chương trình nhập họ tên và mã bưu chính vào ba ô `first-name`, `last-name`, `postal-code` rồi bấm Continue để sang màn hình tổng quan đơn hàng.

Tại màn hình tổng quan, chương trình kiểm tra tổng tiền phải thanh toán. Giá của chiếc ba lô là 29.99 đô la, cộng thêm thuế 2.40 đô la, tổng cộng là 32.39 đô la, và dòng tổng tiền trên trang phải chứa đúng dòng chữ "Total: $32.39". Đây là bước kiểm tra quan trọng vì nó xác nhận website tính tiền đúng, không chỉ đơn thuần là chuyển trang thành công. Kiểm tra xong, chương trình bấm Finish và chờ dòng thông báo "Thank you for your order!" xuất hiện, xác nhận đơn hàng đã hoàn tất.

Phần cuối của TC06 là đăng xuất: chương trình mở menu ở góc trái (nút burger), chờ nút Logout bấm được rồi bấm vào, sau đó kiểm tra URL đã quay về đúng địa chỉ trang đăng nhập và ô nhập tên đăng nhập lại hiển thị. Test passed, khép lại trọn vẹn vòng đời một phiên mua hàng từ lúc đăng nhập đến lúc đăng xuất.

![TC06 - Checkout hoàn tất](screenshots/tc06-checkout-complete.png)

*Hình 3: Màn hình thông báo đặt hàng thành công.*

## 4. Kết quả chạy test

Chạy toàn bộ bộ test bằng lệnh pytest cho kết quả như sau:

```
tests/test_saucedemo.py::test_tc01_login_success PASSED                  [ 16%]
tests/test_saucedemo.py::test_tc02_login_failure PASSED                  [ 33%]
tests/test_saucedemo.py::test_tc03_add_to_cart PASSED                    [ 50%]
tests/test_saucedemo.py::test_tc04_remove_from_cart PASSED               [ 66%]
tests/test_saucedemo.py::test_tc05_sort_by_price_low_to_high PASSED      [ 83%]
tests/test_saucedemo.py::test_tc06_checkout_complete_and_logout PASSED   [100%]

============================== 6 passed in 44.87s ==============================
```

Cả 06 test case đều passed, không có test nào failed hay bị lỗi trong lần chạy ngày 23/10/2026, tổng thời gian chạy là 44.87 giây. Thời gian này bao gồm cả thời gian khởi động trình duyệt cho từng test, thời gian tải trang qua mạng và các khoảng chờ điều kiện, nên dài hơn nhiều so với thời gian xử lý thực tế của website — đây là đặc điểm chung của kiểm thử giao diện. Chi tiết từng dòng log được lưu trong file `reports/test-results.txt`, ngoài ra khi chạy có thể xuất thêm báo cáo dạng HTML bằng pytest-html để xem kết quả trực quan hơn.

## 5. Một số khó khăn khi thực hiện

Khó khăn đầu tiên là vấn đề chờ đợi đã nêu ở mục 1.3. Ở những lần viết thử ban đầu, nếu tìm phần tử hoặc đọc dữ liệu ngay khi trang chưa tải xong, test sẽ báo lỗi không tìm thấy phần tử hoặc đọc phải dữ liệu cũ. Cách khắc phục là thay các khoảng chờ cố định bằng explicit wait theo điều kiện cụ thể cho từng bước, ví dụ chờ URL thay đổi sau khi đăng nhập, chờ thông báo lỗi hiện ra, chờ nút Logout bấm được. Sau khi áp dụng, bộ test chạy ổn định hơn rõ rệt.

Khó khăn thứ hai nằm ở TC05. Ngay sau khi chọn kiểu sắp xếp, giao diện cần một lúc để sắp xếp lại danh sách, nếu đọc giá ngay lúc đó có thể đọc phải thứ tự cũ. Chương trình xử lý bằng cách chờ cho đến khi sản phẩm đầu tiên trong danh sách trở thành Sauce Labs Onesie — sản phẩm rẻ nhất — và chờ toàn bộ các giá đều hiển thị xong, rồi mới đọc và so sánh.

Khó khăn thứ ba liên quan đến môi trường chạy. Bài được chạy trên máy ảo Linux không có màn hình, nên Chrome phải chạy ở chế độ headless, tức trình duyệt vẫn hoạt động đầy đủ nhưng không hiện cửa sổ. Máy ảo này cũng truy cập Internet thông qua một proxy có yêu cầu xác thực và dùng chứng chỉ riêng, trong khi Chrome không hỗ trợ khai báo tài khoản proxy trực tiếp trong tham số `--proxy-server`, dẫn đến lỗi kết nối khi mới bắt đầu làm bài. Để xử lý, trong mã nguồn có thêm file `proxy_relay.py` đóng vai trò một relay nhỏ chạy tại máy local, nhận kết nối từ Chrome rồi chuyển tiếp lên proxy kèm thông tin xác thực. Phần này chỉ là xử lý riêng cho môi trường máy ảo dùng để làm bài; trên máy cá nhân thông thường không có proxy dạng này, mã nguồn tự nhận biết và bỏ qua, người chạy không cần cấu hình gì thêm.

## 6. Hướng dẫn cài đặt và chạy lại

Máy tính cần có sẵn Python từ bản 3.10 trở lên và trình duyệt Google Chrome. Các bước thực hiện như sau:

```bash
# 1. Tải mã nguồn về
git clone https://github.com/bachiep/lab9-selenium.git
cd lab9-selenium

# 2. Tạo môi trường ảo và cài các thư viện cần thiết
python3 -m venv venv
source venv/bin/activate        # Trên Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Chạy toàn bộ test case
python -m pytest tests/ -v --html=reports/report.html --self-contained-html

# Chạy riêng một test case, ví dụ TC03:
python -m pytest tests/test_saucedemo.py::test_tc03_add_to_cart -v
```

## 7. Cấu trúc thư mục

```
lab9-selenium/
├── README.md                  # Báo cáo Lab 9 (file này)
├── requirements.txt           # Các thư viện cần cài: selenium, pytest, pytest-html
├── pytest.ini                 # Cấu hình pytest
├── conftest.py                # Fixture khởi tạo và đóng WebDriver cho từng test
├── proxy_relay.py             # Relay proxy phục vụ môi trường máy ảo khi làm bài
├── tests/
│   └── test_saucedemo.py      # 06 test case TC01–TC06
├── screenshots/               # Các hình ảnh kết quả của các test case
└── reports/
    └── test-results.txt       # Log kết quả lần chạy được ghi trong báo cáo
```

## 8. Kết luận

Qua bài Lab 9, em đã nắm được cách dùng Selenium WebDriver ở mức cơ bản nhưng đầy đủ một vòng kiểm thử: định vị phần tử bằng các loại locator, thao tác nhập liệu, bấm nút và chọn trong danh sách thả xuống, chờ đợi theo điều kiện bằng explicit wait, và khẳng định kết quả bằng assertion. Bộ test gồm 06 test case, vượt yêu cầu tối thiểu 05 test case của đề bài, bao phủ các chức năng chính của một website bán hàng từ đăng nhập, quản lý giỏ hàng, sắp xếp sản phẩm cho đến thanh toán và đăng xuất. Cả 06 test đều passed trong 44.87 giây.

Điểm em thấy rõ nhất sau bài này là viết test tự động khác nhiều so với thao tác tay: chương trình không có khả năng tự quan sát và chờ đợi như người, nên người viết phải tính trước các thời điểm trang chưa sẵn sàng, các trường hợp lỗi và cách kiểm tra kết quả sao cho chặt chẽ. Những test chỉ thao tác mà không kiểm tra kỹ kết quả thì chạy passed cũng không nói lên được điều gì.

Bộ test hiện tại vẫn còn một số hạn chế: mới chạy trên một trình duyệt duy nhất là Chrome, dữ liệu kiểm thử còn cố định trong mã nguồn, và chưa tách theo mô hình Page Object Model nên khi số lượng test tăng lên, việc bảo trì các locator dùng chung sẽ tốn công hơn. Nếu tiếp tục phát triển, em sẽ tổ chức lại mã nguồn theo Page Object Model, cho phép chạy test song song bằng pytest-xdist để rút ngắn thời gian, và cấu hình GitHub Actions để bộ test tự chạy mỗi khi có thay đổi được đẩy lên repo.
