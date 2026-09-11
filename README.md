# Codex Skills

个人 Codex 技能集合，目录结构仿照 [claude-skills](https://github.com/Celineqwq/claude-skills)。

## 技能列表

### Flashcard 闪卡

从 TXT、DOCX、PPTX、PDF、图片或粘贴文本中提取知识，生成可离线打开的交互式 HTML 闪卡。

- 支持英译汉、名词解释和混合模式
- 保留暗色主题、键盘快捷键、队列复习、随机洗牌和历史回溯
- 支持词汇表搜索、背诵状态、遗忘词重练和全部重置
- 新增确定性生成器与 HTML/JavaScript 验证脚本
- 输出：`{主题}-flashcards.html`
- 面向用户的说明输出保留“喵”风格和句号替换规则

## 安装

```powershell
git clone https://github.com/Celineqwq/codex-skill.git
Copy-Item -Recurse .\codex-skill\flashcard "$env:USERPROFILE\.codex\skills\"
```

也可以只复制 `flashcard/` 到 `%USERPROFILE%\.codex\skills\`。

## 目录结构

```text
codex-skill/
├── README.md
└── flashcard/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── references/
    │   ├── input-parsing.md
    │   └── html-runtime.md
    ├── scripts/
    │   ├── build_flashcards.py
    │   └── validate_flashcards.py
    └── examples/
        └── *.html
```

## 验证

```powershell
python flashcard\scripts\build_flashcards.py --input cards.json --output deck.html
python flashcard\scripts\validate_flashcards.py deck.html
```
