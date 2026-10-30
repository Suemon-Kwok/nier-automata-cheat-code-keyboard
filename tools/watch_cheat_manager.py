# watch_cheat_manager.py  (read-only: it never writes to the game)
# 1) Finds the cheat manager object in memory by its stored 9-button code.
# 2) Watches its press counter, 5-second timer and "fired" flag, plus the input masks.
# The timer only counts up while the cheat function is past ALL its checks
# (right map, R2 held, within 1.5 m of the spot), so it shows live whether you are in the zone.
import math, re, struct, subprocess, sys, os, time

HELD_RVA, PRESSED_RVA, STATE_RVA = 0x13FCC00, 0x13FCC04, 0xF64A90
CHECKS = [(0x834F5B, b"\xf7\x05"), (0x83502B, b"\x83\x3d")]
CODE = [0x8, 0x4, 0x8, 0x2, 0x1, 0x40, 0x20, 0x80, 0x10]   # Up Down Up Right Left X B Y A (from your log)
OFF_ARRAY, OFF_COUNT, OFF_CAP, OFF_TIMER, OFF_FIRED = 0x70, 0x50, 0x48, 0x94, 0x34
PAT = struct.pack("<9I", *CODE)
SINGLE = b"[\x01\x02\x04\x08\x10\x20\x40\x80]\x00\x00\x00"
RELAXED = re.compile(b"(?:" + SINGLE + b"){9}", re.S)

def ensure(pkg):
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def exact_finder(data):
    i = data.find(PAT)
    while i != -1:
        yield i
        i = data.find(PAT, i + 1)

def relaxed_finder(data):
    for m in RELAXED.finditer(data):
        v = struct.unpack("<9I", m.group(0))
        if v[0] == v[2]:
            yield m.start()

def scan_memory(read, regions, finder, chunk=4 << 20):
    """regions: iterable of (base, size). Returns sorted absolute addresses (4-byte aligned)."""
    hits, ov = [], len(PAT) - 1
    for base, size in regions:
        off = 0
        while off < size:
            n = min(chunk, size - off)
            try: data = read(base + off, n)
            except Exception: data = None
            if data:
                for i in finder(data):
                    a = base + off + i
                    if a % 4 == 0: hits.append(a)
            if off + n >= size: break
            off += chunk - ov
    return sorted(set(hits))

def read_fields(read, A):
    rbx = A - OFF_ARRAY
    code = struct.unpack("<9I", read(A, 36))
    count = struct.unpack("<Q", read(rbx + OFF_COUNT, 8))[0]
    cap = struct.unpack("<Q", read(rbx + OFF_CAP, 8))[0]
    timer = struct.unpack("<f", read(rbx + OFF_TIMER, 4))[0]
    fired = struct.unpack("<I", read(rbx + OFF_FIRED, 4))[0]
    return dict(A=A, rbx=rbx, code=code, count=count, cap=cap, timer=timer, fired=fired)

def plausible(f):
    return f["count"] <= 100 and math.isfinite(f["timer"]) and -1 <= f["timer"] <= 10

def diff_line(prev, cur):
    held, pressed = cur
    line = "masks held=%08x pressed=%08x" % (held, pressed)
    if prev is not None:
        on, off = held & ~prev[0], prev[0] & ~held
        if on:  line += "  held+%x" % on
        if off: line += "  held-%x" % off
    return line

def win_regions(handle):
    import ctypes
    from ctypes import wintypes
    class MBI(ctypes.Structure):
        _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", wintypes.DWORD), ("PartitionId", wintypes.WORD),
                    ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
                    ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
    k32.VirtualQueryEx.restype = ctypes.c_size_t
    mbi, addr, out = MBI(), 0, []
    while addr < 0x7FFFFFFF0000:
        if not k32.VirtualQueryEx(handle, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        base, size = mbi.BaseAddress or 0, mbi.RegionSize
        writable = mbi.Protect & (0x04 | 0x08 | 0x40 | 0x80)
        if mbi.State == 0x1000 and writable and not (mbi.Protect & 0x101):
            out.append((base, size))
        addr = base + size
    return out

def main():
    ensure("pymem")
    import pymem, pymem.process
    if struct.calcsize("P") * 8 != 64: sys.exit("Use a 64-bit Python.")
    pm = None
    for name in ("NieRAutomata.exe", "NieRAutomataCompat.exe"):
        try: pm = pymem.Pymem(name); exe = name; break
        except Exception: pass
    if pm is None: sys.exit("NieR is not running. Launch the game first.")
    mod = pymem.process.module_from_name(pm.process_handle, exe)
    base, size = mod.lpBaseOfDll, mod.SizeOfImage
    read = pm.read_bytes
    here = os.path.dirname(os.path.abspath(__file__))
    logf = open(os.path.join(here, "cheat_manager_log.txt"), "w", buffering=1)
    def say(s):
        print(s); logf.write(s + "\n")

    for rva, expect in CHECKS:
        if read(base + rva, len(expect)) != expect:
            sys.exit("This game build does not match. Stop here.")
    say("build check OK")
    raw = read(base + STATE_RVA, 0x40)
    say("state dword at f64a90 = %08x" % struct.unpack_from("<I", raw, 0)[0])
    say("bytes at f64a90: " + raw.hex(" "))

    say("scanning game memory for the stored cheat code (about 10-30 s)...")
    regions = win_regions(pm.process_handle)
    hits = scan_memory(read, regions, exact_finder)
    mode = "exact"
    if not hits:
        say("exact code not found; trying a relaxed search")
        hits, mode = scan_memory(read, regions, relaxed_finder), "relaxed"
    cands = []
    for a in hits[:30]:
        try: f = read_fields(read, a)
        except Exception: continue
        where = "game image rva %x" % (a - base) if base <= a < base + size else "heap"
        say("hit[%s] addr=%x (%s) code=%s count=%d cap=%d timer=%g fired=%x" % (
            mode, a, where, " ".join("%x" % c for c in f["code"]), f["count"], f["cap"], f["timer"], f["fired"]))
        if plausible(f): cands.append(f)
    cands = cands[:4]
    if not cands:
        say("no plausible manager object found; stopping after the masks watch.")
    say("\nWatching. Do your test, then Alt+Tab here and press Ctrl+C.\n")

    t0, prev_m, prev_state = time.time(), None, None
    st = [dict(count=f["count"], fired=f["fired"], tval=f["timer"], tt=0.0) for f in cands]
    try:
        while True:
            now = time.time() - t0
            held, pressed = struct.unpack("<II", read(base + HELD_RVA, 8))
            if (held, pressed) != prev_m:
                say("t=%7.3f  %s" % (now, diff_line(prev_m, (held, pressed)))); prev_m = (held, pressed)
            state = struct.unpack("<I", read(base + STATE_RVA, 4))[0]
            if state != prev_state:
                say("t=%7.3f  state f64a90 = %08x" % (now, state)); prev_state = state
            for i, f0 in enumerate(cands):
                f = read_fields(read, f0["A"]); s = st[i]
                if f["count"] != s["count"]:
                    say("t=%7.3f  cand%d count %d -> %d" % (now, i, s["count"], f["count"])); s["count"] = f["count"]
                if f["fired"] != s["fired"]:
                    say("t=%7.3f  cand%d FIRED flag %x -> %x" % (now, i, s["fired"], f["fired"])); s["fired"] = f["fired"]
                moved = abs(f["timer"] - s["tval"]) > 0.01
                reset = f["timer"] < s["tval"] - 0.5
                if moved and (reset or now - s["tt"] >= 0.5):
                    say("t=%7.3f  cand%d timer %.2f%s" % (now, i, f["timer"], "  (reset)" if reset else ""))
                    s["tval"], s["tt"] = f["timer"], now
                elif moved:
                    pass
            time.sleep(0.004)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        say("stopped: %r" % (e,))
    logf.close()
    print("\nsaved cheat_manager_log.txt")

if __name__ == "__main__":
    main()
