# Steam Deck / Linux 安装器（分支：steam-deck）

> ⚠️ **这个分支只给 Steam Deck 用。**
> Windows 用户请回 [main 分支](https://github.com/suixin0306-crypto/LBEE-Uncensored-Patch) 下载 `LBEE_Uncensored_Patch_v1.7.4_setup.exe` 双击安装，**不需要**这里的东西。

## 解决什么问题

原版 `setup.exe` 是「C# 外壳 + 内嵌 ZIP」，外壳解开后调用 `安装.exe` → `powershell.exe -File install.ps1`。
Steam Deck 的 Proton 兼容层（俗称模拟器）不自带 PowerShell，内层脚本一行都没执行，
外壳最后校验 `SCRIPT.PAK` 哈希失败，于是弹「安装未完成（校验未通过）」。

这个分支用纯 Python 重做了安装流程，在 SteamOS 自带的 python3 上直接跑，不经过 Wine / Proton。

## 用法

1. 下载本分支：Code → Download ZIP（或 clone 后 `git checkout steam-deck`）
2. 解压，得到 `lbee_deck_install.py` 和 `安装.sh`
3. 把它们和 `LBEE_Uncensored_Patch_v1.7.4_setup.exe` 放在同一目录
4. 桌面模式打开 Konsole：

```bash
cd ~/Downloads
python3 lbee_deck_install.py --check    # 先确认能识别到游戏目录
python3 lbee_deck_install.py            # 开始安装
```

5. Steam → 属性 → 启动选项，填入：

```
WINEDLLOVERRIDES="dsound=n,b" %command%
```

6. 用**新存档**进游戏。

## 已验证

- 4GB `VOICE0.PAK` 合并结果与官方 `LBEE_VoiceMerge4.exe` **逐字节一致**（SHA256 相同）
- 解包 `setup.exe` 内置 487 个文件 / 1.75GB，约 6 秒
- 在已打补丁的目录重跑：自检 4 项全 OK、文件哈希不变（幂等）

## 已知限制

- 仅 SteamOS / Linux；Windows 请用 main 分支的 `setup.exe`
- Steam「验证文件完整性」会回滚本补丁
- 旧存档不兼容，必须新开档
- 目前只在 Windows 上做过等价性验证，**尚未在真机 Steam Deck 上完整回归**；遇到问题请带上 `--check` 的输出反馈

## 版权

游戏版权归 Key / VisualArts；中文汉化由 Jack-Myth 制作；补丁作者 Oya4me，反馈 QQ 群 1136805764。
