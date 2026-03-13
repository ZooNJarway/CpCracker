from typing import Optional
from colorama import Fore, Style
import cv2
import numpy as np
import torch
from torchvision import transforms


CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789_'  # ← 改为完整字符集
NUM_CLASSES = len(CHARACTERS)
CHAR_TO_INDEX = {c: i for i, c in enumerate(CHARACTERS)}
INDEX_TO_CHAR = {i: c for c, i in CHAR_TO_INDEX.items()}



class CaptchaModel(torch.nn.Module):
    def __init__(self):
        super(CaptchaModel, self).__init__()
        self.features = torch.nn.Sequential(
            torch.nn.Conv2d(1, 32, kernel_size=3, padding=1),  # 输入通道为 3（RGB）
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(32, 64, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(64 * 8 * 21, 512),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 4 * NUM_CLASSES)
        )

    def forward(self, x):
        batch_size = x.size(0)
        x = self.features(x)
        x = x.view(batch_size, -1)
        x = self.classifier(x)
        x = x.view(batch_size, 4, NUM_CLASSES)
        return x


class CaptchaProcessor:
    def __init__(self, model_path='./captcha_model.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = CaptchaModel().to(self.device)
        self.model.load_state_dict(
            torch.load(model_path, map_location=self.device, weights_only=True)
        )
        self.model.eval()

    def recognize_captcha(self, image_path: str) -> Optional[str]:
        """
        使用训练好的模型识别验证码图片
        参数:
            image_path: 验证码图片的文件路径
        返回:
            识别出的验证码文本，如果识别失败返回None
        """
        try:
            img = self._preprocess_image(image_path)
            img_tensor = transforms.ToTensor()(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(img_tensor)
                _, preds = torch.max(outputs, 2)
                preds = preds.cpu().squeeze(0).numpy()

            captcha_text = ''.join([INDEX_TO_CHAR[p] for p in preds])
            return captcha_text
        except Exception as e:
            print(f"[ --- ] Analyze Captcha Failed!!: {e}")
            return None

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        图像预处理函数，保留单通道灰度图
        """
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 灰度化
        filtered = cv2.medianBlur(gray, 5)  # 自适应中值滤波
        _, threshed = cv2.threshold(filtered, 120, 255, cv2.THRESH_BINARY)  # 阈值处理
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(threshed, kernel, iterations=1)  # 膨胀
        eroded = cv2.erode(dilated, kernel, iterations=1)  # 腐蚀
        resized = cv2.resize(eroded, (84, 32))  # 调整尺寸
        return resized  # 返回单通道图像
