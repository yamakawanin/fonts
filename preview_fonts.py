#!/usr/bin/env python3
"""
中文字体预览图生成工具
为 chinese-fonts 仓库中的所有 .ttf 字体生成中文预览 PNG。
"""

import hashlib
import html
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont

# 常量定义
REPO_URL = "https://github.com/yuleshow/chinese-fonts.git"
REPO_DIR = Path(__file__).parent / "chinese-fonts"
OUTPUT_DIR = Path(__file__).parent / "font_previews"

# 画布设置
CANVAS_WIDTH = 1600
BACKGROUND_COLOR = "#fbfaf7"
TEXT_COLOR = "#1f1f1f"
DIVIDER_COLOR = "#d8d3c8"

# 回退字体（用于不支持中文的字体）
FALLBACK_FONT_PATH = REPO_DIR / "汀明體.ttf"

# 字号定义
FONT_SIZES = {
    "title": 56,
    "large": 72,
    "medium": 42,
    "small": 26,
    "tiny": 20,
}

# 预览文本内容
PREVIEW_TEXTS = {
    "large": "天地玄黄，宇宙洪荒。",
    "classic": "春风又绿江南岸，明月何时照我还。",
    "traditional": "學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？",
    "mixed": "中国大陆／臺灣香港：汉字、漢字、龙凤、龍鳳、后里、後裔。",
    "punctuation": "“中文引号”『书名号』：（括号）、逗号，句号。问号？感叹号！",
    "english": "ABC abc 1234567890 Claude VS Code Font Preview",
    "body": "这是一段中文正文预览，用来观察字体在较小字号下的可读性、笔画密度、字距、行距和整体气质。中文字体有些适合标题，有些适合正文，有些更适合海报、古籍、手写或艺术展示。",
    "tiny": "更小字号测试：20px，观察细节是否糊、是否拥挤。",
}


def clone_repo() -> None:
    """克隆字体仓库（如果不存在）"""
    if REPO_DIR.exists():
        print(f"使用已存在的仓库: {REPO_DIR}")
        return
    
    print(f"正在克隆仓库: {REPO_URL}")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(REPO_DIR)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("仓库克隆完成")
    except subprocess.CalledProcessError as e:
        print(f"克隆仓库失败: {e.stderr}")
        sys.exit(1)


def find_ttf_files() -> List[Path]:
    """递归查找所有 .ttf 文件"""
    if not REPO_DIR.exists():
        print(f"错误: 仓库目录不存在 {REPO_DIR}")
        sys.exit(1)
    
    # 同时查找 .ttf 和 .TTF 文件（不区分大小写）
    ttf_files = list(REPO_DIR.glob("**/*.ttf")) + list(REPO_DIR.glob("**/*.TTF"))
    # 去重（以防文件系统不区分大小写导致重复）
    ttf_files = list(set(ttf_files))
    print(f"找到 {len(ttf_files)} 个 .ttf 字体文件")
    return ttf_files


def get_unique_filename(font_path: Path) -> str:
    """生成唯一的输出文件名，避免同名覆盖"""
    stem = font_path.stem
    
    # 检查是否有重名文件
    existing = list(OUTPUT_DIR.glob(f"{stem}.png"))
    if not existing:
        return f"{stem}.png"
    
    # 添加短哈希避免冲突
    hash_str = hashlib.md5(str(font_path).encode()).hexdigest()[:6]
    return f"{stem}_{hash_str}.png"


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """根据最大宽度对文本进行自动换行"""
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    
    if current_line:
        lines.append(current_line)
    
    return lines


def load_font(font_path: Path, size: int) -> Optional[ImageFont.FreeTypeFont]:
    """加载字体文件，返回 None 表示失败"""
    try:
        return ImageFont.truetype(str(font_path), size)
    except Exception as e:
        print(f"  加载字体失败: {font_path.name} (大小 {size}px): {e}")
        return None


def font_supports_chinese(font_path: Path) -> bool:
    """检测字体是否支持中文字符"""
    try:
        font = ImageFont.truetype(str(font_path), 48)
        # 渲染一段中文文本
        test_text = "天地玄黄宇宙洪荒"
        img = Image.new("RGB", (400, 100), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), test_text, fill=TEXT_COLOR, font=font)
        
        # 检查非背景色像素的颜色种类
        pixels = list(img.getdata())
        bg_color = (251, 250, 247)  # BACKGROUND_COLOR RGB
        non_bg_colors = set()
        for pixel in pixels:
            if pixel != bg_color:
                non_bg_colors.add(pixel)
        
        # 如果非背景色像素颜色种类超过 10 种，认为支持中文（方框通常只有边框颜色）
        return len(non_bg_colors) > 10
    except Exception:
        return False


def generate_preview(font_path: Path) -> bool:
    """为单个字体生成预览图，返回是否成功"""
    try:
        # 创建画布
        image = Image.new("RGB", (CANVAS_WIDTH, 2400), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)
        
        # 检测字体是否支持中文
        supports_chinese = font_supports_chinese(font_path)
        
        y_offset = 60  # 初始 y 坐标
        
        # 如果不支持中文，添加警告框
        if not supports_chinese:
            warning_font = load_font(FALLBACK_FONT_PATH, 30)
            if warning_font:
                # 绘制警告背景
                draw.rectangle([(60, y_offset - 10), (CANVAS_WIDTH - 60, y_offset + 50)], fill="#ffe6e6")
                draw.text((80, y_offset), "⚠ Warning: This font does not support Chinese characters. Chinese text uses fallback font.", 
                          fill="#cc0000", font=warning_font)
                y_offset += 70
        
        # 1. 字体文件名标题
        title_font = load_font(font_path, FONT_SIZES["title"])
        if not title_font:
            return False
        
        title = font_path.name
        draw.text((80, y_offset), title, fill=TEXT_COLOR, font=title_font)
        y_offset += 80
        
        # 分割线
        draw.line([(80, y_offset), (CANVAS_WIDTH - 80, y_offset)], fill=DIVIDER_COLOR, width=2)
        y_offset += 40
        
        # 2. 大字号中文 - 如果不支持中文，使用回退字体
        if supports_chinese:
            large_font = load_font(font_path, FONT_SIZES["large"])
        else:
            large_font = load_font(FALLBACK_FONT_PATH, FONT_SIZES["large"])
        if large_font:
            draw.text((80, y_offset), PREVIEW_TEXTS["large"], fill=TEXT_COLOR, font=large_font)
            y_offset += 120
        
        # 分割线
        draw.line([(80, y_offset), (CANVAS_WIDTH - 80, y_offset)], fill=DIVIDER_COLOR, width=2)
        y_offset += 40
        
        # 3. 常用中文 - 如果不支持中文，使用回退字体
        if supports_chinese:
            medium_font = load_font(font_path, FONT_SIZES["medium"])
        else:
            medium_font = load_font(FALLBACK_FONT_PATH, FONT_SIZES["medium"])
        if medium_font:
            lines = wrap_text(PREVIEW_TEXTS["classic"], medium_font, CANVAS_WIDTH - 160)
            for line in lines:
                draw.text((80, y_offset), line, fill=TEXT_COLOR, font=medium_font)
                y_offset += 60
            y_offset += 20
        
        # 4. 古文繁体 - 如果不支持中文，使用回退字体
        if supports_chinese:
            traditional_font = load_font(font_path, FONT_SIZES["medium"])
        else:
            traditional_font = load_font(FALLBACK_FONT_PATH, FONT_SIZES["medium"])
        if traditional_font:
            lines = wrap_text(PREVIEW_TEXTS["traditional"], traditional_font, CANVAS_WIDTH - 160)
            for line in lines:
                draw.text((80, y_offset), line, fill=TEXT_COLOR, font=traditional_font)
                y_offset += 60
            y_offset += 20
        
        # 5. 简繁混排 - 如果不支持中文，使用回退字体
        if supports_chinese:
            mixed_font = load_font(font_path, FONT_SIZES["medium"])
        else:
            mixed_font = load_font(FALLBACK_FONT_PATH, FONT_SIZES["medium"])
        if mixed_font:
            lines = wrap_text(PREVIEW_TEXTS["mixed"], mixed_font, CANVAS_WIDTH - 160)
            for line in lines:
                draw.text((80, y_offset), line, fill=TEXT_COLOR, font=mixed_font)
                y_offset += 60
            y_offset += 20
        
        # 6. 标点测试
        if medium_font:
            lines = wrap_text(PREVIEW_TEXTS["punctuation"], medium_font, CANVAS_WIDTH - 160)
            for line in lines:
                draw.text((80, y_offset), line, fill=TEXT_COLOR, font=medium_font)
                y_offset += 60
            y_offset += 20
        
        # 分割线
        draw.line([(80, y_offset), (CANVAS_WIDTH - 80, y_offset)], fill=DIVIDER_COLOR, width=2)
        y_offset += 40
        
        # 7. 英文数字
        if medium_font:
            lines = wrap_text(PREVIEW_TEXTS["english"], medium_font, CANVAS_WIDTH - 160)
            for line in lines:
                draw.text((80, y_offset), line, fill=TEXT_COLOR, font=medium_font)
                y_offset += 60
            y_offset += 20
        
        # 8. 小字号正文测试 - 如果不支持中文，使用回退字体
        if supports_chinese:
            small_font = load_font(font_path, FONT_SIZES["small"])
        else:
            small_font = load_font(FALLBACK_FONT_PATH, FONT_SIZES["small"])
        if small_font:
            lines = wrap_text(PREVIEW_TEXTS["body"], small_font, CANVAS_WIDTH - 160)
            for line in lines:
                draw.text((80, y_offset), line, fill=TEXT_COLOR, font=small_font)
                y_offset += 40
            y_offset += 20
        
        # 9. 更小字号测试 - 如果不支持中文，使用回退字体
        if supports_chinese:
            tiny_font = load_font(font_path, FONT_SIZES["tiny"])
        else:
            tiny_font = load_font(FALLBACK_FONT_PATH, FONT_SIZES["tiny"])
        if tiny_font:
            lines = wrap_text(PREVIEW_TEXTS["tiny"], tiny_font, CANVAS_WIDTH - 160)
            for line in lines:
                draw.text((80, y_offset), line, fill=TEXT_COLOR, font=tiny_font)
                y_offset += 30
            y_offset += 20
        
        # 裁剪画布到实际内容高度
        if y_offset < image.height:
            image = image.crop((0, 0, CANVAS_WIDTH, y_offset + 40))
        
        # 保存图像
        output_filename = get_unique_filename(font_path)
        output_path = OUTPUT_DIR / output_filename
        image.save(output_path, "PNG")
        
        return True
        
    except Exception as e:
        print(f"  生成预览失败: {font_path.name}: {e}")
        return False


def generate_index_html(font_files: List[Path], successful: List[Path]) -> None:
    """生成 index.html 网页"""
    html_path = OUTPUT_DIR / "index.html"
    
    # 构建字体到预览图的映射
    preview_map = {}
    for font_path in successful:
        output_filename = get_unique_filename(font_path)
        preview_map[font_path] = output_filename
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中文字体预览</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}
        .stats {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 30px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-5px);
        }}
        .card img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .card .info {{
            padding: 15px;
        }}
        .card .font-name {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .card .font-path {{
            font-size: 12px;
            color: #888;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <h1>中文字体预览</h1>
    <div class="stats">
        <p>共 {len(font_files)} 个字体文件 | 成功生成 {len(successful)} 张预览图</p>
    </div>
    <div class="grid">
"""
    
    for font_path in successful:
        preview_filename = preview_map[font_path]
        relative_path = font_path.relative_to(REPO_DIR)
        font_name = html.escape(font_path.stem)
        font_path_escaped = html.escape(str(relative_path))
        # URL编码文件名，解决浏览器无法加载中文/特殊字符文件名的问题
        preview_filename_encoded = quote(preview_filename)
        
        html_content += f"""        <div class="card">
            <a href="{preview_filename_encoded}" target="_blank">
                <img src="{preview_filename_encoded}" alt="{font_name}" loading="lazy">
            </a>
            <div class="info">
                <div class="font-name">{font_name}</div>
                <div class="font-path">{font_path_escaped}</div>
            </div>
        </div>
"""
    
    html_content += """    </div>
</body>
</html>
"""
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"索引网页已生成: {html_path}")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("中文字体预览图生成工具")
    print("=" * 60)
    
    # 1. 克隆仓库
    clone_repo()
    
    # 2. 创建输出目录
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 3. 查找所有 .ttf 文件
    ttf_files = find_ttf_files()
    if not ttf_files:
        print("未找到任何 .ttf 字体文件")
        return
    
    # 4. 为每个字体生成预览图
    successful = []
    failed = []
    errors = []
    
    for i, font_path in enumerate(ttf_files, 1):
        print(f"[{i}/{len(ttf_files)}] 生成预览: {font_path.name}")
        
        if generate_preview(font_path):
            successful.append(font_path)
        else:
            failed.append(font_path)
            errors.append(f"{font_path}: 字体加载或生成失败")
    
    # 5. 保存错误日志
    if errors:
        error_path = OUTPUT_DIR / "errors.txt"
        with open(error_path, "w", encoding="utf-8") as f:
            f.write("\n".join(errors))
        print(f"错误日志已保存: {error_path}")
    
    # 6. 生成索引网页
    if successful:
        generate_index_html(ttf_files, successful)
    
    # 7. 输出统计信息
    print("\n" + "=" * 60)
    print("处理完成")
    print("=" * 60)
    print(f"共找到 {len(ttf_files)} 个 .ttf 字体文件")
    print(f"成功生成 {len(successful)} 张预览图")
    print(f"失败 {len(failed)} 个")
    print(f"输出目录: {OUTPUT_DIR}")
    if successful:
        print(f"索引网页: {OUTPUT_DIR / 'index.html'}")
    print("=" * 60)


if __name__ == "__main__":
    main()