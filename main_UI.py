# -*- coding: utf-8 -*-

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit
)


# import sys
# import os
# import argparse
# from colorama import Fore, Style
# from main import Cracker

class CrackerThread(QThread):
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, target_url, captcha_url, username, password, captcha):
        super().__init__()
        self.target_url = target_url
        self.captcha_url = captcha_url
        self.username = username
        self.password = password
        self.captcha = captcha

    def run(self):
        try:
            from main import Cracker

            # 构建目标 URL
            login_url = self.target_url
            if not login_url.endswith('/login'):
                if login_url.endswith('/'):
                    login_url += 'login'
                else:
                    login_url += '/login'

            # 直接实例化 Cracker 并运行
            cracker = Cracker(
                target_url=login_url,
                captcha_url=self.captcha_url,
                username_field=self.username,
                password_field=self.password,
                captcha_field=self.captcha
            )

            # 重定向打印输出
            import sys
            from io import StringIO
            stdout_redirect = StringIO()
            sys.stdout = stdout_redirect

            cracker.run()

            # 发送日志和结果
            output = stdout_redirect.getvalue()
            self.log_signal.emit(output)
            if "Maybe Success" in output:
                self.result_signal.emit("破解成功！")
            else:
                self.result_signal.emit("破解完成，未发现成功登录信息")

        except Exception as e:
            self.log_signal.emit(f"发生错误: {str(e)}")
            self.result_signal.emit("破解过程中出错")
        finally:
            sys.stdout = sys.__stdout__  # 恢复标准输出

        class Args:
            def __init__(self, target_url, captcha_url, username, password, captcha):
                self.target_url = target_url
                self.captcha_url = captcha_url
                self.user = username
                self.pwd = password
                self.cap = captcha

        args = Args(self.target_url, self.captcha_url, self.username, self.password, self.captcha)
        login_url = args.target_url
        if not login_url.endswith('/login'):
            if login_url.endswith('/'):
                login_url += 'login'
            else:
                login_url += '/login'

        cracker = Cracker(login_url, args.captcha_url, args.user, args.pwd, args.cap)

        # 重定向打印输出
        import sys
        from io import StringIO
        stdout_redirect = StringIO()
        sys.stdout = stdout_redirect

        try:
            cracker.run()
        finally:
            sys.stdout = sys.__stdout__  # 恢复标准输出

            # 发送日志和结果
            output = stdout_redirect.getvalue()
            self.log_signal.emit(output)
            if "Maybe Success" in output:
                self.result_signal.emit("破解成功！")
            else:
                self.result_signal.emit("破解完成，未发现成功登录信息")


class CpCrackerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CpCracker >>> CipherGhost >> (ZooNJarway)")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Banner
        banner_label = QLabel()
        pixmap = QPixmap("./CipherGhost.jpg")  # 加载本地图片

        if not pixmap.isNull():
            # 如果图片存在，按宽度缩放，高度自适应
            scaled_pixmap = pixmap.scaled(500, 300, Qt.AspectRatioMode.IgnoreAspectRatio)
            banner_label.setPixmap(scaled_pixmap)
        else:
            banner_label.setText("CypherGhost Logo Not Found")
            banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(banner_label)

        # 目标URL输入
        url_layout = QHBoxLayout()
        url_label = QLabel("目标登录URL:")
        self.url_input = QLineEdit("")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # 验证码URL输入
        captcha_url_layout = QHBoxLayout()
        captcha_url_label = QLabel("验证码图片URL:")
        self.captcha_url_input = QLineEdit("")
        captcha_url_layout.addWidget(captcha_url_label)
        captcha_url_layout.addWidget(self.captcha_url_input)
        layout.addLayout(captcha_url_layout)

        # 字段配置区域
        fields_layout = QHBoxLayout()

        # 用户名字段
        user_layout = QHBoxLayout()
        user_label = QLabel("用户名字段名称:")
        self.user_input = QLineEdit("")
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.user_input)

        # 密码字段
        pwd_layout = QHBoxLayout()
        pwd_label = QLabel("密码字段名称:")
        self.pwd_input = QLineEdit("")
        pwd_layout.addWidget(pwd_label)
        pwd_layout.addWidget(self.pwd_input)

        # 验证码字段
        cap_layout = QHBoxLayout()
        cap_label = QLabel("验证码字段名称:")
        self.cap_input = QLineEdit("")
        cap_layout.addWidget(cap_label)
        cap_layout.addWidget(self.cap_input)

        fields_layout.addLayout(user_layout)
        fields_layout.addLayout(pwd_layout)
        fields_layout.addLayout(cap_layout)
        layout.addLayout(fields_layout)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("开始破解")
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self.start_cracking)
        self.stop_button.clicked.connect(self.stop_cracking)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # 日志输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(QLabel("日志输出:"))
        layout.addWidget(self.log_output)

        # 结果展示
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        layout.addWidget(QLabel("破解结果:"))
        layout.addWidget(self.result_output)

        central_widget.setLayout(layout)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
            QLabel {
                color: #D4D4D4;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2D2D2D;
                color: #FFFFFF;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357AE8;
            }
            QTextEdit {
                background-color: #2D2D2D;
                color: #D4D4D4;
                border: 1px solid #444;
                padding: 5px;
            }
        """)

    def start_cracking(self):
        """开始破解"""
        target_url = self.url_input.text().strip()
        captcha_url = self.captcha_url_input.text().strip()
        username = self.user_input.text().strip()
        password = self.pwd_input.text().strip()
        captcha = self.cap_input.text().strip()

        if not all([target_url, captcha_url, username, password, captcha]):
            self.log_output.append("错误：所有字段都必须填写！")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_output.clear()
        self.result_output.clear()

        self.cracker_thread = CrackerThread(target_url, captcha_url, username, password, captcha)
        self.cracker_thread.log_signal.connect(self.update_log)
        self.cracker_thread.result_signal.connect(self.update_result)
        self.cracker_thread.finished.connect(self.thread_finished)
        self.cracker_thread.start()

    def stop_cracking(self):
        """停止破解"""
        if hasattr(self, 'cracker_thread') and self.cracker_thread.isRunning():
            self.cracker_thread.terminate()
            self.thread_finished()

    def update_log(self, message):
        """更新日志"""
        self.log_output.append(message)

    def update_result(self, message):
        """更新结果"""
        self.result_output.setText(message)

    def thread_finished(self):
        """线程结束处理"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)


if __name__ == "__main__":
    import os
    import sys
    from PyQt6.QtWidgets import QApplication

    os.environ['RUN_FROM_UI'] = '1'
    app = QApplication(sys.argv)
    window = CpCrackerUI()
    window.show()
    sys.exit(app.exec())
