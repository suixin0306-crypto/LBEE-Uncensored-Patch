#!/usr/bin/env bash
# LBEE 内容还原补丁 v1.7.4 · Steam Deck / Linux 启动壳
# 用法: ./安装.sh [--check|--uninstall|--extract-only DIR|--dry-run|--game PATH]
set -euo pipefail
cd "$(dirname "$0")"

# 优先用 python3；没有就退回 python（SteamOS 自带 python3）
PY=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    echo "错误：没有找到 python3（需要 Python 3.8 或更新版本）。" >&2
    echo "SteamOS 自带 python3；其它 Linux 发行版请先安装：" >&2
    echo "  Debian/Ubuntu: sudo apt install python3" >&2
    echo "  Arch/SteamOS:  sudo pacman -S python" >&2
    exit 1
fi

exec "$PY" lbee_deck_install.py "$@"
