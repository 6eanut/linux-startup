#!/usr/bin/env python3
import json
from pathlib import Path

input_dir = Path("temp")
output_json = Path("config_map_merged.json")

elements = []

# 遍历所有 .config* 文件
for f in input_dir.rglob("*.config*"):
    relpath = f.relative_to(input_dir)
    # 文件名转换: acpi.h.config2 -> acpi.h_2
    file_tag = str(relpath).replace(".config", "_")

    # 读取配置文件，去掉空行
    with f.open() as fp:
        config_lines = [line.strip() for line in fp if line.strip()]

    elements.append({
        "config_dict": {line.split("=", 1)[0]: line.split("=", 1)[1] for line in config_lines},
        "files": set([file_tag])
    })

# 合并：完全相同或包含关系
to_remove = set()
for i, e1 in enumerate(elements):
    for j, e2 in enumerate(elements):
        if i == j or j in to_remove:
            continue
        # 如果 e2 配置包含 e1 配置，则 e1 文件并入 e2
        if all(k in e2["config_dict"] and e2["config_dict"][k] == v
               for k, v in e1["config_dict"].items()):
            e2["files"].update(e1["files"])
            to_remove.add(i)

# 删除被合并的子集元素
elements = [e for idx, e in enumerate(elements) if idx not in to_remove]

# 去重并格式化输出 JSON
output_list = []
seen_configs = set()
for e in elements:
    config_array = [f"{k}={v}" for k, v in e["config_dict"].items()]
    key = tuple(sorted(config_array))
    if key not in seen_configs:
        output_list.append({
            "config": config_array,
            "files": sorted(e["files"])
        })
        seen_configs.add(key)

# 写入 JSON
with output_json.open("w") as f:
    json.dump(output_list, f, indent=2)

print(f"总配置组合数量: {len(output_list)}")