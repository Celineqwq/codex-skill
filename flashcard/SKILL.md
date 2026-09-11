---
name: flashcard
description: |
  从 TXT、DOCX、PPTX、PDF、图片或粘贴文本中提取知识内容，自动生成英译汉、名词解释或混合模式的交互式 HTML 闪卡。用户需要制作复习卡片、闪卡、词汇卡或将讲义和笔记转成 HTML 学习卡时使用。
metadata:
  short-description: 将讲义、笔记、词汇或术语生成交互式 HTML 闪卡
---

# Flashcard

把输入资料转换成单文件、可离线打开的交互式 HTML 闪卡。

## 使用方式

支持：

- `$flashcard C:\path\notes.pdf`
- `$flashcard word1:释义1 word2:释义2`
- `$flashcard chapter1.pdf chapter2.pptx --mode 英译汉`
- `/flashcard ...` 作为兼容旧用法的写法。

可用模式：`自动`、`英译汉`、`名词解释`、`混合`。未指定时自动判断。

## 结果要求

- 输出一个自包含 HTML 文件，不依赖 CDN、网络或本地服务器。
- 保留已确认的术语、定义和翻译，不补造资料中没有的释义。
- 支持卡片翻转、记得/忘了、随机复习、遗忘词重练、历史回溯、词汇表搜索、重置和键盘操作。
- 默认文件名为 `{主题}-flashcards.html`；已有同名文件且未允许覆盖时先询问用户。
- 少于 3 张卡片仍可生成，但要明确提醒内容较少。
- 本技能不生成 Anki `.apkg` 或 Anki 导出文件，除非后续另行实现。

## 工作流

1. 收集输入文件和参数，确认路径可读。
2. 按格式提取文本。解析规则和格式说明见 `references/input-parsing.md`。
3. 自动识别或遵循用户指定的模式，解析出卡片数组：
   `{ front, back, section }`。
4. 去重时以规范化后的 `front + back` 为准，保留首次出现的条目。
5. 生成卡片 JSON。数据必须使用 `json.dumps(..., ensure_ascii=False)` 或等价安全方式写入，不手工拼接 JavaScript 字符串。
6. 运行生成器：

```powershell
python scripts/build_flashcards.py --input cards.json --output "{主题}-flashcards.html" --title "{主题} · 复习卡片"
```

7. 运行验证器：

```powershell
python scripts/validate_flashcards.py "{主题}-flashcards.html"
```

8. 只有验证通过后才报告结果。若生成失败，保留错误信息并修复后重试。

详细 HTML 运行时契约和可选自定义项见 `references/html-runtime.md`。

## 解析规则

优先级从高到低：

1. 显式成对分隔符：`→`、`←`、`:`、`：`、`-`、`—`、制表符或表格竖线。
2. 编号或项目符号列表中的成对条目。
3. 表格中的双列词条或术语/释义列。
4. 交替出现的术语段落和定义段落。
5. 自然段落中的“术语 + 定义”结构。

无法可靠判断时不要强行切分，保留原文并标记为需要用户确认。

## 安全与质量

- 卡片内容通过 `textContent` 渲染，禁止使用 `innerHTML` 注入用户文本。
- JSON 数据放入 `<script type="application/json">`，由前端 `JSON.parse` 读取。
- HTML 不允许引用外部脚本、样式、字体或图片。
- 不把 OCR 不确定的文字改写成确定结论；无法识别的内容标记为 `[待核对]`。
- 不改动源文件。输出写入用户指定位置或当前输出目录。
- 用户要求改写定义、合并卡片或改变排序时，以用户指令为准，但要保持原文事实边界。

## 输出风格（必须保留）

- 所有面向用户的说明句末尾添加“喵”。
- 面向用户的说明句中的句号 `。` 替换为 `~`。
- 代码、命令、路径、JSON 和 HTML 内部文本不受此规则影响。
- 这是原有技能行为，用于标识 skill 已正常调用，不得省略。

示例：

```text
已从文件提取 32 张卡片喵~
其中英译汉 20 张，名词解释 12 张喵~
HTML 已生成至 C:\output\生物化学-flashcards.html喵~
```

## 失败处理

- 文件不存在：报告缺失路径，列出相邻候选文件，不猜测。
- 提取为空：说明格式或文件问题，不生成空壳 HTML。
- JavaScript 验证失败：定位生成文件，修复模板或数据后重新验证。
- 用户要求覆盖已有文件：确认后使用生成器的 `--force`。
- 图片文字模糊：只提取可辨认内容并标记不确定项。
