# Little Busters! English Edition — Uncensored H-Scene Patch

给 Steam 版《Little Busters! English Edition》补回被删减的 H 剧情（中文台词 + 原版语音 + CG + 配乐）。

---

## 下载（当前稳定版 v1.3）

👉 **[Releases → v1.3](https://github.com/suixin0306-crypto/LBEE-Uncensored-Patch/releases/tag/v1.3)**

下载 `LBEE_Uncensored_Patch_v1.3.7z`（628MB）→ 解压 → 双击 **`安装.exe`**

前置条件：
- Steam 正版，游戏为**原版状态**（全新安装或 Steam 验证过文件完整性）
- 约 6GB 空闲磁盘
- 装过"无印版补丁"等改过 `LITBUS_WIN32.exe` 的，请先 Steam 验证还原

---

## ✅ v1.3 已解决的问题

1. **结局黑屏出现角色 HCG（严重）** — 原先 H 图占用了引擎的 ED 结局插图槽位；v1.3 改用引擎安全槽位，结局/Log/立绘/鉴赏全部正常
2. **结局残留上一张 HCG** — H 段结束恢复宿主原画面
3. **部分中文缺字** — 替换 49 行生僻字 + 2 行俄语改中文
4. **佐々美线无法进入** — 修复 `SEEN0517` 的 FARCALL 目标偏移
5. **H 段配乐** — 每段 H 使用专属曲，结束自动恢复

## ❌ v1.3 已知限制

1. **H CG 为 55 张精选**（原版 132 张）— 引擎安全槽位限制，部分画面停留更久
2. **来ヶ谷线 H 段未包含**
3. **旧存档不兼容**（改脚本导致，请用新存档）
4. 鉴赏模式未集成 H CG

## 🎯 v1.4 目标

1. **恢复 132 张完整 CG** — 已定位方案：使用 OTHCG 中"仅日文模式使用"的 263 个安全条目（英文/中文模式下不会被引擎加载）
2. **新增来ヶ谷 #086 H 段** — 316 行中文（翻译中）+ 22 张图 + 105 条语音
3. 鉴赏模式集成
4. 安装器/分发优化

---

## 版本历史

| 版本 | 内容 | 状态 |
|---|---|---|
| v1.3 | 安全槽位版，55 张精选 CG，主线/结局/UI 全正常 | ✅ 当前稳定版 |
| v1.2 | 132 张完整 CG，但会污染结局 ED 图与 Log 界面 | ⚠️ 已废弃 |

## 版权声明

- 官方中文汉化：Jack-Myth — [LBEE_TranslationPatch](https://github.com/Jack-Myth/LBEE_TranslationPatch)
- 游戏版权归 Key / VisualArts 所有；本补丁仅供个人学习交流，请支持正版，勿传播游戏本体