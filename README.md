# NeonLingo 本地增强版

基于中文分词 + 本地分级词库的 Chrome / Edge 浏览器插件。将中文网页中符合用户 CEFR 等级的词汇替换为英文，鼠标悬浮可查看中文原文。

## 功能

- 中文网页自动分词（`Intl.Segmenter`，Chrome/Edge 原生支持）
- 本地分级词库（中文 → 英文 + CEFR 等级 A1~C1）
- 按用户等级过滤，仅替换「英文等级 ≤ 用户等级」的词汇
- 替换词带橙色虚线下划线，悬停显示中文原文（`title` 属性）
- 弹窗：等级选择、启用/禁用、本页替换统计
- 可视区域懒处理（Intersection Observer）+ 动态内容监听（MutationObserver）

## 安装（开发者模式）

1. 打开 Chrome / Edge，进入扩展管理页  
   - Chrome: `chrome://extensions`  
   - Edge: `edge://extensions`
2. 开启「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择本仓库中的 `extension` 目录

## 使用

1. 点击工具栏 NeonLingo 图标打开弹窗
2. 选择你的英语等级（默认 B1）
3. 浏览任意中文网页，符合条件的词会自动替换为英文
4. 鼠标悬停在带下划线的英文上，查看中文原文

## 目录结构

```
extension/
├── manifest.json          # 插件清单 (Manifest V3)
├── background.js          # 词库预加载、存储与消息路由
├── content.js             # DOM 遍历、分词、查词、替换
├── popup.html / .js / .css
├── injected.css           # 页面内替换样式
├── dict/
│   └── graded_dict.json   # 分级词库（示例约 300+ 词条）
└── scripts/
    └── merge_dict.py      # 从 CC-CEDICT + Oxford 5000 生成完整词库
```

## 构建完整词库

1. 下载 Oxford 5000 CEFR 等级表：

```bash
python extension/scripts/download_oxford.py
```

2. 下载 CC-CEDICT：

```bash
python extension/scripts/download_cedict.py
```

3. 合并生成 `graded_dict.json`：

```bash
python extension/scripts/merge_dict.py
```

输出文件：`extension/dict/graded_dict.json`（约 12 万词条，~9 MB）

数据来源：
- CC-CEDICT（[MDBG](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)，CC BY-SA 4.0）
- Oxford 5000（[nalgeon/words](https://github.com/nalgeon/words)）

## 测试示例

在任意网页控制台或本地 HTML 中放入：

```html
<p>这是一个苹果，非常重要。政府正在投资新技术。</p>
```

等级 B1 时预期：`apple`、`important` 被替换；`投资`(B2)、`政府`(B1) 等按等级规则处理。

## 技术说明

| 模块 | 说明 |
|------|------|
| 分词 | `Intl.Segmenter('zh-CN', { granularity: 'word' })` |
| 词库 | 内存 JSON 对象，O(1) 精确匹配 |
| 等级 | A1(1) < A2(2) < B1(3) < B2(4) < C1(5) |
| 存储 | `chrome.storage.local`（userLevel, isEnabled） |

## 许可证

词库数据来源：CC-CEDICT（开源）、Oxford 5000（请遵循其使用条款）。
