"""Relay proxy nội bộ: thêm Proxy-Authorization khi chuyển tiếp tới egress proxy.

Lý do tồn tại file này (workaround thật của môi trường chạy test):
- VM chạy test ra Internet bắt buộc qua một egress proxy có xác thực
  (biến môi trường HTTPS_PROXY dạng http://user:pass@host:3128).
- Chrome KHÔNG hỗ trợ nhúng user:pass vào --proxy-server: truyền thẳng
  chuỗi proxy của môi trường vào Chrome sẽ lỗi ERR_TUNNEL_CONNECTION_FAILED,
  còn bỏ proxy thì lỗi ERR_SSL_PROTOCOL_ERROR vì egress chặn kết nối trực tiếp.
- Giải pháp (tương tự relay.py ở Lab 8 - JMeter): chạy một relay nhỏ trên
  127.0.0.1 không cần xác thực để Chrome kết nối tới, relay tự gắn thêm
  header Proxy-Authorization khi mở tunnel CONNECT tới proxy thật.

Trên máy cá nhân bình thường (proxy không có xác thực hoặc không có proxy),
module này không được dùng tới.
"""
import base64
import socket
import threading
from urllib.parse import unquote, urlparse

_BUFFER = 65536


class _BufferedConn:
    """Đọc header HTTP theo từng dòng nhưng không nuốt mất phần body/tunnel."""

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buf = b""

    def read_until(self, marker: bytes) -> bytes:
        while marker not in self.buf:
            chunk = self.sock.recv(_BUFFER)
            if not chunk:
                break
            self.buf += chunk
        idx = self.buf.find(marker)
        if idx == -1:
            data, self.buf = self.buf, b""
            return data
        end = idx + len(marker)
        data, self.buf = self.buf[:end], self.buf[end:]
        return data

    def read_some(self) -> bytes:
        if self.buf:
            data, self.buf = self.buf, b""
            return data
        return self.sock.recv(_BUFFER)

    def sendall(self, data: bytes):
        self.sock.sendall(data)


def _pipe(src: _BufferedConn, dst: _BufferedConn):
    try:
        while True:
            data = src.read_some()
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.sock.shutdown(socket.SHUT_WR)
        except OSError:
            pass


class ProxyRelay:
    """HTTP proxy không xác thực trên localhost, forward kèm xác thực lên upstream."""

    def __init__(self, upstream_url: str):
        u = urlparse(upstream_url)
        self.upstream_host = u.hostname
        self.upstream_port = u.port or 3128
        creds = f"{unquote(u.username or '')}:{unquote(u.password or '')}"
        self.auth_header = (
            "Proxy-Authorization: Basic "
            + base64.b64encode(creds.encode()).decode()
            + "\r\n"
        )
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", 0))
        self._server.listen(50)
        self.port = self._server.getsockname()[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        try:
            self._server.close()
        except OSError:
            pass

    def _serve(self):
        while True:
            try:
                client, _ = self._server.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(client,), daemon=True).start()

    def _handle(self, client_sock: socket.socket):
        client = _BufferedConn(client_sock)
        upstream = None
        try:
            head = client.read_until(b"\r\n\r\n")
            if not head:
                return
            first_line = head.split(b"\r\n", 1)[0].decode("latin-1")
            parts = first_line.split(" ")
            method = parts[0].upper()

            upstream_sock = socket.create_connection(
                (self.upstream_host, self.upstream_port), timeout=30
            )
            upstream = _BufferedConn(upstream_sock)

            if method == "CONNECT":
                target = parts[1]
                req = (
                    f"CONNECT {target} HTTP/1.1\r\n"
                    f"Host: {target}\r\n"
                    f"{self.auth_header}"
                    "Proxy-Connection: keep-alive\r\n\r\n"
                )
                upstream.sendall(req.encode())
                resp_head = upstream.read_until(b"\r\n\r\n")
                status = resp_head.split(b"\r\n", 1)[0]
                if b" 200" not in status:
                    client.sendall(resp_head)
                    return
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            else:
                # HTTP thường qua proxy: chèn thêm header xác thực ngay
                # trước dòng trống kết thúc phần header rồi forward đi.
                new_head = head[:-2] + self.auth_header.encode() + b"\r\n"
                upstream.sendall(new_head)

            t1 = threading.Thread(target=_pipe, args=(client, upstream), daemon=True)
            t2 = threading.Thread(target=_pipe, args=(upstream, client), daemon=True)
            t1.start(); t2.start()
            t1.join(); t2.join()
        except OSError:
            pass
        finally:
            for conn in (client, upstream):
                if conn is not None:
                    try:
                        conn.sock.close()
                    except OSError:
                        pass
