# Little Busters! English Edition — Uncensored H-Scene Patch v1.2

给 Steam 版《Little Busters! English Edition》补回被删减的 H 剧情（中文台词 + 原版语音 + 原版 CG）。

Restores the cut H-scenes of *Little Busters! English Edition* (Steam, all-ages) using the official Chinese fan translation for dialogue, original Japanese voices and original CG art.

> **本仓库只存放说明与发布信息。补丁本体（约 3.9GB）在 [Releases](../../releases) 里分卷下载。**

---

## 特性 / Features

- **10 段 H 剧情，原位插回剧情**（不是塞进菜单）— 10 H-scenes inserted at their original story positions
- **中文台词**（基于官方汉化译文，显示在英文栏；切日文可看原文）— Chinese dialogue via the official fan translation
- **原版日文语音 1,324 条** — 1,324 original Japanese voice clips
- **原版 H CG**（从 EX 素材合成，含立绘叠背景）— original H CG rebuilt from EX assets
- **H 段专属 BGM**（Two Sugars），结束后自动恢复 — dedicated H-scene BGM, auto-restored
- **一键安装器**：自动装官方中文汉化 + 本补丁 — one-click installer, sets up the Chinese localization too

涉及角色 / Routes：

| 角色 | 段 |
|---|---|
| 葉留佳 Haruka | #068 |
| 鈴 Rin | #044 |
| 佐々美 Sasami | #024 |
| 美魚 Mio | #091（前后两段）|
| 小毬 Komari | #019 |
| クド Kud | #075（强制线）/#078 |
| 沙耶 Saya | #047 |
| 佳奈多 Kanata | #070 |

---

## 下载与安装 / Download & Install

**1. 下载 / Download**

到 [Releases](../../releases) 下载全部 4 个分卷：

```
LBEE_Uncensored_Patch_v1.2.7z.001
LBEE_Uncensored_Patch_v1.2.7z.002
LBEE_Uncensored_Patch_v1.2.7z.003
LBEE_Uncensored_Patch_v1.2.7z.004
```

**2. 合并 / Merge**

把 4 个文件放在**同一个文件夹**里，双击 `合并.bat`（或在本目录打开命令行执行）：

```bat
copy /b LBEE_Uncensored_Patch_v1.2.7z.001 + LBEE_Uncensored_Patch_v1.2.7z.002 + LBEE_Uncensored_Patch_v1.2.7z.003 + LBEE_Uncensored_Patch_v1.2.7z.004 LBEE_Uncensored_Patch_v1.2.7z
```

得到 `LBEE_Uncensored_Patch_v1.2.7z`（4,154,465,990 字节，SHA256 见 `SHA256SUMS.txt`）。

**3. 解压 / Extract**

用 7-Zip / WinRAR / Bandizip 解压，得到 `LBEE_中文H内容补丁` 文件夹。

**4. 安装 / Install**

关闭游戏 → 双击文件夹里的 **`安装.exe`** → 按提示确认游戏目录 → 等待完成。

安装器会自动：

1. 检测/安装官方中文汉化（字体、界面、`dsound.dll` 钩子）
2. 首次安装时备份原文件到 `files\LBEE_ZH_H_backup`
3. 复制 H 内容文件（约 4.5 GB）

---

## 前置条件 / Requirements

- Steam 正版《Little Busters! English Edition》
- 游戏为**原版状态**（全新安装，或 Steam 验证过文件完整性）
- 约 **10 GB** 空闲磁盘（安装 4.5GB + 备份 4.5GB）

> ⚠ 如果之前装过"无印版补丁"等**修改过 `LITBUS_WIN32.exe`** 的东西，请先
> Steam → 属性 → 已安装文件 → **验证文件完整性** 还原。
> 改过的 exe 会和中文汉化的 `dsound.dll` 钩子冲突，导致**黑屏**。

---

## 卸载 / Uninstall

双击 `卸载.exe` 从备份还原；彻底回原版用 Steam 验证文件完整性。

---

## 已知说明 / Known Notes (not bugs)

- 部分 H 段本来就没有配音（原作设计）— some scenes have no voice acting by design
- 佳奈多线结尾有原作本身的黑屏段落 — Kanata's route has original black-screen passages
- 改动脚本可能让**旧存档**读取异常，请用新存档 — use a new save; modified scripts may break old saves

---

## FAQ

**Q: 进游戏黑屏/卡死？**
检查 `LITBUS_WIN32.exe` 是否为 Steam 原版（5,208,944 字节）；装过改 exe 的补丁请先 Steam 验证。

**Q: 中文缺字/方块？**
官方汉化没装成功。运行补丁文件夹里的 `run_patch.cmd` 手动装一次汉化，再重新运行 `安装.exe`。

**Q: 合并出来的文件报错/解压失败？**
对比 `SHA256SUMS.txt` 里的 SHA256，确认 4 个分卷都下载完整、且合并顺序正确。

---

## 致谢与声明 / Credits & Disclaimer

- 官方中文汉化：**Jack-Myth** — [LBEE_TranslationPatch](https://github.com/Jack-Myth/LBEE_TranslationPatch)
- 本补丁在官方汉化基础上移植 H 内容，**仅供个人学习交流使用，请勿用于商业用途**；
- 游戏本体及全部素材版权归 **Key / VisualArts** 所有，请支持正版；
- 本仓库不包含游戏本体。如相关权利方有异议，请联系删除。
