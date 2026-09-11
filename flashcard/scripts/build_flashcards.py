#!/usr/bin/env python3
"""Build a standalone interactive HTML flashcard deck from JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="dark">
  <title>__TITLE__</title>
  <style>
    :root {
      --bg: #0b1120;
      --panel: #111c31;
      --panel-strong: #17233d;
      --card-bg: #17243e;
      --card-back: #1d3155;
      --text: #eef5ff;
      --muted: #9fb0ca;
      --accent: #69a8ff;
      --accent-strong: #3d82ee;
      --correct: #48d597;
      --wrong: #ff9d63;
      --warning: #f6c85f;
      --border: rgba(255, 255, 255, 0.12);
      --shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
    }
    * { box-sizing: border-box; }
    html, body { min-height: 100%; margin: 0; }
    body {
      min-height: 100vh;
      background:
        radial-gradient(circle at 50% -20%, rgba(74, 131, 231, 0.22), transparent 42%),
        var(--bg);
      color: var(--text);
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
      display: flex;
      justify-content: center;
    }
    button { font: inherit; }
    .app {
      width: min(1120px, 100%);
      padding: 24px;
      display: grid;
      gap: 18px;
    }
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
    }
    h1 { margin: 0 0 6px; font-size: clamp(1.4rem, 3vw, 2.1rem); }
    .subtitle { color: var(--muted); font-size: 0.92rem; }
    .pills { display: flex; flex-wrap: wrap; gap: 8px; }
    .pill {
      border: 1px solid var(--border);
      color: var(--muted);
      background: rgba(255, 255, 255, 0.03);
      padding: 9px 14px;
      border-radius: 999px;
      cursor: pointer;
    }
    .pill.active {
      color: #081221;
      background: var(--accent);
      border-color: var(--accent);
      font-weight: 700;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .stat {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 13px 16px;
    }
    .stat span { display: block; color: var(--muted); font-size: 0.8rem; }
    .stat strong { font-size: 1.45rem; }
    .progress-shell {
      height: 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      overflow: hidden;
    }
    .progress-bar {
      height: 100%;
      width: 0;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), var(--correct));
      transition: width 180ms ease;
    }
    .card-meta {
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 0.9rem;
    }
    .stage {
      perspective: 1200px;
      min-height: 350px;
    }
    .card {
      position: relative;
      width: 100%;
      min-height: 350px;
      border: 0;
      padding: 0;
      border-radius: 22px;
      background: transparent;
      color: inherit;
      cursor: pointer;
      outline: none;
    }
    .card:focus-visible .card-face { box-shadow: 0 0 0 3px var(--accent), var(--shadow); }
    .card-inner {
      position: absolute;
      inset: 0;
      transform-style: preserve-3d;
      transition: transform 380ms cubic-bezier(.2, .7, .2, 1);
    }
    .card.flipped .card-inner { transform: rotateY(180deg); }
    .card-face {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: clamp(26px, 5vw, 58px);
      border: 1px solid var(--border);
      border-radius: 22px;
      background: linear-gradient(145deg, var(--card-bg), var(--panel-strong));
      box-shadow: var(--shadow);
      backface-visibility: hidden;
      overflow: auto;
    }
    .card-back {
      background: linear-gradient(145deg, var(--card-back), #17233b);
      transform: rotateY(180deg);
    }
    .card-text {
      width: 100%;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      line-height: 1.65;
    }
    .card-front .card-text { font-size: clamp(1.55rem, 4vw, 2.45rem); font-weight: 800; }
    .card-back .card-text { font-size: clamp(1.02rem, 2.2vw, 1.3rem); line-height: 1.8; }
    .card-label {
      position: absolute;
      top: 16px;
      left: 18px;
      color: var(--muted);
      font-size: 0.76rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .actions, .tools {
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 10px;
    }
    .btn {
      min-height: 44px;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 17px;
      background: var(--panel);
      color: var(--text);
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease, border-color 120ms ease;
    }
    .btn:hover:not(:disabled) { transform: translateY(-1px); border-color: var(--accent); }
    .btn:disabled { opacity: 0.42; cursor: not-allowed; }
    .btn.primary { background: var(--accent-strong); border-color: var(--accent-strong); font-weight: 700; }
    .btn.correct { border-color: rgba(72, 213, 151, 0.6); }
    .btn.wrong { border-color: rgba(255, 157, 99, 0.6); }
    .completion {
      display: none;
      text-align: center;
      padding: 58px 24px;
      background: rgba(72, 213, 151, 0.08);
      border: 1px solid rgba(72, 213, 151, 0.32);
      border-radius: 18px;
    }
    .completion.visible { display: block; }
    .completion h2 { margin: 0 0 8px; }
    .completion p { margin: 0; color: var(--muted); }
    .modal {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      background: rgba(2, 7, 18, 0.74);
      z-index: 20;
    }
    .modal.open { display: flex; }
    .modal-panel {
      width: min(920px, 100%);
      max-height: min(82vh, 760px);
      display: grid;
      grid-template-rows: auto auto minmax(0, 1fr);
      gap: 14px;
      padding: 20px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }
    .modal-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
    .modal-head h2 { margin: 0; font-size: 1.25rem; }
    .search {
      width: 100%;
      min-height: 44px;
      border: 1px solid var(--border);
      border-radius: 11px;
      padding: 10px 13px;
      color: var(--text);
      background: #0d1729;
      outline: none;
    }
    .search:focus { border-color: var(--accent); }
    .word-list { overflow: auto; border-top: 1px solid var(--border); }
    .word-row {
      display: grid;
      grid-template-columns: 48px minmax(140px, 0.7fr) minmax(220px, 1.3fr);
      gap: 12px;
      padding: 12px 4px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    }
    .word-row.mastered { opacity: 0.56; background: rgba(72, 213, 151, 0.04); }
    .word-state { font-size: 0.78rem; color: var(--muted); }
    .word-front { font-weight: 700; overflow-wrap: anywhere; }
    .word-back { color: #c8d7eb; white-space: pre-wrap; overflow-wrap: anywhere; }
    .empty { padding: 34px 10px; text-align: center; color: var(--muted); }
    .toast {
      position: fixed;
      left: 50%;
      bottom: 22px;
      transform: translateX(-50%) translateY(18px);
      opacity: 0;
      pointer-events: none;
      padding: 10px 16px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #14213a;
      transition: opacity 160ms ease, transform 160ms ease;
      z-index: 30;
    }
    .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
    @media (max-width: 720px) {
      .app { padding: 15px; gap: 14px; }
      .topbar { display: block; }
      .pills { margin-top: 14px; }
      .stats { gap: 8px; }
      .stat { padding: 10px; }
      .stat strong { font-size: 1.15rem; }
      .stage, .card { min-height: 390px; }
      .word-row { grid-template-columns: 42px 1fr; }
      .word-back { grid-column: 2; }
      .actions .btn { flex: 1 1 42%; }
      .tools .btn { flex: 1 1 42%; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
    }
  </style>
</head>
<body>
  <main class="app">
    <header class="topbar">
      <div>
        <h1 id="deck-title">__TITLE__</h1>
        <div class="subtitle">Space / Enter 翻转 · ← 忘了 · → 记得 · ↑ 上一张</div>
      </div>
      <div class="pills" id="section-pills" aria-label="分类"></div>
    </header>

    <section class="stats" aria-label="学习统计">
      <div class="stat"><span>剩余</span><strong id="stat-remaining">0</strong></div>
      <div class="stat"><span>已掌握</span><strong id="stat-mastered">0</strong></div>
      <div class="stat"><span>待复习</span><strong id="stat-review">0</strong></div>
    </section>
    <div class="progress-shell" aria-hidden="true"><div class="progress-bar" id="progress-bar"></div></div>

    <div class="card-meta">
      <span id="section-name">全部</span>
      <span id="card-index">第 0 / 0 张</span>
    </div>

    <section class="stage">
      <button class="card" id="flashcard" type="button" aria-label="翻转卡片">
        <div class="card-inner">
          <div class="card-face card-front">
            <span class="card-label">正面</span>
            <div class="card-text" id="card-front"></div>
          </div>
          <div class="card-face card-back">
            <span class="card-label">背面</span>
            <div class="card-text" id="card-back"></div>
          </div>
        </div>
      </button>
      <div class="completion" id="completion">
        <h2>全部复习完毕</h2>
        <p>当前分类中的卡片均已掌握</p>
      </div>
    </section>

    <div class="actions">
      <button class="btn" id="previous-btn" type="button">↑ 上一张</button>
      <button class="btn wrong" id="forgot-btn" type="button">😕 忘了</button>
      <button class="btn primary" id="flip-btn" type="button">🔄 翻转</button>
      <button class="btn correct" id="known-btn" type="button">✅ 记得</button>
    </div>
    <div class="tools">
      <button class="btn" id="shuffle-btn" type="button">🔀 打乱重来</button>
      <button class="btn" id="review-btn" type="button">📝 复习遗忘词</button>
      <button class="btn" id="glossary-btn" type="button">📋 词汇表</button>
      <button class="btn" id="reset-btn" type="button">🔄 全部重置</button>
    </div>
  </main>

  <div class="modal" id="glossary-modal" role="dialog" aria-modal="true" aria-labelledby="glossary-title">
    <div class="modal-panel">
      <div class="modal-head">
        <h2 id="glossary-title">词汇表</h2>
        <button class="btn" id="close-modal-btn" type="button">关闭</button>
      </div>
      <input id="word-search" class="search" type="search" placeholder="🔍 搜索词汇..." autocomplete="off">
      <div class="word-list" id="word-list"></div>
    </div>
  </div>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>

  <script id="flashcard-data" type="application/json">__DATA__</script>
  <script>
    (() => {
      const data = JSON.parse(document.getElementById("flashcard-data").textContent);
      const cards = data.cards;
      const sectionLabels = { "en-cn": "英译汉", "cn-def": "名词解释", "默认": "默认" };
      const elements = {
        title: document.getElementById("deck-title"),
        pills: document.getElementById("section-pills"),
        remaining: document.getElementById("stat-remaining"),
        mastered: document.getElementById("stat-mastered"),
        review: document.getElementById("stat-review"),
        progress: document.getElementById("progress-bar"),
        sectionName: document.getElementById("section-name"),
        index: document.getElementById("card-index"),
        card: document.getElementById("flashcard"),
        front: document.getElementById("card-front"),
        back: document.getElementById("card-back"),
        completion: document.getElementById("completion"),
        previous: document.getElementById("previous-btn"),
        forgot: document.getElementById("forgot-btn"),
        flip: document.getElementById("flip-btn"),
        known: document.getElementById("known-btn"),
        shuffle: document.getElementById("shuffle-btn"),
        reviewButton: document.getElementById("review-btn"),
        glossary: document.getElementById("glossary-btn"),
        reset: document.getElementById("reset-btn"),
        modal: document.getElementById("glossary-modal"),
        closeModal: document.getElementById("close-modal-btn"),
        search: document.getElementById("word-search"),
        wordList: document.getElementById("word-list"),
        toast: document.getElementById("toast")
      };

      const sections = ["all", ...new Set(cards.map((card) => card.section || "默认"))];
      const state = {
        filter: "all",
        queue: [],
        current: null,
        mastered: new Set(),
        review: new Set(),
        history: [],
        flipped: false,
        complete: false
      };

      const labelFor = (section) => section === "all" ? "全部" : (sectionLabels[section] || section);
      const indicesFor = (filter = state.filter) => cards
        .map((_, index) => index)
        .filter((index) => filter === "all" || (cards[index].section || "默认") === filter);
      const shuffle = (items) => {
        const result = [...items];
        for (let index = result.length - 1; index > 0; index -= 1) {
          const swapIndex = Math.floor(Math.random() * (index + 1));
          [result[index], result[swapIndex]] = [result[swapIndex], result[index]];
        }
        return result;
      };
      const snapshot = () => ({
        filter: state.filter,
        queue: [...state.queue],
        current: state.current,
        mastered: [...state.mastered],
        review: [...state.review],
        flipped: state.flipped,
        complete: state.complete
      });
      const restore = (saved) => {
        state.filter = saved.filter;
        state.queue = [...saved.queue];
        state.current = saved.current;
        state.mastered = new Set(saved.mastered);
        state.review = new Set(saved.review);
        state.flipped = saved.flipped;
        state.complete = saved.complete;
        render();
      };
      const pushHistory = () => {
        state.history.push(snapshot());
        if (state.history.length > 100) state.history.shift();
      };
      const activeQueue = () => {
        const active = indicesFor();
        const pending = active.filter((index) => !state.mastered.has(index));
        if (pending.length) return shuffle(pending);
        const forgotten = active.filter((index) => state.review.has(index));
        return shuffle(forgotten);
      };
      const startSession = (filter = state.filter, clearProgress = false) => {
        state.filter = filter;
        if (clearProgress) {
          state.mastered = new Set();
          state.review = new Set();
          state.history = [];
        }
        state.queue = activeQueue();
        state.current = state.queue.length ? state.queue.shift() : null;
        state.flipped = false;
        state.complete = state.current === null;
        render();
      };
      const nextCard = () => {
        if (state.queue.length) {
          state.current = state.queue.shift();
        } else {
          const active = indicesFor().filter((index) => state.review.has(index) && !state.mastered.has(index));
          state.queue = shuffle(active);
          state.current = state.queue.length ? state.queue.shift() : null;
        }
        state.flipped = false;
        state.complete = state.current === null;
        render();
      };
      const mark = (known) => {
        if (state.current === null) return;
        pushHistory();
        const index = state.current;
        if (known) {
          state.mastered.add(index);
          state.review.delete(index);
        } else {
          state.review.add(index);
          state.mastered.delete(index);
          state.queue.push(index);
        }
        nextCard();
      };
      const flip = () => {
        if (state.current === null) return;
        state.flipped = !state.flipped;
        render();
      };
      const undo = () => {
        const saved = state.history.pop();
        if (!saved) return;
        restore(saved);
      };
      const statusFor = (index) => state.mastered.has(index) ? "mastered" : (state.review.has(index) ? "review" : "new");
      const statusLabel = (status) => ({ mastered: "已掌握", review: "待复习", new: "未学习" })[status];

      const makeButton = (label, active, onClick) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "pill" + (active ? " active" : "");
        button.textContent = label;
        button.addEventListener("click", onClick);
        return button;
      };
      const renderPills = () => {
        elements.pills.replaceChildren(...sections.map((section) => makeButton(
          labelFor(section),
          state.filter === section,
          () => startSession(section, false)
        )));
      };
      const renderGlossary = () => {
        const query = elements.search.value.trim().toLocaleLowerCase();
        const visible = indicesFor().filter((index) => {
          const card = cards[index];
          return !query || card.front.toLocaleLowerCase().includes(query) || card.back.toLocaleLowerCase().includes(query);
        });
        if (!visible.length) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = "没有匹配的卡片";
          elements.wordList.replaceChildren(empty);
          return;
        }
        const rows = visible.map((index) => {
          const card = cards[index];
          const row = document.createElement("div");
          const status = statusFor(index);
          row.className = "word-row" + (status === "mastered" ? " mastered" : "");
          const statusNode = document.createElement("div");
          statusNode.className = "word-state";
          statusNode.textContent = statusLabel(status);
          const frontNode = document.createElement("div");
          frontNode.className = "word-front";
          frontNode.textContent = card.front;
          const backNode = document.createElement("div");
          backNode.className = "word-back";
          backNode.textContent = card.back;
          row.append(statusNode, frontNode, backNode);
          return row;
        });
        elements.wordList.replaceChildren(...rows);
      };
      const showToast = (message) => {
        elements.toast.textContent = message;
        elements.toast.classList.add("show");
        window.clearTimeout(showToast.timer);
        showToast.timer = window.setTimeout(() => elements.toast.classList.remove("show"), 1800);
      };
      const render = () => {
        const active = indicesFor();
        const masteredCount = active.filter((index) => state.mastered.has(index)).length;
        const reviewCount = active.filter((index) => state.review.has(index)).length;
        const total = active.length;
        const remaining = Math.max(0, total - masteredCount);
        const progress = total ? Math.round((masteredCount / total) * 100) : 100;

        elements.remaining.textContent = String(remaining);
        elements.mastered.textContent = String(masteredCount);
        elements.review.textContent = String(reviewCount);
        elements.progress.style.width = progress + "%";
        elements.sectionName.textContent = labelFor(state.filter);
        elements.index.textContent = state.current === null
          ? `第 ${total} / ${total} 张`
          : `第 ${Math.min(masteredCount + 1, total)} / ${total} 张`;
        elements.completion.classList.toggle("visible", state.complete);
        elements.card.style.display = state.complete ? "none" : "block";
        elements.card.classList.toggle("flipped", state.flipped);
        elements.previous.disabled = state.history.length === 0;
        const disabled = state.current === null;
        elements.forgot.disabled = disabled;
        elements.flip.disabled = disabled;
        elements.known.disabled = disabled;

        if (state.current === null) {
          elements.front.textContent = "";
          elements.back.textContent = "";
        } else {
          const card = cards[state.current];
          elements.front.textContent = card.front;
          elements.back.textContent = card.back;
        }
        renderPills();
        if (elements.modal.classList.contains("open")) renderGlossary();
      };

      elements.card.addEventListener("click", flip);
      elements.flip.addEventListener("click", flip);
      elements.forgot.addEventListener("click", () => mark(false));
      elements.known.addEventListener("click", () => mark(true));
      elements.previous.addEventListener("click", undo);
      elements.shuffle.addEventListener("click", () => {
        state.queue = shuffle(indicesFor().filter((index) => !state.mastered.has(index)));
        state.current = state.queue.length ? state.queue.shift() : null;
        state.flipped = false;
        state.complete = state.current === null;
        render();
      });
      elements.reviewButton.addEventListener("click", () => {
        const forgotten = indicesFor().filter((index) => state.review.has(index) && !state.mastered.has(index));
        if (!forgotten.length) {
          showToast("当前没有待复习卡片");
          return;
        }
        state.queue = shuffle(forgotten);
        state.current = state.queue.shift();
        state.flipped = false;
        state.complete = false;
        render();
      });
      elements.reset.addEventListener("click", () => {
        startSession(state.filter, true);
        showToast("已重置全部进度");
      });
      elements.glossary.addEventListener("click", () => {
        elements.modal.classList.add("open");
        elements.search.value = "";
        renderGlossary();
        elements.search.focus();
      });
      elements.closeModal.addEventListener("click", () => elements.modal.classList.remove("open"));
      elements.modal.addEventListener("click", (event) => {
        if (event.target === elements.modal) elements.modal.classList.remove("open");
      });
      elements.search.addEventListener("input", renderGlossary);
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && elements.modal.classList.contains("open")) {
          elements.modal.classList.remove("open");
          return;
        }
        if (document.activeElement === elements.search) return;
        if (event.key === " " || event.key === "Enter") {
          event.preventDefault();
          flip();
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          mark(false);
        } else if (event.key === "ArrowRight") {
          event.preventDefault();
          mark(true);
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          undo();
        } else if (event.key.toLowerCase() === "r") {
          startSession(state.filter, true);
        } else if (event.key.toLowerCase() === "f") {
          elements.reviewButton.click();
        }
      });

      elements.title.textContent = data.title;
      document.title = data.title;
      startSession("all", false);
    })();
  </script>
</body>
</html>
"""


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_cards(path: Path, title_override: str | None) -> tuple[str, list[dict[str, str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        raw_cards = payload
        title = title_override or "复习卡片"
    elif isinstance(payload, dict):
        raw_cards = payload.get("cards", [])
        title = title_override or clean_text(payload.get("title")) or "复习卡片"
    else:
        raise ValueError("JSON root must be an array or an object containing cards")

    if not isinstance(raw_cards, list):
        raise ValueError("cards must be an array")

    cards: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for position, raw in enumerate(raw_cards, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"card {position} must be an object")
        front = clean_text(raw.get("front"))
        back = clean_text(raw.get("back"))
        section = clean_text(raw.get("section")) or "默认"
        if not front or not back:
            continue
        key = (re.sub(r"\s+", " ", front).casefold(), re.sub(r"\s+", " ", back).casefold())
        if key in seen:
            continue
        seen.add(key)
        cards.append({"front": front, "back": back, "section": section})

    if not cards:
        raise ValueError("no valid cards found")
    return title, cards


def safe_json_for_script(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def build(input_path: Path, output_path: Path, title_override: str | None, force: bool) -> dict[str, Any]:
    title, cards = load_cards(input_path, title_override)
    if output_path.exists() and not force:
        raise FileExistsError(f"output already exists: {output_path}; use --force to overwrite")

    payload = {"title": title, "cards": cards}
    document = (
        HTML_TEMPLATE
        .replace("__TITLE__", html.escape(title, quote=True))
        .replace("__DATA__", safe_json_for_script(payload))
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return {"output": str(output_path), "title": title, "cards": len(cards), "sections": sorted({card["section"] for card in cards})}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a standalone HTML flashcard deck from JSON.")
    parser.add_argument("--input", required=True, type=Path, help="JSON file containing cards")
    parser.add_argument("--output", required=True, type=Path, help="HTML output path")
    parser.add_argument("--title", help="Optional deck title")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = build(args.input, args.output, args.title, args.force)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
