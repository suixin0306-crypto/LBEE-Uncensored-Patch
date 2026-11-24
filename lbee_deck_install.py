#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LBEE 内容还原补丁 —— Steam Deck / Linux 原生安装器
=================================================

给 Steam 版《Little Busters! English Edition》安装 LBEE_Uncensored_Patch（汉化 + H 内容
+ 语音合并）。全程不依赖 Wine / Proton / PowerShell：SteamOS 自带 python3 即可运行。

用法（桌面模式 Konsole）：

    python3 lbee_deck_install.py                # 自动找安装包和游戏目录
    python3 lbee_deck_install.py --game ~/.steam/steam/steamapps/common/'Little Busters! English Edition'
    python3 lbee_deck_install.py --uninstall    # 还原 H 内容 / 语音 / dsound
    python3 lbee_deck_install.py --check        # 只看状态，不动文件

注意：
  * 不要用 sudo 运行（否则游戏目录里会出现 root 属主文件，Steam 无法更新）。
  * 需要约 4.5GB 游戏盘空闲（合并 4GB 的 VOICE0.PAK）。
  * 装完必须在 Steam 启动项里加：WINEDLLOVERRIDES="dsound=n,b" %command%
"""

import argparse
import hashlib
import io
import os
import re
import shutil
import struct
import sys
import time
import zipfile
from pathlib import Path

# ---------------------------------------------------------------- constants

TRAILER_MAGIC = b"LBP1"
TRAILER_SIZE = 20

VANILLA_FONT_SHA = "520F9C0E22EDC176E6C62D3CB460CD2C81174E7091F50FB24A85996D4CF9BD9C"
ZH_FONT_SHA = "3FFF3BB234B3954FB6A4F78CB12CAA8955326AA5B83E296E3292C447ADDFCD04"
NEW_DSOUND_SHA = "14227E93991A69D832CF268FCA9D2E2811E594F16168EFFF2C330F0595A8F95C"
OURS_SCRIPT_SHA = "CA361B814FA400871E9298CA240EA65175539DA9840EEC688503338FB002BAFE"

ORIGINAL_EXE_SIZE = 5208944
VOICE0_VANILLA_COUNT = 41266
VOICE0_MERGED_COUNT = 43148

H_PAKS = ("SCRIPT.PAK", "EVENTCG.PAK", "SYSCG2.PAK")
ZH_PAKS = ("BATTLE.PAK", "FONT.PAK", "GM.PAK", "OTHCG.PAK", "PARTS.PAK", "PT.PAK", "SYSCG.PAK")
BACKUP_DIRNAME = "LBEE_ZH_H_backup"
GAME_DIRNAME = "Little Busters! English Edition"

CHUNK = 8 << 20
_SENDFILE_OK = hasattr(os, "sendfile")

# ---------------------------------------------------------------- terminal


def _fix_stdout():
    for stream in (sys.stdout, sys.stderr):
        enc = (getattr(stream, "encoding", "") or "").lower()
        if enc not in ("utf-8", "utf8"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def say(msg="", end="\n"):
    print(msg, end=end, flush=True)


def hdr(title):
    say()
    say("=" * 62)
    say(f"  {title}")
    say("=" * 62)


class Progress:
    def __init__(self, label, total):
        self.label = label
        self.total = max(1, total)
        self.done = 0
        self.t0 = time.time()
        self._last = 0.0
        self._last_pct10 = -1
        self._tty = bool(getattr(sys.stdout, "isatty", lambda: False)())

    def _line(self):
        pct = 100.0 * self.done / self.total
        mb = self.done / (1 << 20)
        speed = mb / max(1e-6, time.time() - self.t0)
        return f"  {self.label}: {pct:5.1f}%  {mb:8.1f} MB  {speed:6.1f} MB/s"

    def add(self, n):
        self.done += n
        now = time.time()
        if now - self._last < 0.5 and self.done < self.total:
            return
        self._last = now
        pct = 100.0 * self.done / self.total
        if self._tty:
            say(self._line(), end="\r")
        else:
            pct10 = int(pct // 10)
            if pct10 > self._last_pct10:
                self._last_pct10 = pct10
                say(self._line())
        if self.done >= self.total:
            say()

    def finish(self):
        if self.done < self.total:
            self.done = self.total
            self.add(0)


# ---------------------------------------------------------------- helpers


def sha256_file(path, progress_label=None):
    h = hashlib.sha256()
    size = os.path.getsize(path)
    pg = Progress(progress_label, size) if progress_label else None
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
            if pg:
                pg.add(len(b))
    return h.hexdigest().upper()


def pak_file_count(path):
    """前 16 字节: header_size, file_count, id_start, block_size (little endian)."""
    with open(path, "rb") as f:
        b = f.read(16)
    if len(b) < 16:
        return -1
    return struct.unpack_from("<I", b, 4)[0]


def human(n):
    return f"{n / (1 << 30):.2f} GB" if n >= (1 << 30) else f"{n / (1 << 20):.1f} MB"


def _align_up(v, a):
    return (v + a - 1) // a * a


# ---------------------------------------------------------------- setup.exe payload


class SliceFile(io.RawIOBase):
    """把 setup.exe 尾部的 ZIP 区域包装成可 seek 的文件对象（不复制 1GB）。"""

    def __init__(self, path, offset, size):
        self._f = open(path, "rb", buffering=0)
        self._off = offset
        self._size = size
        self._pos = 0

    # io.RawIOBase
    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self._pos

    def seek(self, offset, whence=0):
        if whence == 0:
            p = offset
        elif whence == 1:
            p = self._pos + offset
        elif whence == 2:
            p = self._size + offset
        else:
            raise ValueError("bad whence")
        if p < 0:
            raise ValueError("negative seek")
        self._pos = p
        return p

    def readinto(self, buf):
        n = min(len(buf), self._size - self._pos)
        if n <= 0:
            return 0
        self._f.seek(self._off + self._pos)
        data = self._f.read(n)
        buf[: len(data)] = data
        self._pos += len(data)
        return len(data)

    def close(self):
        try:
            self._f.close()
        finally:
            super().close()


def open_payload(exe_path):
    """打开 setup.exe 内嵌 ZIP，返回 (zipfile, 说明字符串)。"""
    exe_path = Path(exe_path)
    size = exe_path.stat().st_size
    if size < TRAILER_SIZE:
        raise SystemExit(f"[x] 不是有效的安装包: {exe_path}")
    with open(exe_path, "rb") as f:
        f.seek(size - TRAILER_SIZE)
        tr = f.read(TRAILER_SIZE)
    if tr[:4] != TRAILER_MAGIC:
        raise SystemExit(
            f"[x] 安装包尾标志缺失（不是 v1.7.x 的 setup.exe？）: {exe_path}"
        )
    off, zsize = struct.unpack_from("<qq", tr, 4)
    if off < 0 or zsize <= 0 or off + zsize > size:
        raise SystemExit("[x] 安装包内部的 ZIP 区域损坏，请重新下载。")
    return zipfile.ZipFile(SliceFile(exe_path, off, zsize)), f"payload {human(zsize)}"


def find_setup_exe(explicit=None):
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            raise SystemExit(f"[x] 找不到安装包: {p}")
        return p
    names = re.compile(r"LBEE_Uncensored_Patch.*setup\.exe$", re.I)
    dirs = [Path.cwd(), Path(__file__).resolve().parent,
            Path.home() / "Downloads", Path.home() / "Desktop",
            Path.home() / "下载", Path.home() / "桌面"]
    seen = set()
    for d in dirs:
        if not d.is_dir() or str(d) in seen:
            continue
        seen.add(str(d))
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for p in entries:
            if p.is_file() and names.search(p.name):
                return p
    raise SystemExit(
        "[x] 没找到 LBEE_Uncensored_Patch_v*_setup.exe。\n"
        "    把它和本脚本放在同一目录，或用 --exe 指定路径。"
    )


# ---------------------------------------------------------------- PAK header


class PakHeader:
    """与引擎一致的 PAK 头解析（同 lbee/pak.py 的 PakHeader）。"""

    def __init__(self, raw):
        if len(raw) < 0x20:
            raise ValueError("header too small")
        self.raw = raw
        (self.header_size, self.file_count, self.id_start, self.block_size) = struct.unpack_from(
            "<4I", raw, 0
        )
        if self.block_size <= 0 or self.block_size > 0x100000:
            raise ValueError(f"implausible block size {self.block_size}")
        if self.file_count < 0 or self.file_count > 100_000_000:
            raise ValueError(f"implausible file count {self.file_count}")

        pos = 0x20
        bitpos = 0

        def align_byte():
            nonlocal pos, bitpos
            if bitpos:
                pos += 1
                bitpos = 0

        def read_byte():
            nonlocal pos
            align_byte()
            if pos >= len(raw):
                return 0
            v = raw[pos]
            pos += 1
            return v - 256 if v >= 128 else v

        def read_bit():
            nonlocal pos, bitpos
            if pos >= len(raw):
                return 0
            v = (raw[pos] >> bitpos) & 1
            bitpos += 1
            if bitpos >= 8:
                pos += 1
                bitpos = 0
            return v

        def skip_bit():
            nonlocal pos, bitpos
            if pos >= len(raw):
                return
            bitpos += 1
            if bitpos >= 8:
                pos += 1
                bitpos = 0

        def read_u32():
            nonlocal pos
            align_byte()
            if pos + 4 > len(raw):
                return 0
            v = struct.unpack_from("<I", raw, pos)[0]
            pos += 4
            return v

        self.chunk_count = read_byte()
        self.has_extra_table = read_bit()
        skip_bit()
        self.chunks = []          # (index, ctype, offset)
        self.chunk_offset_positions = []
        for _ in range(max(0, self.chunk_count)):
            index = read_byte()
            ctype = read_byte()
            off_pos = pos + (1 if bitpos else 0)
            offset = read_u32()
            if ctype not in (1, 2):
                raise ValueError(f"unknown chunk type {ctype}")
            self.chunks.append((index, ctype, offset))
            self.chunk_offset_positions.append(off_pos)
        align_byte()
        while pos % 4:
            pos += 1
        self.name_offset_position = pos
        self.name_table_offset = read_u32()
        self.table_start = pos
        self.table_end = self.table_start + 8 * self.file_count
        if self.table_end > len(raw):
            raise ValueError("file table beyond header")

    def entry(self, i):
        off_blocks, size = struct.unpack_from("<II", self.raw, self.table_start + 8 * i)
        return off_blocks * self.block_size, size

    def chunk_size(self, ctype, count=None):
        count = self.file_count if count is None else count
        return count * 2 if ctype == 2 else (count + 7) // 8

    def chunk_data(self):
        return [self.raw[off:off + self.chunk_size(ctype)] for _idx, ctype, off in self.chunks]


# ---------------------------------------------------------------- VOICE0 merge


class MergeError(Exception):
    pass


def _write_all(f, data):
    view = memoryview(data)
    while view:
        n = f.write(view)
        if not n:
            raise MergeError("写入失败（磁盘满？）")
        view = view[n:]


def _fsync_dir(path):
    """让 rename 落盘（Linux 才支持对目录 fsync，失败就算了）。"""
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _copy_span(src, dst, offset, size, pg=None):
    """把 src 的 [offset, offset+size) 拷到 dst（Linux 上用 sendfile 零拷贝）。"""
    global _SENDFILE_OK
    todo = size
    pos = offset
    while todo > 0:
        n = min(CHUNK, todo)
        if _SENDFILE_OK:
            try:
                sent = os.sendfile(dst.fileno(), src.fileno(), pos, n)
            except OSError:
                _SENDFILE_OK = False
                sent = 0
            if sent > 0:
                pos += sent
                todo -= sent
                if pg:
                    pg.add(sent)
                continue
        src.seek(pos)
        data = src.read(n)
        if not data:
            raise MergeError("源文件提前结束")
        _write_all(dst, data)
        pos += len(data)
        todo -= len(data)
        if pg:
            pg.add(len(data))


def _write_zeros(dst, count):
    if count <= 0:
        return
    z = b"\x00" * min(count, 1 << 16)
    while count > 0:
        n = min(count, len(z))
        _write_all(dst, z[:n])
        count -= n


def merge_voice0(pak_path, voices_path, expect_count, dry_run=False):
    """把 LBV1 语音追加进 VOICE0.PAK（流式，等价于 LBEE_VoiceMerge4.exe）。"""
    pak_path = Path(pak_path)
    voices_path = Path(voices_path)

    total_size = pak_path.stat().st_size
    with open(pak_path, "rb") as f:
        head16 = f.read(16)
        if len(head16) < 16:
            raise MergeError("PAK 头太短")
        header_size = struct.unpack_from("<I", head16, 0)[0]
        if header_size < 0x40 or header_size > 16 << 20:
            raise MergeError(f"PAK 头长度异常: {header_size}")
        if header_size > total_size:
            raise MergeError("PAK 头比文件还大")
        f.seek(0)
        raw_header = f.read(header_size)

    h = PakHeader(raw_header)
    if h.name_table_offset != 0:
        raise MergeError("该 PAK 带文件名表，不是 VOICE0 的格式")
    if h.has_extra_table:
        raise MergeError("该 PAK 带 12 字节附加表，不是 VOICE0 的格式")
    if expect_count >= 0 and h.file_count != expect_count:
        raise MergeError(
            f"VOICE0 语音条数是 {h.file_count}，不是原版的 {expect_count}"
            f"（可能装过别的补丁，请先在 Steam 里验证文件完整性）"
        )

    # ---- 读 voices.bin (LBV1)
    voices = []  # (id, size, data_offset)
    with open(voices_path, "rb") as vf:
        head = vf.read(8)
        if len(head) < 8 or head[:4] != b"LBV1":
            raise MergeError("voices.bin 魔数不对（不是 LBV1）")
        vcount = struct.unpack_from("<I", head, 4)[0]
        if vcount <= 0 or vcount > 5_000_000:
            raise MergeError(f"voices.bin 条数异常: {vcount}")
        voice_bytes = 0
        for i in range(vcount):
            idx = vf.read(8)
            if len(idx) < 8:
                raise MergeError(f"voices.bin 在第 {i} 条处截断")
            vid, vsize = struct.unpack("<ii", idx)
            if vsize < 0:
                raise MergeError(f"voices.bin 第 {i} 条长度非法")
            voices.append((vid, vsize, vf.tell()))
            vf.seek(vsize, 1)
            voice_bytes += vsize
        if vf.tell() > vf.seek(0, 2):
            raise MergeError("voices.bin 截断")

    voices.sort(key=lambda v: v[0])
    append_base = h.id_start + h.file_count
    for k, (vid, _sz, _off) in enumerate(voices):
        want = append_base + k
        if vid != want:
            raise MergeError(
                f"语音 id 不连续：第 {k} 条应为 {want}，实际 {vid}"
                f"（voices.bin 必须严格是 {append_base}..{append_base + len(voices) - 1}）"
            )

    old_count = h.file_count
    new_count = old_count + len(voices)
    block = h.block_size

    # ---- 侧数据数组扩容：type2 每条约 2 字节；chunk index 1 填 32767
    blobs = h.chunk_data()
    grown = []
    old_chunk_bytes = 0
    for (index, ctype, _off), blob in zip(h.chunks, blobs):
        old_chunk_bytes += len(blob)
        new_size = h.chunk_size(ctype, new_count)
        buf = bytearray(new_size)
        buf[: len(blob)] = blob
        if ctype == 2:
            fill = b"\xff\x7f" if index == 1 else b"\x00\x00"
            buf[len(blob):] = fill * len(voices)
        grown.append(bytes(buf))

    pad = h.header_size - h.table_end - old_chunk_bytes
    if pad < 0:
        raise MergeError("侧数据超出 PAK 头")
    trailing_len = pad + sum(len(b) for b in grown)
    needed = h.table_start + 8 * new_count + trailing_len
    header_size = h.header_size
    if needed > header_size:
        header_size = _align_up(needed, block)

    # ---- 新文件表 / 数据偏移
    offsets = []
    cursor = header_size // block
    for i in range(old_count):
        size = h.entry(i)[1]
        offsets.append(cursor)
        cursor += _align_up(size, block) // block
    new_offsets = []
    for _vid, vsize, _off in voices:
        new_offsets.append(cursor)
        cursor += _align_up(vsize, block) // block
    expected_total = header_size + (cursor - header_size // block) * block

    # ---- 拼新头
    out_header = bytearray(header_size)
    out_header[: h.table_start] = h.raw[: h.table_start]
    struct.pack_into("<I", out_header, 0, header_size)
    struct.pack_into("<I", out_header, 4, new_count)
    chunk_cursor = h.table_start + 8 * new_count
    for pos_field, blob in zip(h.chunk_offset_positions, grown):
        struct.pack_into("<I", out_header, pos_field, chunk_cursor)
        chunk_cursor += len(blob)
    pos = h.table_start
    for i in range(old_count):
        struct.pack_into("<II", out_header, pos, offsets[i], h.entry(i)[1])
        pos += 8
    for k, (vid, vsize, _off) in enumerate(voices):
        struct.pack_into("<II", out_header, pos, new_offsets[k], vsize)
        pos += 8
    for blob in grown:
        out_header[pos:pos + len(blob)] = blob
        pos += len(blob)

    say(f"  VOICE0: {old_count} -> {new_count} 条, 头 {h.header_size} -> {header_size} B, "
        f"新文件 {human(expected_total)}")
    say(f"  追加语音: {len(voices)} 条 / {human(voice_bytes)}, id {voices[0][0]}..{voices[-1][0]}")
    if dry_run:
        return new_count, expected_total

    # ---- 空间检查
    free = shutil.disk_usage(pak_path.parent).free
    if free < expected_total + (64 << 20):
        raise MergeError(
            f"游戏盘空间不足：需要 {human(expected_total + (64 << 20))}，"
            f"只剩 {human(free)}"
        )

    tmp = Path(str(pak_path) + ".new")
    bak = Path(str(pak_path) + ".bak")
    if tmp.exists():
        tmp.unlink()

    pg = Progress("合并 VOICE0", expected_total)
    t0 = time.time()
    try:
        with open(pak_path, "rb", buffering=0) as src, \
                open(voices_path, "rb", buffering=0) as vfs, \
                open(tmp, "wb", buffering=0) as dst:
            _write_all(dst, out_header)
            for i in range(old_count):
                off, size = h.entry(i)
                _copy_span(src, dst, off, size, pg)
                _write_zeros(dst, _align_up(size, block) - size)
            for vid, vsize, voff in voices:
                _copy_span(vfs, dst, voff, vsize, pg)
                _write_zeros(dst, _align_up(vsize, block) - vsize)
            dst.truncate(expected_total)
            os.fsync(dst.fileno())
        pg.finish()

        # ---- 写后校验
        got = tmp.stat().st_size
        if got != expected_total:
            raise MergeError(f"写入后大小不对: {got} != {expected_total}")
        with open(tmp, "rb") as f:
            new_raw = f.read(header_size)
        nh = PakHeader(new_raw)
        if nh.header_size != header_size or nh.file_count != new_count \
                or nh.id_start != h.id_start or nh.block_size != block \
                or nh.chunk_count != h.chunk_count:
            raise MergeError("写入后 PAK 头字段不一致")
        for index, ctype, off in nh.chunks:
            if ctype == 2 and index == 1:
                for i in range(old_count, new_count):
                    v = new_raw[off + 2 * i] | (new_raw[off + 2 * i + 1] << 8)
                    if v != 32767:
                        raise MergeError("写入后侧数据（chunk1）异常")
        if not dry_run:
            say(f"  校验通过，用时 {time.time() - t0:.1f}s")

        # ---- 备份 + 原子替换（两个 rename 之间没有 VOICE0，断电只会剩 .bak，可恢复）
        os.replace(pak_path, bak)
        try:
            os.replace(tmp, pak_path)
        except OSError:
            os.replace(bak, pak_path)      # 替换失败则回滚
            raise
        _fsync_dir(pak_path.parent)
    except BaseException:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise
    return new_count, expected_total


# ---------------------------------------------------------------- game discovery


def _library_paths(root):
    out = [root]
    vdf = root / "steamapps" / "libraryfolders.vdf"
    if vdf.is_file():
        try:
            txt = vdf.read_text(errors="replace")
        except OSError:
            txt = ""
        for m in re.findall(r'"path"\s+"([^"]+)"', txt):
            p = Path(m.replace("\\\\", "\\"))
            if p.is_dir():
                out.append(p)
    return out


def _find_child(parent, name):
    try:
        for e in os.scandir(parent):
            if e.is_dir() and e.name.casefold() == name.casefold():
                return Path(e.path)
    except OSError:
        return None
    return None


def candidate_games():
    home = Path.home()
    roots = [
        home / ".steam" / "steam",
        home / ".steam" / "root",
        home / ".local" / "share" / "Steam",
        Path("/usr/local/share/Steam"),
    ]
    # SD 卡 / 外置库
    for base in (Path("/run/media"), Path("/media"), Path("/mnt")):
        if base.is_dir():
            try:
                for mount in base.glob("*/*"):
                    roots.append(mount)
            except OSError:
                pass

    seen = set()
    out = []
    for root in roots:
        if not root.is_dir():
            continue
        for lib in _library_paths(root):
            common = lib / "steamapps" / "common"
            if not common.is_dir():
                continue
            g = _find_child(common, GAME_DIRNAME)
            if g and str(g) not in seen:
                seen.add(str(g))
                out.append(g)
    return out


def _looks_like_game(p):
    """必须有 files/SCRIPT.PAK，且能看到主程序或 VOICE0（防止把解包目录当游戏目录）。"""
    return ((p / "files" / "SCRIPT.PAK").is_file()
            and ((p / "LITBUS_WIN32.exe").is_file()
                 or (p / "files" / "VOICE0.PAK").is_file()))


def find_game(hint=None):
    if hint:
        p = Path(hint).expanduser()
        if _looks_like_game(p):
            return p
        raise SystemExit(f"[x] {p} 不像游戏目录（缺 files/SCRIPT.PAK 或 LITBUS_WIN32.exe）")
    for g in candidate_games():
        if _looks_like_game(g):
            return g
    raise SystemExit(
        "[x] 没找到游戏目录。请确认已安装《Little Busters! English Edition》，"
        "或用 --game 指定（路径含 files/SCRIPT.PAK）。"
    )


# ---------------------------------------------------------------- state / steps


def read_state(game):
    files = game / "files"
    st = {
        "game": game,
        "script_sha": sha256_file(files / "SCRIPT.PAK"),
        "font_sha": sha256_file(files / "FONT.PAK") if (files / "FONT.PAK").is_file() else "",
        "dsound_sha": sha256_file(game / "dsound.dll") if (game / "dsound.dll").is_file() else "",
        "voice_count": pak_file_count(files / "VOICE0.PAK") if (files / "VOICE0.PAK").is_file() else -1,
        "exe_size": (game / "LITBUS_WIN32.exe").stat().st_size if (game / "LITBUS_WIN32.exe").is_file() else 0,
    }
    st["chinese_ok"] = st["font_sha"] == ZH_FONT_SHA
    st["ours"] = st["script_sha"] == OURS_SCRIPT_SHA
    return st


def show_state(st):
    say(f"  游戏目录 : {st['game']}")
    say(f"  主程序   : {'原版' if st['exe_size'] == ORIGINAL_EXE_SIZE else '非原版/未知'} "
        f"({st['exe_size']:,} B, 原版应为 {ORIGINAL_EXE_SIZE:,} B)")
    say(f"  汉化字体 : {'已装 (FONT.PAK 正确)' if st['chinese_ok'] else '未装 / 不完整'}")
    say(f"  H 内容   : {'已装 (SCRIPT.PAK 匹配 v1.7.4)' if st['ours'] else '未装'}")
    vc = st["voice_count"]
    if vc == VOICE0_MERGED_COUNT:
        say(f"  语音     : 已合并 ({vc} 条)")
    elif vc == VOICE0_VANILLA_COUNT:
        say(f"  语音     : 原版 ({vc} 条)，待合并")
    else:
        say(f"  语音     : 异常 ({vc} 条，原版 {VOICE0_VANILLA_COUNT} / 合并后 {VOICE0_MERGED_COUNT})")
    if st["dsound_sha"]:
        say(f"  dsound   : {'最新 (2026.10.01)' if st['dsound_sha'] == NEW_DSOUND_SHA else '旧版/非补丁版本'}")


def copy_zip_entry(zf, name, dest, label=None):
    """解出 ZIP 条目到 dest（先写 .part，校验大小后原子替换，避免半截文件）。"""
    info = zf.getinfo(name)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(dest) + ".part")
    if tmp.exists():
        tmp.unlink()
    pg = Progress(label or f"复制 {dest.name}", info.file_size)
    try:
        with zf.open(info) as src, open(tmp, "wb") as dst:
            while True:
                b = src.read(CHUNK)
                if not b:
                    break
                _write_all(dst, b)
                pg.add(len(b))
            dst.flush()
            os.fsync(dst.fileno())
        pg.finish()
        if tmp.stat().st_size != info.file_size:
            raise MergeError(f"{name} 解压后大小不符（{tmp.stat().st_size} != {info.file_size}）")
        os.replace(tmp, dest)
    except BaseException:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise
    return dest


def install(args):
    game = find_game(args.game)
    exe = find_setup_exe(args.exe)
    zf, payload_note = open_payload(exe)

    # 安装包完整性：缺条目直接给中文提示（避免 KeyError / 半装）
    names = set(zf.namelist())
    required = ([f"files/{p}" for p in H_PAKS]
                + [f"zh_files/{p}" for p in ZH_PAKS]
                + ["dsound.dll", "voices/voices.bin"])
    missing = [r for r in required if r not in names]
    if missing:
        raise SystemExit(
            "[x] 安装包内容不完整或版本不对，缺少：\n    " + "\n    ".join(missing[:8]) +
            "\n    请重新下载 LBEE_Uncensored_Patch_v1.7.4_setup.exe。"
        )

    hdr("LBEE 内容还原补丁 · Deck/Linux 安装器")
    say(f"  安装包   : {exe.name}  ({payload_note})")
    st = read_state(game)
    show_state(st)
    say()

    files = game / "files"

    if st["exe_size"] and st["exe_size"] != ORIGINAL_EXE_SIZE:
        say("  ! LITBUS_WIN32.exe 不是 Steam 原版，改过的 exe 会和汉化钩子冲突（黑屏）。")
        say("    建议先 Steam → 属性 → 已安装文件 → 验证完整性。")
        if args.dry_run:
            say("    （dry-run：不询问，继续检查）")
        elif not args.yes:
            if input("  仍要继续？[y/N] ").strip().lower() != "y":
                return 1

    need = 0
    if not st["chinese_ok"]:
        need += sum(zf.getinfo(f"zh_files/{p}").file_size for p in ZH_PAKS)
    if st["voice_count"] == VOICE0_VANILLA_COUNT:
        need += 4_300_000_000
    free = shutil.disk_usage(game).free
    say(f"  磁盘空闲 : {human(free)}（本次约需 {human(need)}）")
    if need and free < need:
        say("  [x] 空间不足。VOICE0 合并要 4.13GB 新文件 + 保留 3.99GB 原文件，约需 4.3GB 余量。")
        return 1

    if args.dry_run:
        say()
        say("  [dry-run] 只解析，不写任何文件。计划：")
        say(f"    汉化   : {'已装，跳过' if st['chinese_ok'] else '写入 %d 个 PAK + dsound.dll' % len(ZH_PAKS)}")
        bak_dir = files / BACKUP_DIRNAME
        say(f"    备份   : {'已有 .complete 标记' if (bak_dir / '.complete').is_file() else '新建 files/' + BACKUP_DIRNAME}")
        say(f"    H 内容 : 覆盖 {', '.join(H_PAKS)}")
        if st["voice_count"] == VOICE0_VANILLA_COUNT:
            with zf.open("voices/voices.bin") as vf:
                vh = vf.read(8)
            vc = struct.unpack_from("<I", vh, 4)[0] if len(vh) >= 8 else -1
            say(f"    语音   : 合并 {vc} 条（先写 .new 再替换，原文件留 .bak）")
        else:
            say("    语音   : 已是合并状态，跳过")
        return 0

    if not args.yes:
        say()
        say("  将执行：")
        if not st["chinese_ok"]:
            say("   1) 写入 Jack-Myth 中文汉化（7 个 PAK + dsound.dll）")
        else:
            say("   1) 汉化已在，跳过")
        say("   2) 备份原版 SCRIPT/EVENTCG/SYSCG2 到 files/LBEE_ZH_H_backup")
        say("   3) 覆盖 H 内容 3 个 PAK")
        say("   4) 把 1,882 条语音合并进 VOICE0.PAK（4GB，1-3 分钟）")
        if input("\n  开始安装？[Y/n] ").strip().lower() not in ("", "y", "yes"):
            return 1

    if not st["chinese_ok"]:
        hdr("1/4 安装 Jack-Myth 中文汉化")
        for p in ZH_PAKS:
            copy_zip_entry(zf, f"zh_files/{p}", files / p, f"[汉化] {p}")
        ds_dst = game / "dsound.dll"
        ds_bak = Path(str(ds_dst) + ".bak")
        if ds_dst.is_file() and not ds_bak.exists():
            shutil.copyfile(ds_dst, ds_bak)
        copy_zip_entry(zf, "dsound.dll", ds_dst, "[汉化] dsound.dll")
        if sha256_file(files / "FONT.PAK") != ZH_FONT_SHA:
            say("  [x] 汉化复制后 FONT.PAK 校验失败。请确认安装包完整。")
            return 1
        say("  汉化安装完成。")
    else:
        say("1/4 汉化已完整，跳过。")

    # ---- 2) 备份 H 内容原文件（.complete 标记保证「有标记 = 三个备份都完整」）
    bak_dir = files / BACKUP_DIRNAME
    marker = bak_dir / ".complete"
    if marker.is_file():
        say("2/4 已有完整备份，跳过。")
    else:
        hdr("2/4 备份原文件")
        bak_dir.mkdir(parents=True, exist_ok=True)
        for p in H_PAKS:
            src = files / p
            cur = bak_dir / p
            # 已有非空备份一律保留：宁可留旧版，也不要用"已打过补丁"的文件覆盖原版备份
            if cur.is_file() and cur.stat().st_size > 0:
                say(f"  [备份] {p} 已存在，保留")
                continue
            copy_zip_entry_bytes(src, cur, f"[备份] {p}")
        marker.write_text("ok\n")
        _fsync_dir(bak_dir)
        say("  备份完成。")

    # ---- 3) H 内容
    hdr("3/4 写入 H 内容")
    for p in H_PAKS:
        copy_zip_entry(zf, f"files/{p}", files / p, f"[H] {p}")

    # ---- 3.5) dsound 版本
    ds_dst = game / "dsound.dll"
    ds_bak = Path(str(ds_dst) + ".bak")
    cur = sha256_file(ds_dst) if ds_dst.is_file() else ""
    if cur != NEW_DSOUND_SHA:
        say("  更新汉化兼容层 dsound.dll (2026.10.01)...")
        if ds_dst.is_file() and not ds_bak.exists():
            shutil.copyfile(ds_dst, ds_bak)
        copy_zip_entry(zf, "dsound.dll", ds_dst, "[dsound] dsound.dll")

    # ---- 4) 语音合并
    hdr("4/4 合并语音到 VOICE0.PAK")
    voice_pak = files / "VOICE0.PAK"
    if not voice_pak.is_file():
        say("  [x] 找不到 files/VOICE0.PAK，游戏目录不完整，请先 Steam 验证完整性。")
        return 1
    cnt = pak_file_count(voice_pak)
    if cnt == VOICE0_MERGED_COUNT:
        say(f"  VOICE0.PAK 已是 {cnt} 条，跳过。")
    elif cnt != VOICE0_VANILLA_COUNT:
        say(f"  [x] VOICE0.PAK 是 {cnt} 条（原版应为 {VOICE0_VANILLA_COUNT}）。")
        say("      请先在 Steam 里验证文件完整性，再重新运行本脚本。")
        return 1
    else:
        tmp_voices = files / ".lbee_voices.bin"
        try:
            copy_zip_entry(zf, "voices/voices.bin", tmp_voices, "[voices] voices.bin")
            merge_voice0(voice_pak, tmp_voices, VOICE0_VANILLA_COUNT)
        finally:
            try:
                tmp_voices.unlink()
            except OSError:
                pass

    zf.close()

    # ---- 收尾自检：和 Windows 安装器同样的 4 项校验
    hdr("安装完成 · 自检")
    checks = [
        ("files/SCRIPT.PAK（H 内容）", sha256_file(files / "SCRIPT.PAK") == OURS_SCRIPT_SHA),
        ("files/FONT.PAK（汉化字体）", sha256_file(files / "FONT.PAK") == ZH_FONT_SHA),
        ("dsound.dll（兼容层）", (game / "dsound.dll").is_file()
         and sha256_file(game / "dsound.dll") == NEW_DSOUND_SHA),
        ("files/VOICE0.PAK（语音）", pak_file_count(files / "VOICE0.PAK") == VOICE0_MERGED_COUNT),
    ]
    for name, ok in checks:
        say(f"  {'OK  ' if ok else 'FAIL'} {name}")
    if not all(ok for _n, ok in checks):
        say()
        say("  [x] 自检未通过。请把上面的输出和安装日志发到 QQ 群 1136805764。")
        say("      也可以先 Steam 验证文件完整性，再重跑本脚本。")
        return 1

    say()
    say("  1) Steam → 库 → 右键游戏 → 属性 → 启动选项，填入：")
    say('       WINEDLLOVERRIDES="dsound=n,b" %command%')
    say("     （不加这一行，汉化字体钩子不会加载，进游戏会缺字/黑屏）")
    say("  2) 用新存档开始游戏（旧存档结构不兼容，会回标题）")
    say("  3) 卸载：python3 lbee_deck_install.py --uninstall")
    if (files / "VOICE0.PAK.bak").is_file():
        say()
        say("  提示：files/VOICE0.PAK.bak 是合并前的原文件（3.99GB）。")
        say("        确认游戏正常后可以删掉它腾空间，但删了就不能一键还原语音。")
    say()
    return 0


def copy_zip_entry_bytes(src, dest, label):
    """把已有文件复制到目标（先写 .part，fsync 后原子替换）。"""
    src = Path(src)
    dest = Path(dest)
    size = src.stat().st_size
    pg = Progress(label, size)
    tmp = Path(str(dest) + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if tmp.exists():
        tmp.unlink()
    try:
        with open(src, "rb") as s, open(tmp, "wb") as d:
            while True:
                b = s.read(CHUNK)
                if not b:
                    break
                _write_all(d, b)
                pg.add(len(b))
            d.flush()
            os.fsync(d.fileno())
        pg.finish()
        if tmp.stat().st_size != size:
            raise MergeError(f"{src.name} 复制后大小不符")
        os.replace(tmp, dest)
        _fsync_dir(dest.parent)
    except BaseException:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise


# ---------------------------------------------------------------- uninstall


def uninstall(args):
    game = find_game(args.game)
    files = game / "files"
    hdr("LBEE 内容还原补丁 · 卸载")
    say(f"  游戏目录 : {game}")
    if not args.yes and input("\n  确认还原 H 内容 / 语音 / dsound？[y/N] ").strip().lower() != "y":
        return 1

    bak_dir = files / BACKUP_DIRNAME
    if bak_dir.is_dir():
        for p in H_PAKS:
            src = bak_dir / p
            if src.is_file():
                copy_zip_entry_bytes(src, files / p, f"[还原] {p}")
        for p in H_PAKS:
            if (files / p).is_file():
                say(f"  已还原 files/{p}")
    else:
        say("  没有找到 H 内容备份（可能没装过）。")

    voice_bak = files / "VOICE0.PAK.bak"
    stale = files / "VOICE0.PAK.patched.tmp"
    if stale.is_file():
        try:
            stale.unlink()          # 清掉上次崩溃留下的临时文件
        except OSError:
            pass
    if voice_bak.is_file():
        live = files / "VOICE0.PAK"
        if live.is_file():
            os.replace(live, stale)
        try:
            os.replace(voice_bak, live)
        except OSError:
            if stale.is_file() and not live.exists():
                os.replace(stale, live)     # 回滚，别把 4GB 弄丢
            raise
        try:
            stale.unlink()
        except OSError:
            pass
        _fsync_dir(files)
        say("  已从 VOICE0.PAK.bak 还原语音。")
    else:
        say("  没有 VOICE0.PAK.bak（语音可能没合并过）。")

    ds = game / "dsound.dll"
    ds_bak = game / "dsound.dll.bak"
    if ds_bak.is_file():
        os.replace(ds_bak, ds)
        say("  已还原 dsound.dll。")
    else:
        say("  dsound.dll 没有备份，可忽略（Steam 验证会一并还原）。")

    say()
    say("  还原完成。要彻底恢复官方文件（汉化的 7 个 PAK），请用：")
    say("    Steam → 属性 → 已安装文件 → 验证游戏文件完整性")
    say()
    return 0


# ---------------------------------------------------------------- extract


def extract_all(args):
    exe = find_setup_exe(args.exe)
    zf, note = open_payload(exe)
    dest = Path(args.extract_only).expanduser()
    hdr("解包安装文件")
    say(f"  安装包 : {exe.name} ({note})")
    say(f"  输出到 : {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    infos = zf.infolist()
    skipped = 0
    for i, info in enumerate(infos, 1):
        name = info.filename
        target = (dest / name)
        try:
            resolved = target.resolve()
        except OSError:
            skipped += 1
            continue
        if resolved != root and root not in resolved.parents:   # 防 zip-slip
            say(f"  ! 跳过可疑路径: {name}")
            skipped += 1
            continue
        if name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst, CHUNK)
        if i % 20 == 0 or i == len(infos):
            say(f"  {i}/{len(infos)}", end="\r")
    say()
    say(f"  完成，共 {len(infos)} 个文件" + (f"，跳过 {skipped} 个。" if skipped else "。"))
    return 0


# ---------------------------------------------------------------- main


def main(argv=None):
    _fix_stdout()
    ap = argparse.ArgumentParser(
        description="LBEE 内容还原补丁 Steam Deck / Linux 安装器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--exe", help="setup.exe 路径（默认自动在脚本目录/下载目录找）")
    ap.add_argument("--game", help="游戏根目录（含 files/SCRIPT.PAK）")
    ap.add_argument("--yes", "-y", action="store_true", help="不再询问，直接执行")
    ap.add_argument("--check", action="store_true", help="只检查状态")
    ap.add_argument("--uninstall", action="store_true", help="还原 H 内容 / 语音 / dsound")
    ap.add_argument("--extract-only", metavar="DIR", help="只把安装包解压到 DIR")
    ap.add_argument("--dry-run", action="store_true", help="只解析，不写文件")
    args = ap.parse_args(argv)

    if getattr(os, "geteuid", lambda: -1)() == 0:
        raise SystemExit(
            "[x] 不要用 sudo / root 运行：会在游戏目录里留下 root 文件，Steam 反而更新不了。\n"
            "    直接以 deck 用户运行即可。"
        )

    if args.extract_only:
        return extract_all(args)
    if args.uninstall:
        return uninstall(args)
    if args.check:
        game = find_game(args.game)
        hdr("状态检查")
        st = read_state(game)
        show_state(st)
        ok = st["chinese_ok"] and st["ours"] and st["voice_count"] == VOICE0_MERGED_COUNT
        say()
        say("  结论: " + ("已安装完整 ✅" if ok else "未安装完整（运行本脚本即可）"))
        return 0 if ok else 1
    return install(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say("\n已取消。")
        sys.exit(130)
    except MergeError as e:
        say(f"\n[x] {e}")
        sys.exit(1)
    except PermissionError as e:
        say(f"\n[x] 没有写权限：{e}")
        say("    游戏目录可能是只读挂载，或文件属主不对（不要用 sudo 跑过）。")
        sys.exit(1)
    except OSError as e:
        say(f"\n[x] 文件操作失败：{e}")
        say("    请检查磁盘空间 / 游戏目录权限后重试。")
        sys.exit(1)
