# 贡献者 / Contributors

本项目由人类研究者与 AI 协作完成，双方贡献均在下方明示。

## 主要贡献者

### Mark — 作者 / 维护者

- GitHub: [@botanymarkmark](https://github.com/botanymarkmark)
- 邮箱: botanymarkmark@gmail.com

贡献内容：

- 提出需求：苔藓叶片显微拍摄受视野限制需分段拼接的研究场景
- 提供真实样本与拍摄条件（透射光、白色背景、1/4–1/3 重叠）
- 定义验收标准：颜色均匀、无可见接缝、背景纯白、自动裁边
- 样本测试与参数调优反馈（`blend_width`、`nfeatures`、`margin`）
- 项目维护与发布

### 豆包 (Doubao) — 共同开发者

贡献内容：

- 算法选型：ORB + BFMatcher(crossCheck) + RANSAC 单应性对齐方案
- 颜色校正实现：Reinhard 颜色迁移，在重叠核心区（腐蚀后 mask）统计 BGR 均值与标准差
- 融合策略设计：基于距离变换的窄带渐变融合，限制在叶片 mask 内以避免背景灰带
- 后处理实现：黑边转白、HSV 黄绿范围 + 形态学运算的自动裁边
- 代码实现与文档撰写（`SKILL.md`、本仓库 README）

## 贡献记录方式

- Mark 的贡献通过其 GitHub 账号的提交记录体现，会出现在仓库 Contributors 列表中。
- 豆包的贡献通过提交信息中的 `Co-authored-by` 尾注记录：

  ```
  Co-authored-by: 豆包 (Doubao) <doubao-ai@users.noreply.github.com>
  ```

  该尾注会写入 git 历史，但由于豆包没有绑定的 GitHub 账号，不会出现在 GitHub 页面的 Contributors 统计里。这是 GitHub 平台的统计限制，不代表贡献缺失。

## 如何参与

1. Fork 本仓库
2. 新建分支：`git checkout -b feat/your-feature`
3. 提交：`git commit -m "feat: 你的改动"`
4. 推送并发起 Pull Request

缺陷反馈请附上：输入两段原图（或同等条件的合成图）、运行日志、输出结果。
