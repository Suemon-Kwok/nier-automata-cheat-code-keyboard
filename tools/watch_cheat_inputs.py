# watch_cheat_inputs.py  (read-only: it never writes to the game)
# Watches the two input-mask values the cheat function reads, and disassembles two helper
# functions for reference. Results go to cheat_inputs_log.txt and cheat_functions.txt.
import struct, subprocess, sys, os, time

HELD_RVA, PRESSED_RVA = 0x13FCC00, 0x13FCC04   # read by the cheat function (R2 test / new-press test)
CHECKS = [(0x834F5B, b"\xf7\x05"),             # test dword ptr [rip+..], 0x4000   (R2 test)
          (0x83502B, b"\x83\x3d")]             # cmp  dword ptr [rip+..], 0        (new-press test)
FUNCS = [0x3084C0, 0x745D40]                   # helpers called by the cheat function

def ensure(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def diff_line(t, prev, cur):
    held, pressed = cur
    line = "t=%7.3f  held=%08x  pressed=%08x" % (t, held, pressed)
    if prev is not None:
        on, off = held & ~prev[0], prev[0] & ~held
        if on:  line += "   held+%x" % on
        if off: line += "   held-%x" % off
    return line

def describe_live(pm, base, t):
    try:
        raw = pm.read_bytes(base + t, 48)
    except Exception:
        return ""
    d = struct.unpack_from("<I", raw, 0)[0]
    f = struct.unpack_from("<f", raw, 0)[0]
    s = raw.split(b"\x00")[0]
    txt = s.decode("ascii") if len(s) >= 4 and all(32 <= c < 127 for c in s) else ""
    out = "   ; [%x] dword=%08x float=%g" % (t, d, f)
    return out + (' str="%s"' % txt if txt else "")

def disasm_at(pm, base, rva, maxlen=0x300):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86_const
    from capstone.x86 import X86_OP_MEM
    code = pm.read_bytes(base + rva, maxlen)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    lines = ["=== function at rva %x ===" % rva]
    for ins in md.disasm(code, rva):
        ann = ""
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == x86_const.X86_REG_RIP:
                ann = describe_live(pm, base, ins.address + ins.size + op.mem.disp)
        lines.append("%08x  %-6s %s%s" % (ins.address, ins.mnemonic, ins.op_str, ann))
        off = ins.address + ins.size - rva
        if ins.mnemonic == "ret" and code[off:off + 1] == b"\xcc":
            break
    return "\n".join(lines)

def main():
    ensure("pymem"); ensure("capstone")
    import pymem, pymem.process
    if struct.calcsize("P") * 8 != 64: sys.exit("Use a 64-bit Python.")
    pm = None
    for name in ("NieRAutomata.exe", "NieRAutomataCompat.exe"):
        try: pm = pymem.Pymem(name); exe = name; break
        except Exception: pass
    if pm is None: sys.exit("NieR is not running. Launch the game first.")
    base = pymem.process.module_from_name(pm.process_handle, exe).lpBaseOfDll
    here = os.path.dirname(os.path.abspath(__file__))

    for rva, expect in CHECKS:
        got = pm.read_bytes(base + rva, len(expect))
        if got != expect:
            sys.exit("This game build does not match (bytes at %x are %s). Stop here." % (rva, got.hex(" ")))
    print("build check OK")

    with open(os.path.join(here, "cheat_functions.txt"), "w") as f:
        f.write("\n\n".join(disasm_at(pm, base, r) for r in FUNCS))
    print("saved cheat_functions.txt")

    print("\nWatching input masks. Do your test presses (pause ~2 s between each).")
    print("Press Ctrl+C in this window when finished.\n")
    t0, prev, log = time.time(), None, []
    try:
        while True:
            held, pressed = struct.unpack("<II", pm.read_bytes(base + HELD_RVA, 8))
            cur = (held, pressed)
            if cur != prev:
                line = diff_line(time.time() - t0, prev, cur)
                print(line); log.append(line); prev = cur
            time.sleep(0.002)
    except KeyboardInterrupt:
        pass
    path = os.path.join(here, "cheat_inputs_log.txt")
    with open(path, "w") as f: f.write("\n".join(log))
    print("\nsaved:", path)

if __name__ == "__main__":
    main()
