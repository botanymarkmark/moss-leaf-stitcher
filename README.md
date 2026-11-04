# moss-leaf-stitch

> 苔藓叶片显微照片拼接工具 · Stitch two partial micrographs of a moss leaf into one seamless image.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/opencv--python-4.x-green)](https://opencv.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

显微镜视野装不下一整片苔藓叶片，于是分上下两段拍——这个工具把两段拼回去，并且拼得看不出接缝。

---

## 它解决什么问题

分视野拍摄会带来三个麻烦，肉眼一看就露馅：

1. **错位** —— 两段没有严格对齐，叶片中脉断成两截
2. **色差** —— 曝光/焦距不同，上半段偏亮偏黄，下半段偏暗偏冷
3. **硬接缝** —— 简单拼接会在重合区留下一道明显的直线边界

本工具一次性处理这三件事，输出可以直接进论文图版的叶片全图。

## 特性

| 步骤 | 方法 | 效果 |
|---|---|---|
| 对齐 | ORB 特征 + BFMatcher(crossCheck) + RANSAC 单应性 | 自动处理平移、旋转、轻微透视 |
| 颜色校正 | Reinhard 颜色迁移（重叠核心区统计 BGR 均值/标准差） | 统一上下两段色调与对比度 |
| 融合 | 距离变换 + 窄带渐变（默认 150 px） | 只在叶片 mask 内过渡，不产生背景灰带 |
| 背景 | 变换黑边 → 纯白 | 符合显微观察与印刷习惯 |
| 裁剪 | HSV 黄绿范围 + 形态学闭开运算找最大轮廓 | 自动去掉多余白边，留 80 px 余量 |

## 安装

```bash
git clone https://github.com/botanymarkmark/moss-leaf-stitcher.git
cd moss-leaf-stitcher
python -m pip install -r requirements.txt
```

依赖只有两个：`opencv-python`、`numpy`。

## 使用

### 命令行

```bash
python scripts/leaf_stitch.py <上部图> <下部图> <输出图>
```

```bash
python scripts/leaf_stitch.py 叶1_上.jpg 叶1_下.jpg 叶1_拼接.jpg
```

- **上部图**：叶尖端那一段
- **下部图**：叶基端那一段
- **顺序不能反**

### Python 调用

```python
import sys
sys.path.insert(0, 'scripts')
from leaf_stitch import stitch_leaf

result = stitch_leaf(
    img1_path='叶1_上.jpg',    # 叶尖端
    img2_path='叶1_下.jpg',    # 叶基端
    output_path='叶1_拼接.jpg',
    blend_width=150,           # 渐变融合带宽度（px）
)
```

### 作为 Agent Skill 使用

本仓库遵循 [SKILL.md](SKILL.md) 规范（`name` + `version` + `description` frontmatter）。把整个目录放进你的 skills 目录即可被 Agent 自动发现：

```bash
# WorkBuddy / 通用 skills 目录
cp -r moss-leaf-stitcher ~/.workbuddy/skills/moss-leaf-stitch
```

`SKILL.md` 内含完整触发条件、参数说明与排错手册。

## 参数与调优

| 参数 | 默认 | 调大的效果 |
|---|---|---|
| `nfeatures` | 10000 | 纹理少、匹配点不足时加大 |
| `blend_width` | 150 | 接缝仍可见时加大到 200–300 |
| RANSAC 阈值 | 5.0 | 两段形变较大时放宽到 8–10 |

## 拍摄要求

- 两段之间要有 **1/4 – 1/3 叶片长度**的重叠，否则特征匹配会失败
- 背景用白色或浅色（常规透射光场景）；深色背景会影响叶片 mask 提取
- 同一片叶子的两段在相近光照下拍摄，色差校正才有充足样本

## 排错

**拼接后有明显接缝** → 加大 `blend_width` 到 200 或 300。

**上下色差还在** → 看运行日志里的「重叠核心区像素」：小于 500 时颜色校正会自动跳过，需要重拍并保证更大重叠。

**背景不是白色** → 脚本只把接近黑色的区域转白。原始背景本身是灰/蓝色时需手动处理。

**叶片被裁掉一截** → `margin` 默认 80 px，窄叶或长条形标本可调大到 150。

## 目录结构

```
moss-leaf-stitcher/
├── SKILL.md              # Agent Skill 定义与完整文档
├── scripts/
│   └── leaf_stitch.py    # 主程序
├── tests/
│   └── smoke_test.py     # 合成图端到端自检
├── requirements.txt
├── CONTRIBUTORS.md
└── LICENSE
```

## 自检

无需真实样本，用合成图跑通全流程：

```bash
python tests/smoke_test.py
```

## 贡献者

| 角色 | 贡献者 | 职责 |
|---|---|---|
| 作者 / 维护者 | **Mark** ([@botanymarkmark](https://github.com/botanymarkmark)) | 需求定义、拍摄与样本测试、验收 |
| 共同开发者 | **豆包 (Doubao)** | 算法设计、代码实现、文档撰写 |

完整说明见 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

> 说明：GitHub 仓库右侧的 Contributors 列表只统计「提交者邮箱已绑定 GitHub 账号」的提交。豆包作为 AI 协作方没有 GitHub 账号，因此以 `Co-authored-by` 尾注形式记录在提交历史中，并在此表与 CONTRIBUTORS.md 中列明。

## License

[MIT](LICENSE) © 2026 Mark
