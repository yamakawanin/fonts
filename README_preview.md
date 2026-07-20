# 中文字体预览图生成工具

该工具可以自动从 GitHub 仓库 `https://github.com/yuleshow/chinese-fonts` 克隆所有 `.ttf` 字体文件，并为每个字体生成一张中文预览 PNG 图片。

## 功能特性

- 自动克隆仓库（如果本地不存在）
- 递归扫描所有 `.ttf` 字体文件
- 为每个字体生成包含多种中文样张的预览图
- 处理同名文件（通过添加哈希后缀避免覆盖）
- 生成 `index.html` 网页，方便在浏览器中查看所有预览图
- 错误处理：记录加载失败的字体到 `font_previews/errors.txt`

## 安装与运行

### 1. 创建虚拟环境（推荐）

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或者 Windows: .venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行脚本

```bash
python preview_fonts.py
```

脚本会自动：
- 检查并克隆 `chinese-fonts` 仓库（如果不存在）
- 扫描所有 `.ttf` 字体文件
- 在 `font_previews/` 目录下生成预览 PNG 图片
- 生成 `font_previews/index.html` 网页
- 在控制台显示处理进度和最终统计

## 输出结果

- **预览图目录**：`font_previews/`
- **索引网页**：`font_previews/index.html`（可在浏览器中打开）
- **错误日志**：`font_previews/errors.txt`（如有字体加载失败）

## 注意事项

- 仅处理 `.ttf` 格式字体，不处理 `.otf` 或 `.ttc` 格式
- 不会将字体文件复制到输出目录
- 不会修改原始仓库内容
- 支持中文文件名、空格、括号等特殊字符