import os
from datetime import datetime

import cv2
import matplotlib.pyplot as plt
# import numpy as np
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
# from PIL import Image
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


class GrayscaleTransform:
    def __call__(self, img):
        return img.convert('L')  # 转换为灰度图像


class AdaptiveMedianFilter:
    def __call__(self, img):
        img_np = np.array(img)
        filtered = cv2.medianBlur(img_np, 5)  # 自适应中值滤波
        return Image.fromarray(filtered)


class ThresholdTransform:
    def __init__(self, threshold=127):
        self.threshold = threshold

    def __call__(self, img):
        img_np = np.array(img)
        _, threshed = cv2.threshold(img_np, self.threshold, 255, cv2.THRESH_BINARY)  # 阈值处理
        return Image.fromarray(threshed)


class DilateTransform:
    def __init__(self, kernel_size=3):
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def __call__(self, img):
        img_np = np.array(img)
        dilated = cv2.dilate(img_np, self.kernel, iterations=1)  # 膨胀图像
        return Image.fromarray(dilated)


class ErodeTransform:
    def __init__(self, kernel_size=3):
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def __call__(self, img):
        img_np = np.array(img)
        eroded = cv2.erode(img_np, self.kernel, iterations=1)  # 腐蚀图像
        return Image.fromarray(eroded)


# ========================================
# 配置 & 参数设置
# ========================================

DATA_DIR = './DataForTest'
MODEL_SAVE_PATH = '../captcha_model.pth'
LOG_FILE = './logs/training.log'
BATCH_SIZE = 32
NUM_EPOCHS = 50
LEARNING_RATE = 0.001
IMAGE_SIZE = (84, 32)  # 宽度 x 高度
CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'  # 字符集
NUM_CLASSES = len(CHARACTERS)
CHAR_TO_INDEX = {c: i for i, c in enumerate(CHARACTERS)}
INDEX_TO_CHAR = {i: c for c, i in CHAR_TO_INDEX.items()}


# ========================================
#  自定义 Dataset 类
# ========================================

class CaptchaDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.file_list = [f for f in os.listdir(root_dir) if f.endswith(('.png', '.jpg'))]

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        img_name = self.file_list[idx]
        label_str = os.path.splitext(img_name)[0][:4]  # 只取前 4 个字符作为标签
        img_path = os.path.join(self.root_dir, img_name)
        image = Image.open(img_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        label = torch.tensor([CHAR_TO_INDEX[c] for c in label_str], dtype=torch.long)
        return image, label


# ========================================
# 模型定义（CNN）
# ========================================

class CaptchaModel(nn.Module):
    """
    自定义验证码识别模型。

    该模型继承自PyTorch的nn.Module类，主要包括两个部分：特征提取层(self.features)和分类器(self.classifier)。
    特征提取层使用卷积神经网络（CNN）来提取输入图像的特征，而分类器则用于根据提取到的特征预测验证码中的字符。
    """

    def __init__(self):
        """
        初始化模型。

        初始化包括设置特征提取层和分类器层的架构。特征提取层由两个卷积层组成，每个卷积层后面跟着一个ReLU激活函数和一个最大池化层。
        分类器由两个全连接层组成，将特征提取层的输出映射到验证码字符的预测概率上。
        """
        super(CaptchaModel, self).__init__()
        # 特征提取层
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),  # 第一个卷积层，输入通道数为1，输出通道数为32
            nn.ReLU(),  # ReLU激活函数
            nn.MaxPool2d(2),  # 最大池化层，缩小特征图的尺寸
            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # 第二个卷积层，输入通道数为32，输出通道数为64
            nn.ReLU(),  # ReLU激活函数
            nn.MaxPool2d(2),  # 最大池化层，进一步缩小特征图的尺寸
        )
        # 分类器
        self.classifier = nn.Sequential(
            nn.Linear(64 * 8 * 21, 512),  # 根据特征图大小调整全连接层的输入尺寸
            nn.ReLU(),  # ReLU激活函数
            nn.Linear(512, 4 * NUM_CLASSES)  # 输出层，假设NUM_CLASSES为字符集大小，输出验证码中每个位置的字符概率
        )

    def forward(self, x):
        """
        对输入验证码的处理流程。

        输入：x - 一批输入图像张量。
        输出：x - 验证码字符的预测概率张量。

        该方法首先通过特征提取层处理输入图像，然后将提取到的特征展平，最后通过分类器得到每个验证码字符的预测概率。
        """
        batch_size = x.size(0)  # 获取批次大小
        x = self.features(x)  # 特征提取
        x = x.view(batch_size, -1)  # 将特征图展平为一维向量
        x = self.classifier(x)  # 分类预测
        x = x.view(batch_size, 4, NUM_CLASSES)  # 调整输出尺寸，假设验证码长度为4
        return x


# ========================================
# 数据预处理和加载
# ========================================

transform = transforms.Compose([
    GrayscaleTransform(),  # 灰度化
    AdaptiveMedianFilter(),  # 自适应中值滤波
    ThresholdTransform(120),  # 二值化，阈值设为 120
    DilateTransform(3),  # 膨胀
    ErodeTransform(3),  # 腐蚀
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
])
dataset = CaptchaDataset(DATA_DIR, transform=transform)
dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# ========================================
#  模型、损失函数、优化器
# ========================================

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = CaptchaModel().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)


# ========================================
#  日志记录函数
# ========================================

def log_message(message):
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now()} | {message}\n")


# ========================================
#  准确率计算函数
# ========================================

def calculate_accuracy(outputs, labels):
    _, preds = torch.max(outputs, 2)
    correct = (preds == labels).sum().item()
    total = labels.numel()
    return correct / total


# ========================================
#  可视化损失曲线
# ========================================

def plot_losses(losses):
    plt.figure(figsize=(10, 5))
    plt.plot(losses, label='Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss Curve')
    plt.legend()
    plt.grid(True)
    plt.savefig('loss_curve.png')
    plt.show()


# ========================================
#  开始训练
# ========================================

log_message(" 开始训练...")

losses = []

for epoch in range(NUM_EPOCHS):
    model.train()
    running_loss = 0.0
    running_acc = 0.0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)  # shape: [batch, 4, num_chars]

        loss = 0
        for i in range(4):  # 对每个字符分别计算损失
            loss += criterion(outputs[:, i, :], labels[:, i])

        loss.backward()
        optimizer.step()

        acc = calculate_accuracy(outputs, labels)
        running_loss += loss.item()
        running_acc += acc

    avg_loss = running_loss / len(dataloader)
    avg_acc = running_acc / len(dataloader)
    losses.append(avg_loss)

    log_message(f"Epoch [{epoch + 1}/{NUM_EPOCHS}], Loss: {avg_loss:.4f}, Accuracy: {avg_acc * 100:.2f}%")

# ========================================
#  保存模型
# ========================================

torch.save(model.state_dict(), MODEL_SAVE_PATH)
log_message(f"模型已保存至 {MODEL_SAVE_PATH}")

# ========================================
#  绘制损失曲线
# ========================================

plot_losses(losses)
log_message("训练完成！")
