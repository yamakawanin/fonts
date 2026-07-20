# 中文字体预览

这个仓库提供一个可重复运行的中文字体预览生成器，并保存最新生成的预览图，方便直接在 GitHub 浏览字体的实际排版效果。

## 在线浏览

完整预览索引位于 [font_previews/index.html](font_previews/index.html)。每张预览图包含大字、简繁混排、标点、英文数字与正文小字号样张。

![字体预览示例](font_previews/GenYoGothicTW-Regular_996958.png)

## 本地生成

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python preview_fonts.py
```

脚本会浅克隆 [yuleshow/chinese-fonts](https://github.com/yuleshow/chinese-fonts)，扫描其中的 `.ttf` 字体并在 `font_previews/` 中生成 PNG 与索引页面。字体源文件和虚拟环境不会提交到本仓库；预览图会随仓库同步。

## 更新预览

重新运行脚本后，提交 `font_previews/` 中的变更即可更新 GitHub 上的效果。

```bash
git add font_previews
git commit -m "Update font previews"
git push
```
