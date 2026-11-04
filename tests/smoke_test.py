"""合成图端到端自检：不依赖真实样本，验证拼接流程可跑通。

用法:
    python tests/smoke_test.py
"""
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from leaf_stitch import stitch_leaf  # noqa: E402

W, H = 600, 1400          # 完整叶片画布
OVERLAP = 320             # 上下两段重叠行数（约 23%）
OUT_DIR = os.path.join(HERE, "out")


def make_leaf_canvas():
    """白底 + 黄绿色椭圆叶片 + 中脉/侧脉/噪点，制造足够的 ORB 特征。"""
    rng = np.random.default_rng(42)
    canvas = np.full((H, W, 3), 255, dtype=np.uint8)

    # 叶片主体
    cv2.ellipse(canvas, (W // 2, H // 2), (150, 620), 0, 0, 360, (70, 160, 150), -1)

    # 中脉
    cv2.line(canvas, (W // 2, H // 2 - 600), (W // 2, H // 2 + 600), (95, 130, 125), 5)

    # 侧脉
    for i in range(-11, 12):
        y = H // 2 + i * 52
        cv2.line(canvas, (W // 2, y), (W // 2 - 130, y - 45), (100, 140, 130), 2)
        cv2.line(canvas, (W // 2, y), (W // 2 + 130, y - 45), (100, 140, 130), 2)

    # 纹理噪点（只加在叶片内，制造可匹配的角点）
    noise = rng.integers(-22, 23, (H, W, 3), dtype=np.int16)
    leaf_mask = (cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY) < 245)
    noisy = canvas.astype(np.int16) + noise
    canvas[leaf_mask] = np.clip(noisy, 0, 255).astype(np.uint8)[leaf_mask]
    return canvas


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    full = make_leaf_canvas()

    upper = full[: H // 2 + OVERLAP // 2].copy()
    lower = full[H // 2 - OVERLAP // 2 :].copy()

    # 制造曝光差异，检验颜色校正环节
    upper = np.clip(upper.astype(np.int16) + 12, 0, 255).astype(np.uint8)
    lower = np.clip(lower.astype(np.int16) - 12, 0, 255).astype(np.uint8)

    up_path = os.path.join(OUT_DIR, "upper.jpg")
    low_path = os.path.join(OUT_DIR, "lower.jpg")
    out_path = os.path.join(OUT_DIR, "stitched.jpg")
    cv2.imwrite(up_path, upper, [cv2.IMWRITE_JPEG_QUALITY, 95])
    cv2.imwrite(low_path, lower, [cv2.IMWRITE_JPEG_QUALITY, 95])

    print("=" * 52)
    print(f"上部: {upper.shape[1]}x{upper.shape[0]}  下部: {lower.shape[1]}x{lower.shape[0]}")
    print("=" * 52)

    result = stitch_leaf(up_path, low_path, out_path)

    assert result is not None, "拼接返回空结果"
    h, w = result.shape[:2]
    assert h > 1000, f"输出高度异常: {h}（应接近原始 {H}）"
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())
    assert 100 < mean < 250, f"输出亮度异常: {mean:.1f}"

    print("=" * 52)
    print(f"PASS  输出 {w}x{h}  平均亮度 {mean:.1f}")
    print(f"      {out_path}")
    print("=" * 52)


if __name__ == "__main__":
    main()
