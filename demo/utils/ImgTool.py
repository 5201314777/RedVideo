import ctypes

import cv2
import numpy as np


def yv12_to_bgr(self, pBuf, frame_info):
    """
    海康 YV12 → OpenCV BGR
    """
    width = frame_info.nWidth
    height = frame_info.nHeight

    # YV12 size = width * height * 3 / 2
    yv12 = np.frombuffer(
        ctypes.string_at(pBuf, width * height * 3 // 2),
        dtype=np.uint8
    )

    # reshape
    yv12 = yv12.reshape((height * 3 // 2, width))

    # 转 BGR
    bgr = cv2.cvtColor(yv12, cv2.COLOR_YUV2BGR_YV12)
    return bgr