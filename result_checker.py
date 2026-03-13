from typing import Tuple, Optional
from config import *



class ResultChecker:
    def __init__(self, username: str):
        self.username = username

    def check_preset_credentials(self, password: str) -> Tuple[bool, Optional[str]]:
        if self.username in preset_credentials and password == preset_credentials[self.username]:
            return True, self.username
        return False, None

    def is_login_successful(self, content_length: int) -> bool:
        return content_length < 2400