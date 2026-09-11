# HTML 闪卡运行时契约

生成器 `scripts/build_flashcards.py` 负责实现本契约。只有用户要求修改界面或交互时，才需要读取本文件并调整模板。

## 数据格式

输入 JSON 可以是数组：

```json
[
  {"front": "DNA", "back": "脱氧核糖核酸", "section": "en-cn"},
  {"front": "细胞膜", "back": "包围细胞并控制物质进出的结构。", "section": "cn-def"}
]
```

也可以是对象：

```json
{
  "title": "生物化学 · 复习卡片",
  "cards": []
}
```

`front` 和 `back` 必须为非空字符串；`section` 可省略。生成器会过滤空条目并按 `front + back` 去重。

## 页面结构

必须包含：

- 标题、当前分类和键盘提示。
- 分类筛选按钮，至少包含“全部”和输入中出现的 section。
- 进度条与统计：剩余、已掌握、待复习。
- 卡片索引：第 X / Y 张。
- 翻转卡片。
- 操作按钮：上一张、忘了、翻转、记得。
- 工具栏：打乱重来、复习遗忘词、词汇表、全部重置。
- 词汇表模态框，支持实时搜索 front/back、状态标记和滚动。
- 全部复习完毕提示。

页面不得依赖外部资源，必须能通过 `file://` 直接打开。

## 会话状态

- `cards`：全部卡片。
- `sectionFilter`：当前分类，默认 `all`。
- `queue`：当前待复习卡片索引。
- `mastered`：已掌握集合。
- `review`：待复习集合。
- `history`：用于撤销的状态快照栈。
- `flipped`：当前卡片是否翻开。

“记得”把当前卡片加入 mastered，并从 queue 和 review 中移除。“忘了”把卡片加入 review，并把它移动到队列末尾。队列耗尽且有 review 卡片时，重新洗牌形成下一轮；没有 review 时显示完成状态。

“上一张”从 `history` 恢复上一操作前的 queue、mastered、review、sectionFilter 和当前卡片。历史为空时按钮禁用。

## 分类

切换分类时重建当前分类的学习会话，不清除其他分类的掌握记录。统计与进度只计算当前分类。分类为空时显示全部。

## 词汇表

词汇行显示状态、front 和 back。状态：

- `已掌握`
- `待复习`
- `未学习`

搜索框使用静态 HTML 和 `addEventListener`，不得通过 `innerHTML` 动态插入卡片文本。打开模态框时聚焦搜索框，按 `Escape` 关闭。

## 键盘操作

- `Space` / `Enter`：翻转。
- `ArrowLeft`：忘了。
- `ArrowRight`：记得。
- `ArrowUp`：上一张。
- `R`：重置全部。
- `F`：复习遗忘词。
- `Escape`：关闭词汇表。

输入框获得焦点时，除 `Escape` 外不触发卡片快捷键。

## 视觉与适配

- 默认深色主题，使用 CSS 变量定义颜色。
- 桌面和移动端均可用，按钮触控区域不小于 44px。
- 卡片正面文字明显大于背面；长定义可滚动。
- 使用 CSS 3D transform 实现翻转。
- 尊重 `prefers-reduced-motion`，减少或关闭动画。
- 不依赖 emoji 才能理解按钮含义，按钮同时包含文字。
- 文本使用 `textContent` 写入，禁止用户数据进入 `innerHTML`。

## 数据注入安全

推荐做法：

```html
<script id="flashcard-data" type="application/json">
  [{"front":"DNA","back":"脱氧核糖核酸","section":"en-cn"}]
</script>
```

```javascript
const cards = JSON.parse(document.getElementById("flashcard-data").textContent);
```

生成器必须至少处理：

- JSON 中的 `<` 替换为 `\u003c`，避免提前关闭 script 标签。
- 不使用用户内容拼接 JavaScript 字符串。
- 标题使用 HTML escaping。
- 控制字符在解析阶段清理。

## 修改模板的边界

用户要求换色、调整文案或增加功能时可以修改生成器输出；不得借 UI 修改移除复习算法、词汇表、键盘操作、可离线运行或安全渲染。
