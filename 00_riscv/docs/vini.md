做三件事：

* arch/riscv下有多少代码行(.c, .h, .S)；
* 这些代码行中有哪些是被配置项管理的？
  * CONFIG_XXX被设置成y/n时管理了file_XXX的第start到第end行；
* 对于.config而言，启用了多少代码行？

初代脚本在这：

* analyze_file写的有问题，导致一些不是配置项的ifdef/if也被考虑进来了，导致出现错误的结果

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 arch/riscv 下每个文件中由 CONFIG_XXX 管理的代码段，
并导出详细映射表（包含条件表达式、控制项及当前启用状态）。
"""

import os
import re
import argparse
import csv
from collections import defaultdict

# ========== 解析 .config ==========
def parse_config(path):
    config = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("CONFIG_"):
                if "=y" in line:
                    key = line.split("=")[0]
                    config[key] = "y"
                elif "=m" in line:
                    key = line.split("=")[0]
                    config[key] = "m"
                elif "is not set" in line:
                    key = line.split()[1]
                    config[key] = "n"
    return config


# ========== 遍历源码 ==========
def get_source_files(root):
    exts = (".c", ".h", ".S")
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(exts):
                files.append(os.path.join(dirpath, fn))
    return files


# ========== 分析单个文件 ==========
pattern_ifdef = re.compile(r"#\s*(if|ifdef|ifndef|elif)\b(.*)")
pattern_else = re.compile(r"#\s*else")
pattern_endif = re.compile(r"#\s*endif")
pattern_config = re.compile(r"CONFIG_[A-Z0-9_]+")

def analyze_file(path):
    managed_ranges = []
    stack = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if not line.strip().startswith("#"):
            continue

        if m := pattern_ifdef.match(line):
            directive, expr = m.groups()
            stack.append((directive, expr.strip(), i))
        elif pattern_else.match(line):
            if stack:
                directive, expr, start = stack[-1]
                managed_ranges.append((start, i - 1, expr))
                stack[-1] = ("else", f"!({expr})", i)
        elif pattern_endif.match(line):
            if stack:
                directive, expr, start = stack.pop()
                managed_ranges.append((start, i - 1, expr))
    return managed_ranges, len(lines)


# ========== 去重嵌套 ==========
def dedup_ranges(ranges):
    if not ranges:
        return []
    ranges.sort(key=lambda x: (x[0], -x[1]))
    result = []
    for r in ranges:
        if not result:
            result.append(r)
        else:
            prev = result[-1]
            if r[0] >= prev[0] and r[1] <= prev[1]:
                continue
            result.append(r)
    return result


# ========== 判断条件是否启用 ==========
def eval_expr(expr, config_dict):
    """
    简单判断条件表达式是否为真。
    支持 CONFIG_XXX / !CONFIG_XXX / && / || 结构。
    """
    expr_eval = expr
    for cfg in re.findall(pattern_config, expr):
        val = config_dict.get(cfg, "unset")
        expr_eval = expr_eval.replace(cfg, "True" if val in ("y", "m") else "False")
    expr_eval = expr_eval.replace("!", " not ").replace("&&", " and ").replace("||", " or ")
    try:
        return eval(expr_eval)
    except Exception:
        return False


# ========== 主逻辑 ==========
def main():
    parser = argparse.ArgumentParser(description="分析arch/riscv中CONFIG控制的代码段")
    parser.add_argument("--config", required=True, help=".config文件路径")
    parser.add_argument("--src", required=True, help="arch/riscv源码路径")
    parser.add_argument("--out", default="config_code_mapping.csv", help="输出文件路径")
    args = parser.parse_args()

    config_dict = parse_config(args.config)
    files = get_source_files(args.src)
    print(f"[+] Scanning {len(files)} source files...")

    total_lines = 0
    managed_lines = 0
    enabled_lines = 0
    detailed_records = []

    for f in files:
        ranges, lines = analyze_file(f)
        ranges = dedup_ranges(ranges)
        total_lines += lines

        for start, end, expr in ranges:
            configs = list(set(re.findall(pattern_config, expr)))
            config_values = [f"{c}={config_dict.get(c, 'unset')}" for c in configs]
            effective = eval_expr(expr, config_dict)

            managed_lines += (end - start + 1)
            if effective:
                enabled_lines += (end - start + 1)

            detailed_records.append({
                "File": f,
                "StartLine": start + 1,
                "EndLine": end + 1,
                "ConfigExpr": expr,
                "ConfigList": " ".join(configs),
                "ConfigValues": " ".join(config_values),
                "Effective": effective,
            })

    print("\n===== 汇总结果 =====")
    print(f"源码总行数: {total_lines}")
    print(f"被配置项管理的行数: {managed_lines}")
    print(f"当前配置启用的行数: {enabled_lines}")

    with open(args.out, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["File", "StartLine", "EndLine", "ConfigExpr",
                      "ConfigList", "ConfigValues", "Effective"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in detailed_records:
            writer.writerow(row)

    print(f"\n详细结果已保存到: {args.out}")


if __name__ == "__main__":
    main()

```

结果在这：

```shell
$ python3 1105-analyze_config_impact.py --config my-config --src linux-6.18-rc3/arch/riscv
[+] Scanning 396 source files...

===== 汇总结果 =====
源码总行数: 65151
被配置项管理的行数: 25780
当前配置启用的行数: 6694

详细结果已保存到: config_code_mapping.csv
```

表格见[这里](config_code_mapping.csv)。
