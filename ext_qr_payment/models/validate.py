import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend


def check_url_with_public_key(url_check, key_public):
    try:
        response = requests.get(url_check)
        cert_data = response.content  # Lấy dữ liệu chứng chỉ từ phản hồi
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        # Lấy khóa công khai từ chứng chỉ
        cert_public_key = cert.public_key()

        # So sánh khóa công khai với khóa công khai được cung cấp
        if cert_public_key == key_public:
            print("Chứng chỉ của trang web phù hợp với khóa công khai.")
        else:
            print("Chứng chỉ của trang web không phù hợp với khóa công khai.")
    except Exception as e:
        print("Có lỗi xảy ra khi kiểm tra URL:", e)


# Sử dụng hàm với một URL cụ thể và khóa công khai cụ thể
url = "https://example.com"
# public_key là một đối tượng khóa công khai, bạn cần tạo từ dữ liệu hoặc từ file
key_public = ...

check_url_with_public_key(url, key_public)
