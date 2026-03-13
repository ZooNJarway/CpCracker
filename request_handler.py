import os
from typing import Dict, Optional

from colorama import Fore, Style
from requests import Session


class RequestHandler:
    def __init__(self, post_file: str = 'POST.txt') -> None:
        """初始化请求处理器"""
        self.post_file = post_file
        self.headers = self._parse_headers()
        self.session = Session()

    def _parse_headers(self) -> Dict[str, str]:
        """
        解析请求头文件
        返回:
            包含请求头字段的字典
        """
        with open(self.post_file, 'r') as f:
            post_content = f.read()
        header_part, _ = post_content.split('\n\n', 1)
        headers_lines = header_part.split('\n')
        headers = {}
        for line in headers_lines[1:]:  # 跳过起始行
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value

        return headers

    def download_captcha(self, captcha_url: str, captcha_path: str) -> bool:
        """
        下载验证码图片
        参数:
            captcha_url: 验证码图片URL
            captcha_path: 保存验证码图片的本地路径
        返回:
            下载成功返回True，否则返回False
        """
        response = self.session.get(captcha_url, headers=self.headers)
        if response.status_code != 200:
            print(f"[ --- ] Captcha Download Error ! : HTTP {response.status_code}")
            return False
        with open(captcha_path, 'wb') as f:
            f.write(response.content)
        return True

    def send_login_request(self, login_url: str, body_part: str, password: str, captcha_text: str) -> Optional[bytes]:
        """
        发送登录请求
        参数:
            login_url: 登录URL
            body_part: 请求体模板
            password: 要测试的密码
            captcha_text: 识别出的验证码
        返回:
            响应内容，如果请求失败返回None
        """
        new_body = body_part.replace('password=payload', f'password={password}')
        new_body = new_body.replace('captcha=payload', f'captcha={captcha_text}')
        # 更新Content-Length
        self.headers['Content-Length'] = str(len(new_body))
        try:
            login_response = self.session.post(
                login_url,
                headers=self.headers,
                data=new_body
            )
            return login_response.content
        except Exception as e:
            print(f"[ --- ] Send Request Error !: {e}")
            return None

    def cleanup_captcha(self, captcha_path: str):
        """清理验证码图片"""
        if os.path.exists(captcha_path):
            os.remove(captcha_path)
