# Little Busters! English Edition — Uncensored H-Scene Patch

给 Steam 版《Little Busters! English Edition》补回被删减的 H 剧情（中文台词 + 原版语音 + CG + 配乐 + 鉴赏图鉴）。

---

## 下载（当前稳定版 v1.5）

👉 **[Releases → v1.5](https://github.com/suixin0306-crypto/LBEE-Uncensored-Patch/releases/tag/v1.5)**

下载 `LBEE_Uncensored_Patch_v1.5.7z`（637MB）→ 解压 → 双击 **`安装.exe`**

前置条件：
- Steam 正版，游戏为**原版状态**（全新安装或 Steam 验证过文件完整性）
- 约 6GB 空闲磁盘
- 装过"无印版补丁"等改过 `LITBUS_WIN32.exe` 的，请先 Steam 验证还原

---

## ✅ 已解决的问题

1. **结局黑屏出现角色 HCG（严重）** — H 图只使用引擎背景加载真正支持的安全槽位（EVENTCG/BGCG）；OTHOCG/CHARCG 保持原版 → 结局 ED 图、文本记录(Log)、立绘、鉴赏零污染
2. **鉴赏模式集成 H CG**（v1.5）— 新增 47 格，看过自动解锁
3. **官方汉化升级 2026.10.01** — 修复 Log 卡死、物品栏缺字、翻译修正
4. **来ヶ谷（Kurugaya）线 H 段** — 316 行中文 + 105 条语音
5. **结局残留 HCG / 黑屏** — H 段结束恢复宿主画面
6. **部分中文缺字** — 生僻字替换
7. **佐々美线无法进入** — 修复 FARCALL 目标偏移
8. **H 段配乐**

## ❌ 已知限制

1. **H CG 为 47 张精选**（引擎安全槽位仅 55 个）
2. **H 段选项（SELECT）未移植** — 原版 H 内的选项（用嘴/用手等）目前线性播放
3. 旧存档不兼容（请用新存档）

## 🎯 后续目标

1. **H 段选项移植** — 解析 EX `SELECT` 生成 LBEE 分支
2. **恢复更多 CG** — 引擎加载链路已逆向（`notes/engine_image_refs.md`），探索更多安全槽位
3. 安装器/分发优化

---

## 版本历史

| 版本 | 内容 | 状态 |
|---|---|---|
| v1.5 | 鉴赏集成版（47 格 H CG 图鉴）| ✅ 当前稳定版 |
| v1.4 | 新汉化 2026.10.01 + 来ヶ谷线 + 安全槽位 | 建议升级 |
| v1.3 | 安全槽位版（旧汉化）| 建议升级 |
| v1.2 | 132 张完整 CG，但污染结局 ED 图与 Log 界面 | ⚠️ 已废弃 |

## 版权声明

- 官方中文汉化：Jack-Myth — [LBEE_TranslationPatch](https://github.com/Jack-Myth/LBEE_TranslationPatch)
- 游戏版权归 Key / VisualArts 所有；本补丁仅供个人学习交流，请支持正版，勿传播游戏本体