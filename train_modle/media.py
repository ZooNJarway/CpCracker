import cv2
import numpy as np

# 打印 OpenCV 版本
print(f"OpenCV Version: {cv2.__version__}")

# 测试 adaptiveMedianBlur 方法
test_img = np.zeros((100, 100), dtype=np.uint8)
try:
    result = cv2.adaptiveMedianBlur(test_img, 5)
    print("adaptiveMedianBlur method works!")
except AttributeError as e:
    print(f"Error: {e}")
