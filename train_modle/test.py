import torch
import torch.nn as nn
from torchvision import transforms
# from PIL import Image
import os
from torch.utils.data import Dataset, DataLoader
# import matplotlib.pyplot as plt
import cv2
import numpy as np
from PIL import Image

class GrayscaleTransform:
    def __call__(self, img):
        return img.convert('L')  # 转换为灰度图

class AdaptiveMedianFilter:
    def __call__(self, img):
        img_np = np.array(img)
        # 使用 medianBlur 作为替代
        filtered = cv2.medianBlur(img_np, 5)
        return Image.fromarray(filtered)

class ThresholdTransform:
    def __init__(self, threshold=127):
        self.threshold = threshold

    def __call__(self, img):
        img_np = np.array(img)
        _, threshed = cv2.threshold(img_np, self.threshold, 255, cv2.THRESH_BINARY)
        return Image.fromarray(threshed)


class DilateTransform:
    def __init__(self, kernel_size=3):
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def __call__(self, img):
        img_np = np.array(img)
        dilated = cv2.dilate(img_np, self.kernel, iterations=1)
        return Image.fromarray(dilated)


class ErodeTransform:
    def __init__(self, kernel_size=3):
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def __call__(self, img):
        img_np = np.array(img)
        eroded = cv2.erode(img_np, self.kernel, iterations=1)
        return Image.fromarray(eroded)
# ========================================
#  配置参数（与 train.py 保持一致）
# ========================================


DATA_DIR = './DataForTest'  # 你提供的测试集路径
MODEL_SAVE_PATH = '../captcha_model.pth'
IMAGE_SIZE = (84, 32)
CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
NUM_CLASSES = len(CHARACTERS)
CHAR_TO_INDEX = {c: i for i, c in enumerate(CHARACTERS)}
INDEX_TO_CHAR = {i: c for c, i in CHAR_TO_INDEX.items()}

# ========================================
#  自定义测试 Dataset 类
# ========================================

class CaptchaTestDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.file_list = [f for f in os.listdir(root_dir) if f.endswith(('.png', '.jpg'))]

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        img_name = self.file_list[idx]
        label_str = os.path.splitext(img_name)[0]  # 去掉后缀作为标签
        label_str = label_str[:4]  # 固定长度为 4 的验证码
        img_path = os.path.join(self.root_dir, img_name)
        image = Image.open(img_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        label = torch.tensor([CHAR_TO_INDEX[c] for c in label_str], dtype=torch.long)
        return image, label, img_name  # 返回图片名用于展示

# ========================================
# 模型定义（必须与 train.py 中完全一致）
# ========================================

class CaptchaModel(nn.Module):
    def __init__(self):
        super(CaptchaModel, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Linear(64 * 8 * 21, 512),
            nn.ReLU(),
            nn.Linear(512, 4 * NUM_CLASSES)
        )

    def forward(self, x):
        batch_size = x.size(0)
        x = self.features(x)
        x = x.view(batch_size, -1)
        x = self.classifier(x)
        x = x.view(batch_size, 4, NUM_CLASSES)
        return x

# ========================================
# 加载模型 & 开始测试
# ========================================

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# 加载模型
model = CaptchaModel().to(device)
model.load_state_dict(torch.load(MODEL_SAVE_PATH))
model.eval()

# 数据预处理
transform = transforms.Compose([
    GrayscaleTransform(),         # 灰度化
    AdaptiveMedianFilter(),       # 自适应中值滤波
    ThresholdTransform(120),      # 二值化，阈值设为 120
    DilateTransform(3),           # 膨胀
    ErodeTransform(3),            # 腐蚀
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
])

# 创建测试集
test_dataset = CaptchaTestDataset(DATA_DIR, transform=transform)
test_dataloader = DataLoader(test_dataset, batch_size=32, shuffle=False)
# 预测并计算准确率
correct = 0
total = 0

with torch.no_grad():
    for images, labels, names in test_dataloader:
        images = images.to(device)
        labels = labels.to(device)
        outputs = model(images)
        _, preds = torch.max(outputs, 2)
        # 计算准确率
        correct += (preds == labels).sum().item()
        total += labels.numel()
        # 可视化部分预测结果
        for i in range(min(5, images.shape[0])):  # 显示前 5 张图
            true_label = ''.join([INDEX_TO_CHAR[l.item()] for l in labels[i]])
            pred_label = ''.join([INDEX_TO_CHAR[p.item()] for p in preds[i]])
            print(f"Image: {names[i]} | True: {true_label} | Pred: {pred_label}")

# 输出整体准确率
accuracy = correct / total
print(f"\n[+++] Test Accuracy: {accuracy * 100:.2f}%")
