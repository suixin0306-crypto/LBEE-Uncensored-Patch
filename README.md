# Little Busters! English Edition — Uncensored H-Scene Patch

给 Steam 版《Little Busters! English Edition》补回被删减的 H 剧情（中文台词 + 原版语音 + CG + 配乐）。

---

## 下载（当前稳定版 v1.4）

👉 **[Releases → v1.4](https://github.com/suixin0306-crypto/LBEE-Uncensored-Patch/releases/tag/v1.4)**

下载 `LBEE_Uncensored_Patch_v1.4.7z`（629MB）→ 解压 → 双击 **`安装.exe`**

前置条件：
- Steam 正版，游戏为**原版状态**（全新安装或 Steam 验证过文件完整性）
- 约 6GB 空闲磁盘
- 装过"无印版补丁"等改过 `LITBUS_WIN32.exe` 的，请先 Steam 验证还原

---

## ✅ v1.4 已解决的问题

1. **结局黑屏出现角色 HCG（严重）** — H 图改用引擎背景加载真正支持的包（EVENTCG/BGCG）的**安全槽位**；OTHOCG/CHARCG 保持原版 → 结局 ED 图、文本记录(Log)、立绘、鉴赏零污染
2. **官方汉化升级 2026.10.01** — 修复 Log 卡死、物品栏缺字、部分翻译
3. **新增来ヶ谷（Kurugaya）线 H 段 #086** — 316 行中文新译 + 105 条语音
4. **结局残留 HCG / 黑屏** — H 段结束恢复宿主画面
5. **部分中文缺字** — 生僻字替换
6. **佐々美线无法进入** — 修复 `SEEN0517` FARCALL 目标偏移
7. **H 段配乐** — 专属曲，结束自动恢复

## ❌ v1.4 已知限制

1. **H CG 为 47 张精选**（11 段分配）— 引擎安全槽位仅 55 个
2. **H 段选项未移植** — 原版 H 内的选项（用嘴/用手等）目前线性播放
3. **鉴赏模式未集成 H CG**
4. 旧存档不兼容（改脚本导致，请用新存档）

## 🎯 v1.5 目标

1. **鉴赏模式集成 H CG** — 已逆向完成：`_CGMODE`（SCRIPT.PAK #162）、缩略图（SYSCG2 可追加）、解锁位图（data000.dat 0x4B，看 CG 自动解锁）
2. **H 段选项移植** — 解析 EX `SELECT` 生成 LBEE 分支
3. **更多 CG 槽位** — 引擎加载链路已逆向（`notes/engine_image_refs.md`）

---

## 版本历史

| 版本 | 内容 | 状态 |
|---|---|---|
| v1.4 | 新汉化 2026.10.01 + 来ヶ谷线 + 安全槽位（47 精选 CG）| ✅ 当前稳定版 |
| v1.3 | 安全槽位版（55 精选 CG，旧汉化 2025.05.10）| 可用，建议升级 |
| v1.2 | 132 张完整 CG，但污染结局 ED 图与 Log 界面 | ⚠️ 已废弃 |

## 版权声明

- 官方中文汉化：Jack-Myth — [LBEE_TranslationPatch](https://github.com/Jack-Myth/LBEE_TranslationPatch)
- 游戏版权归 Key / VisualArts 所有；本补丁仅供个人学习交流，请支持正版，勿传播游戏本体