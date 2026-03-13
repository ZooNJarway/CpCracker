from typing import List


class PasswordManager:
    def __init__(self, password_file: str = 'top100.txt'):
        """初始化密码管理器"""
        self.password_file = password_file
        self.passwords = self._load_passwords()

    def _load_passwords(self) -> List[str]:
        """
        从文件加载密码列表
        返回:
            包含所有密码的字符串列表
        """
        with open(self.password_file, 'r') as f:
            return [line.strip() for line in f.readlines()]



