"""
苔藓叶片显微照片拼接工具
用法: python leaf_stitch.py <upper_img> <lower_img> <output_img>
示例: python leaf_stitch.py ye1_1.jpg ye1_2.jpg ye1_result.jpg
"""
import cv2
import numpy as np
import sys

def stitch_leaf(img1_path, img2_path, output_path, blend_width=150):
    """
    拼接同一片叶片的上下两段显微照片。
    img1: 上部（叶尖端）
    img2: 下部（叶基端）
    """
    # 读取图片
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    if img1 is None or img2 is None:
        raise ValueError("无法读取图片")
    
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    print(f"上部: {w1}x{h1}, 下部: {w2}x{h2}")
    
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # ===== ORB 特征匹配 =====
    orb = cv2.ORB_create(nfeatures=10000)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    good = matches[:500]
    
    pts1 = np.float32([kp1[m.queryIdx].pt for m in good])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good])
    
    H, mask = cv2.findHomography(pts2, pts1, cv2.RANSAC, 5.0)
    inliers = int(np.sum(mask))
    print(f"匹配内点: {inliers}")
    if inliers < 20:
        print("警告: 匹配点较少，拼接可能不准")
    
    # ===== 颜色校正（Reinhard 方法） =====
    warped2 = cv2.warpPerspective(img2, H, (w1, h1))
    
    # 叶片 mask（非白背景）
    leaf1 = (gray1 < 245).astype(np.uint8)
    gray_w2 = cv2.cvtColor(warped2, cv2.COLOR_BGR2GRAY)
    leaf2 = ((gray_w2 > 10) & (gray_w2 < 245)).astype(np.uint8)
    
    overlap = leaf1 & leaf2
    kernel = np.ones((30, 30), np.uint8)
    overlap_inner = cv2.erode(overlap, kernel, iterations=2)
    
    n_over = int(np.sum(overlap_inner))
    print(f"重叠核心区像素: {n_over}")
    
    if n_over > 500:
        def stat(im, m):
            b = im[:,:,0][m>0].astype(np.float32)
            g = im[:,:,1][m>0].astype(np.float32)
            r = im[:,:,2][m>0].astype(np.float32)
            return np.mean(b), np.mean(g), np.mean(r), np.std(b), np.std(g), np.std(r)
        
        m1b, m1g, m1r, s1b, s1g, s1r = stat(img1, overlap_inner)
        m2b, m2g, m2r, s2b, s2g, s2r = stat(warped2, overlap_inner)
        
        print(f"上部颜色均值: B={m1b:.1f} G={m1g:.1f} R={m1r:.1f}")
        print(f"下部颜色均值: B={m2b:.1f} G={m2g:.1f} R={m2r:.1f}")
        
        img2c = img2.astype(np.float32)
        img2c[:,:,0] = (img2c[:,:,0] - m2b) * (s1b / max(s2b,1)) + m1b
        img2c[:,:,1] = (img2c[:,:,1] - m2g) * (s1g / max(s2g,1)) + m1g
        img2c[:,:,2] = (img2c[:,:,2] - m2r) * (s1r / max(s2r,1)) + m1r
        img2c = np.clip(img2c, 0, 255).astype(np.uint8)
        print("颜色校正完成")
    else:
        img2c = img2
        print("重叠区不足，跳过颜色校正")
    
    # ===== 计算画布范围 =====
    corners2 = np.float32([[0,0],[0,h2],[w2,h2],[w2,0]]).reshape(-1,1,2)
    c2w = cv2.perspectiveTransform(corners2, H)
    corners1 = np.float32([[0,0],[0,h1],[w1,h1],[w1,0]]).reshape(-1,1,2)
    allc = np.concatenate((corners1, c2w), axis=0)
    
    xmin = int(np.floor(allc[:,:,0].min()))
    xmax = int(np.ceil(allc[:,:,0].max()))
    ymin = int(np.floor(allc[:,:,1].min()))
    ymax = int(np.ceil(allc[:,:,1].max()))
    
    tx = -xmin
    ty = -ymin
    out_w = xmax - xmin
    out_h = ymax - ymin
    
    print(f"输出画布: {out_w}x{out_h}")
    
    # 变换校正后的下部图
    T = np.array([[1,0,tx],[0,1,ty],[0,0,1]], dtype=np.float64)
    warped2_full = cv2.warpPerspective(img2c, T.dot(H), (out_w, out_h))
    
    # 上部图放到画布坐标系
    img1_canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    img1_canvas[ty:ty+h1, tx:tx+w1] = img1
    
    # ===== 叶片 mask（用于融合权重） =====
    def get_leaf(im):
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        return (g < 245).astype(np.uint8)
    
    leaf1_cv = get_leaf(img1)
    leaf2_cv = get_leaf(img2c)
    
    leaf1_canvas = np.zeros((out_h, out_w), dtype=np.uint8)
    leaf1_canvas[ty:ty+h1, tx:tx+w1] = leaf1_cv
    
    ones2 = np.ones((h2, w2), dtype=np.uint8)
    leaf2_full = cv2.warpPerspective(leaf2_cv * 255, T.dot(H), (out_w, out_h))
    leaf2_full = (leaf2_full > 0).astype(np.uint8)
    
    # ===== 窄带渐变融合 =====
    only1 = leaf1_canvas & (~leaf2_full.astype(bool))
    only2 = leaf2_full & (~leaf1_canvas.astype(bool))
    both = leaf1_canvas & leaf2_full
    
    # 距离变换
    dist_to_1 = cv2.distanceTransform((~only1.astype(bool)).astype(np.uint8), cv2.DIST_L2, 5)
    dist_to_2 = cv2.distanceTransform((~only2.astype(bool)).astype(np.uint8), cv2.DIST_L2, 5)
    
    # 渐变权重
    w1 = np.clip(dist_to_2 / blend_width, 0, 1)
    w2 = np.clip(dist_to_1 / blend_width, 0, 1)
    
    in_both = both.astype(bool)
    w1 = w1 * in_both
    w2 = w2 * in_both
    
    # 完整权重图
    w1_full = np.zeros((out_h, out_w), dtype=np.float32)
    w2_full = np.zeros((out_h, out_w), dtype=np.float32)
    
    w1_full[only1 > 0] = 1.0
    w2_full[only2 > 0] = 1.0
    w1_full[in_both] = w1[in_both]
    w2_full[in_both] = w2[in_both]
    
    # 归一化
    wsum = w1_full + w2_full
    wsum[wsum == 0] = 1.0
    w1_norm = w1_full / wsum
    w2_norm = w2_full / wsum
    
    # 3 通道
    w1_3 = np.stack([w1_norm, w1_norm, w1_norm], axis=2)
    w2_3 = np.stack([w2_norm, w2_norm, w2_norm], axis=2)
    
    # 加权融合
    result = (img1_canvas.astype(np.float32) * w1_3 + 
              warped2_full.astype(np.float32) * w2_3).astype(np.uint8)
    
    # ===== 背景转白色 =====
    gray_r = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    black_mask = gray_r < 10
    white_bg = np.ones((out_h, out_w, 3), dtype=np.uint8) * 255
    leaf_mask = ~black_mask
    white_bg[leaf_mask] = result[leaf_mask]
    
    # ===== 按叶片裁剪 =====
    hsv = cv2.cvtColor(white_bg, cv2.COLOR_BGR2HSV)
    lower_green = np.array([10, 15, 60])
    upper_green = np.array([70, 255, 255])
    leaf_mask_hsv = cv2.inRange(hsv, lower_green, upper_green)
    
    dark = (gray_r < 80).astype(np.uint8) * 255
    leaf_mask_hsv = cv2.bitwise_or(leaf_mask_hsv, dark)
    
    morph_k = np.ones((20, 20), np.uint8)
    leaf_mask_hsv = cv2.morphologyEx(leaf_mask_hsv, cv2.MORPH_CLOSE, morph_k)
    leaf_mask_hsv = cv2.morphologyEx(leaf_mask_hsv, cv2.MORPH_OPEN, morph_k)
    
    contours, _ = cv2.findContours(leaf_mask_hsv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        largest = max(contours, key=cv2.contourArea)
        x, y, cw, ch = cv2.boundingRect(largest)
        margin = 80
        x1c = max(0, x - margin)
        y1c = max(0, y - margin)
        x2c = min(out_w, x + cw + margin)
        y2c = min(out_h, y + ch + margin)
        final = white_bg[y1c:y2c, x1c:x2c]
        print(f"最终尺寸: {final.shape[1]}x{final.shape[0]}")
    else:
        final = white_bg
    
    cv2.imwrite(output_path, final)
    print(f"已保存: {output_path}")
    return final

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("用法: python leaf_stitch.py <上部图> <下部图> <输出图>")
        sys.exit(1)
    stitch_leaf(sys.argv[1], sys.argv[2], sys.argv[3])
