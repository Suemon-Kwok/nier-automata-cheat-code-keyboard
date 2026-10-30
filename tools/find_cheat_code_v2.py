# find_cheat_code_v2.py  (read-only: it never writes to the game)
# Finds the function that loads the cheat-spot constant X=-665.0, disassembles it,
# and also looks for the Z=493.69 constant stored in other ways.
# Results are saved to cheat_report.txt next to this script.
import re, struct, subprocess, sys, os

Z_VAL, X_VAL, TOL = 493.69, -665.0, 0.05

PAT = re.compile(
    rb'(?:\xf3|\x66|\xf2)?[\x40-\x4f]?\x0f[\x10\x28\x2e\x2f\x51\x58\x59\x5c\x5d\x5e\x5f]'
    rb'[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]', re.S)

def rip_refs(img):
    n = len(img)
    for m in PAT.finditer(img):
        end = m.end()
        if end + 4 > n:
            continue
        disp = struct.unpack_from('<i', img, end)[0]
        target = end + 4 + disp
        if 0 <= target <= n - 4:
            yield m.start(), target, struct.unpack_from('<f', img, target)[0]

def find_hits(img):
    zs, xs = [], []
    for ins, tgt, val in rip_refs(img):
        if abs(val - Z_VAL) < TOL: zs.append((ins, tgt, val))
        elif abs(val - X_VAL) < TOL: xs.append((ins, tgt, val))
    return zs, xs

def aligned_float_hits(img, lo, hi, limit=40):
    out, n = [], len(img) // 4
    for i, (v,) in enumerate(struct.iter_unpack('<f', img[:n * 4])):
        if lo <= v <= hi:
            out.append((i * 4, v))
            if len(out) >= limit: break
    return out

def imm_float_hits(img, val, tol, limit=40):
    """mov r32, imm32 where imm32 is a float close to val."""
    b = struct.pack('<f', val)
    rx = re.compile(b'[\\xb8-\\xbf]..' + re.escape(b[2:4]), re.S)
    out = []
    for m in rx.finditer(img):
        f = struct.unpack_from('<f', img, m.start() + 1)[0]
        if abs(f - val) < tol:
            out.append((m.start(), f))
            if len(out) >= limit: break
    return out

def describe(img, t):
    if not (0 <= t <= len(img) - 4): return ""
    f = struct.unpack_from('<f', img, t)[0]
    d = struct.unpack_from('<I', img, t)[0]
    s = bytes(img[t:t + 48]).split(b'\x00')[0]
    txt = s.decode('ascii') if len(s) >= 4 and all(32 <= c < 127 for c in s) else ""
    out = "   ; [%x] dword=%08x float=%g" % (t, d, f)
    if txt: out += ' str="%s"' % txt
    return out

def disasm_function(img, hit_rva, maxlen=0xA00):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    from capstone import x86_const
    from capstone.x86 import X86_OP_MEM
    lo = max(0, hit_rva - 0x2000)
    idx = img.rfind(b'\xcc\xcc', lo, hit_rva)
    start = idx + 2 if idx >= 0 else max(0, hit_rva - 0x100)
    while start < hit_rva and img[start] == 0xcc:
        start += 1
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    lines = ["function start (guess): %x" % start]
    for ins in md.disasm(bytes(img[start:start + maxlen]), start):
        ann = ""
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == x86_const.X86_REG_RIP:
                ann = describe(img, ins.address + ins.size + op.mem.disp)
        mark = "  <== HIT" if ins.address == hit_rva else ""
        lines.append("%08x  %-6s %s%s%s" % (ins.address, ins.mnemonic, ins.op_str, ann, mark))
        nxt = ins.address + ins.size
        if ins.mnemonic == "ret" and ins.address > hit_rva and img[nxt:nxt + 1] == b'\xcc':
            break
    return "\n".join(lines)

def read_image(pm, base, size, chunk=0x100000):
    buf = bytearray(size)
    for off in range(0, size, chunk):
        n = min(chunk, size - off)
        try:
            buf[off:off + n] = pm.read_bytes(base + off, n)
        except Exception:
            for p in range(0, n, 0x1000):
                m = min(0x1000, n - p)
                try: buf[off + p:off + p + m] = pm.read_bytes(base + off + p, m)
                except Exception: pass
    return bytes(buf)

def ensure(pkg, mod=None):
    try:
        __import__(mod or pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def main():
    ensure("pymem"); ensure("capstone")
    import pymem, pymem.process
    if struct.calcsize("P") * 8 != 64: sys.exit("Use a 64-bit Python.")
    pm, exe = None, None
    for name in ("NieRAutomata.exe", "NieRAutomataCompat.exe"):
        try: pm = pymem.Pymem(name); exe = name; break
        except Exception: pass
    if pm is None: sys.exit("NieR is not running. Launch the game first.")
    mod = pymem.process.module_from_name(pm.process_handle, exe)
    base, size = mod.lpBaseOfDll, mod.SizeOfImage
    print("reading", exe, hex(base), hex(size), "...")
    img = read_image(pm, base, size)
    zs, xs = find_hits(img)
    out = ["exe: %s  base: %s  size: %s" % (exe, hex(base), hex(size)),
           "rip-relative hits  Z(%s): %d   X(%s): %d" % (Z_VAL, len(zs), X_VAL, len(xs))]
    for ins, tgt, val in zs[:10]: out.append("Z hit instr=%x const=%x value=%r" % (ins, tgt, val))
    for ins, tgt, val in xs[:10]: out.append("X hit instr=%x const=%x value=%r" % (ins, tgt, val))
    zf = aligned_float_hits(img, 493.0, 494.4)
    out.append("\nstored floats near 493.69 (rva, value): " + ", ".join("%x=%g" % h for h in zf))
    zi = imm_float_hits(img, Z_VAL, TOL)
    out.append("mov-immediate loads near 493.69: " + ", ".join("%x=%g" % h for h in zi))
    xi = imm_float_hits(img, X_VAL, TOL)
    out.append("mov-immediate loads near -665.0: " + ", ".join("%x=%g" % h for h in xi))
    for ins, tgt, val in xs[:3]:
        out.append("\n=== function containing X hit at %x ===" % ins)
        out.append(disasm_function(img, ins))
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cheat_report.txt")
    with open(path, "w") as f: f.write("\n".join(out))
    print("\n".join(out[:2])); print("saved:", path)

if __name__ == "__main__":
    main()
