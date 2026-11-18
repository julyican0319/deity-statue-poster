---
name: deity-statue-poster
description: 神明雕像庙宇文化海报生成器——把用户上传的神像/神明雕像照片逐张转成 3:4 直式高级庙宇文化海报：上半部满铺保真照片，下半部米白底精致庙绘插画（金色光环、祥云纹、红色印章、衬线大字距英文、直排繁体中文、发丝线编号），并由程序锁定精确 50/50 分割、清除生成服务强制水印。凡用户上传神像、神明雕像、佛道教造像、宫庙神將照片并要求做海报、艺术化、生成图片，或提到庙宇文化海报、宫庙文创、神明海报、神像艺术照时，必须使用本 skill，即使用户没有明说"海报"二字。不适用于普通人物肖像、宠物、产品、建筑、风景等非神明雕像题材——这些场景不要触发本 skill。
---

# Deity Statue Poster（神明雕像庙宇文化海报）

把一张神明雕像照片，做成一张「上半部真实摄影、下半部庙绘插画」的 3:4 庙宇文化海报。
这套流程已在真实交付中验证过两轮迭代：第一版极简几何风格被推翻，最终确认的是本文件描述的
庙绘文化风格。不要回退到几何色块风格，也不要扩展到非神明雕像题材。

## 输入参数（向用户收集或按默认推断）

| 参数 | 默认 | 说明 |
|---|---|---|
| 源图 | 必需 | 一张或多张神像照片/截图。**截图必须先裁出真实照片区**（见流程第 1 步） |
| 英文标题 | 按主体推断 | 1–3 词压缩式命名，如 `GOLDEN SHRINE` / `GOLDEN RIDER` / `THE SEATED ONE`；多张成系列时保持同一命名气质 |
| 直排中文 | 按主体推断 | 两组四字短语，如「金甲護法 · 神威顯赫」。**不要虚构宫庙名、神明名讳、真实年份**——用描述性通用词，并主动告知用户可提供确切名讳后逐字替换 |
| 元信息 | `FOLK SHRINE · {年份}` + `NO. {序号} — {年份}` | 序号按张数递增 |
| 输出目录 | 工作区 `海报项目/成品` | 每轮风格迭代用独立子目录（成品 / 成品v2 …），不要覆盖旧版 |

生成前必须告知用户：图像生成消耗额外积分（每张约 5–10）。

## 固定流程（按序执行，不要跳步）

### 第 1 步：源图预处理

先逐一查看原图。如果源图是手机截图（带状态栏、播放按钮、聊天 UI），用 ffmpeg 把真实照片
区域裁出来——UI 残留混进海报上层照片会直接报废。裁切后逐张复查边缘是否干净。
ffmpeg 在 `~/.workbuddy/binaries/ffmpeg/bin`（不在默认 PATH，需手动 export；查分辨率用
`ffmpeg -i`，本机 ffprobe 与 ffmpeg 同体、`-select_streams` 不可用）。

同时建立素材地图：主体身份特征（脸、冠冕、坐骑、手持物）、空间逻辑、色彩机会。
这些决定生成提示词里的主体描述和下半部插画要素。

### 第 2 步：图像生成（每张一次图生图调用）

用 ImageGen，`size` 用 900x1200 竖幅，`input_fidelity: high`，`image1` 传裁切后的照片。
提示词按下面四段模板填写（方括号为占位符），**逐字写明所有被允许的文字，禁止其余文字**：

```
Vertical 3:4 aspect ratio museum-quality temple culture poster, strict 50/50
horizontal split into two equal zones divided by one clean horizontal line at
the exact vertical midpoint.

TOP HALF (full bleed edge-to-edge, no margins): the provided photograph of
[主体场景完整描述——继承素材地图中的身份锚点]. Keep it an unmodified real
photograph: identical subject structure, real texture, natural light and
color, only a subtle editorial color grade; zoom-crop and naturally extend
the background to fill the entire upper half without stretching or
distorting the subject.

BOTTOM HALF: warm cream off-white paper with an elegant refined
temple-poster illustration of the SAME [主体简述] — semi-flat painterly
sacred-art style with delicate gold armor/robe details, jewelry dots, fine
line work (NOT cartoon, NOT thick geometric blocks), a thin gold halo ring
circle behind the figure, two auspicious cloud scroll motifs in fine gold
outline flanking at lower left and lower right, vast cream whitespace.

TYPOGRAPHY: elegant letterspaced serif uppercase title '{英文标题}' at the
left middle of the cream zone, small letterspaced serif caption
'FOLK SHRINE · {年份}' beneath it, a small red square seal stamp with subtle
seal-script marks below the title, and vertical Traditional Chinese caption
reading top-to-bottom '{中文组一}' then '{中文组二}' on the right side of the
cream zone, rendered in clean accurate characters; at the very bottom center
a thin horizontal hairline above small letterspaced text 'NO. {序号} — {年份}'.
These are the only words allowed.

GUARDRAILS: no watermark of any kind, no logo, no signature; the photo half
must remain a real photograph; no e-commerce or template look; no extra or
misspelled text; keep critical content away from extreme top and bottom edges.
```

提示词为什么这样写：`strict 50/50` 与 `exact vertical midpoint` 是给模型的意图锚点
（模型仍会偏差 ±5%，第 4 步用程序兜底）；`NOT cartoon, NOT thick geometric blocks`
防止回退到已否决的几何风格；`unmodified real photograph` 是因为模型倾向把照片半区
也重绘成插画。

### 第 3 步：生成结果质检（每张都查，全过才算过）

1. **上半部**：照片是否满铺（无米白留边）、主体结构无变形、光影自然。
2. **下半部**：插画精致度、光环/祥云/印章齐全、无卡通化。
3. **文字逐字核对**：中英文分别读出来比对。直排中文特别容易崩字、缺字——发现错字
   就重生成一次并在提示词里强调该词；仍失败则在提示词中移除中文、留出干净竖排
   文字安全区，最后用 PIL + 系统繁体字型（如 `C:\Windows\Fonts\kaiu.ttf` 楷体、
   `msjh.ttc` 黑体）叠加，字准优先于风格一体化。印章允许装饰性仿篆纹样。
4. **水印**：右下角必有服务强制水印「AI生成 WORKBUDDY」，提示词挡不掉，
   **不要为了去水印重新生成**——交给第 4 步修补。

### 第 4 步：程序合成（确定性收尾，用本 skill 自带脚本）

```
python <本skill目录>/scripts/compose_poster.py --src 生成图.png --out 成品.jpg \
    [--bottom-crop 20]   # 源图最底行有暗边时裁掉，避免镜像补纹带出黑线
```

脚本自动完成：检测照片/米白分割行 → 同色纸纹+噪声羽化修补水印（默认按比例定位
右下角）→ 上半部 cover-fit（不拉伸）、下半部等宽缩放 + 镜像纸纹补带（或高米白区
fit-height + 渐变侧补）→ 输出 1200x1600、分割线数学锁定 y=800。

修补遮罩只羽化画布内部的边；贴画布边的两侧必须不透明——羽化到边界会露出水印残影
（这是踩过的坑）。修补区默认 `x≥0.855w, y≥0.93h`，若源图底部还有居中的编号行或
发丝线延伸到右侧（如发丝线尖端到 x≈0.79w），确认不重叠，重叠了就缩小 patch。

### 第 5 步：终检与交付

1. 整图预览：分割精确各半、交界无照片残条；文字完整。
2. 用 ffmpeg 裁右下角放大复查：无水印残影、无修补色块边界（`crop=450:280:750:1320`）。
3. `present_files` 呈现全部成品。
4. 回复中说明：文案为通用词，提供确切神明名讳/宫庙名/年份后可逐字替换重出；
   印章为装饰性仿篆，非真实名章。

## 输出格式

- 单张成品：`poster-{系列标识}-{序号}.jpg`，1200x1600（精确 3:4），quality 95。
- 分割线恒在 y=800（canvas 中点），不依赖生成模型。
- 多张成系列时共享：同一英文命名气质、同一元信息格式、同一字体系统；主体插画
  各自响应源图。

## 风格硬约束（验收标准）

- 上半部：真实摄影质感保真，仅轻微杂志调色；背景可自然延伸适配画幅，禁止拉伸扭曲主体。
- 下半部：米白纸底（约 #F0EADC 一带，实际取自生成结果）、半扁平庙绘、细线描、
  金色光环圈、金色祥云纹一对、红色方形印章、大留白、主体居中。
- 禁止：卡通感、廉价向量感、电商模板感、厚几何色块（v1 已否决风格）、多余外框、
  水印、虚构宫庙名/名讳/事实性陈述、错字崩字。

## 调用示例

用户：「@神像照片 帮我把这张做成上次那种庙宇风海报」
→ 触发本 skill。无既定文案时推断：红脸金甲骑白马 → 标题 `GOLDEN RIDER`、
直排「赤面神將 · 白馬護佑」、编号 NO. 01 — 2026；先告知积分消耗，再走第 1–5 步。

用户：「这三张神像截图，一张一张做，不要拼接」
→ 裁切三张源图 → 循环第 2–4 步三次（提示词文案逐张定制、编号 01/02/03）→ 一次交付三张。
