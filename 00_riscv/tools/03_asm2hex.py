#!/usr/bin/env python3
import subprocess
import sys
import tempfile
import os
import re

if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} input.s")
    sys.exit(1)

input_asm = sys.argv[1]

AS = "riscv64-unknown-linux-gnu-as"
OBJDUMP = "riscv64-unknown-linux-gnu-objdump"

with tempfile.TemporaryDirectory() as tmp:
    asm_file = os.path.join(tmp, "code.S")
    obj_file = os.path.join(tmp, "code.o")

    # 1. 生成最小汇编
    with open(input_asm) as f:
        insns = f.read()

    with open(asm_file, "w") as f:
        f.write(
            ".option norvc\n"
            ".text\n"
            ".globl _start\n"
            "_start:\n"
        )
        for line in insns.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                f.write("    " + line + "\n")

    # 2. 汇编
    subprocess.check_call([AS, asm_file, "-o", obj_file])

    # 3. objdump
    dump = subprocess.check_output(
        [OBJDUMP, "-d", obj_file],
        text=True
    )

# 4. 解析 objdump
code_hex = []
mapping = []

for line in dump.splitlines():
    # 形如:
    #  0000000000000000: ffffffff  .word 0xffffffff
    m = re.match(r"\s*[0-9a-f]+:\s+([0-9a-f]{8})\s+(.*)", line)
    if not m:
        continue

    hexcode = m.group(1)
    asm = m.group(2).strip()

    code_hex.append(hexcode)
    mapping.append(f"{hexcode}    {asm}")

# 5. 输出文件
with open("code.bin", "w") as f:
    for h in code_hex:
        f.write(h + "\n")

with open("map.txt", "w") as f:
    for m in mapping:
        f.write(m + "\n")

print("Generated:")
print("  code.bin   (one instruction per line, hex)")
print("  map.txt    (hex <-> asm mapping)")
