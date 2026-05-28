# Chrome 网上应用店 — 上架素材

## 隐私政策 URL

启用 GitHub Pages 后，可使用：

```
https://code-corey.github.io/EnglishViewLearner/privacy.html
```

或在仓库 Settings → Pages 中，将 `/docs` 目录发布为站点，则 URL 为：

```
https://code-corey.github.io/EnglishViewLearner/privacy.html
```

（将 `docs/privacy.html` 复制为 `docs/index.html` 亦可，按需调整。）

本地预览：打开 `docs/privacy.html`

---

## 商店文案（可直接复制）

### 名称
沉浸式学习英语

### 简短说明（≤132 字）
按 CEFR 等级将中文网页词汇替换为英文，本地词库离线可用，悬停查看中文原文。

### 详细说明
沉浸式学习英语是一款帮助英语学习者在浏览中文网页时自然接触英文词汇的 Chrome 扩展。

**主要功能：**
- 自动识别中文网页中的词语，按 Oxford CEFR 等级（A1～C1）替换为英文
- 默认替换当前等级及以下词汇；可开启「仅当前等级」模式
- 内置本地分级词库，核心功能完全离线
- 鼠标悬停已替换单词，查看中文原文
- 右侧悬浮小球快速切换开关与等级
- 可自定义下划线颜色

**适合人群：**
正在学习 A1～C1 词汇、希望在日常阅读中巩固英语的学习者。

**隐私：**
不收集个人数据；设置保存在浏览器本地；网页内容不上传服务器。

**词库来源：**
CC-CEDICT（CC BY-SA 4.0）、Oxford 5000 词表。

**开源：**
https://github.com/code-corey/EnglishViewLearner

### 分类
教育 / Education

### 权限说明（填写审核表单时用）
- `storage`：保存用户等级、开关状态、颜色偏好
- `activeTab`：读取当前页替换统计
- 内容脚本注入所有网页：需在用户访问的中文页面本地分词并替换文本；无数据外传

---

## 截图

1. 打开 `extension/store/screenshot-template.html`（浏览器全屏或调整窗口）
2. 使用 1280×800 截图工具截取
3. 另可截取真实网页替换效果（含下划线英文 + 悬停提示）

建议上传 3 张：
1. 弹窗设置界面
2. 网页替换效果
3. 悬浮小球抽屉

---

## 打包上传

```powershell
.\scripts\package-store.ps1
```

生成 `dist/immersive-english-v1.0.0.zip`，上传到
[Chrome 开发者控制台](https://chrome.google.com/webstore/devconsole)。
