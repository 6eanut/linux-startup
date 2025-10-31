#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict, Counter

# 输入 JSON 文件
input_json = Path("/home/rv/mrvga/config_map_merged.json")
output_csv = Path("/home/rv/mrvga/config_items_stats.csv")

# 用于统计配置项及取值出现次数
counter = Counter()
# 用于记录每个配置项出现过的取值
value_map = defaultdict(set)

with input_json.open() as f:
    data = json.load(f)
    for item in data:
        for cfg in item.get("config", []):
            cfg = cfg.strip()
            if '=' in cfg:
                key, value = cfg.split('=', 1)
                if value == 'm':  # 将 m 当作 y
                    value = 'y'
                counter[(key, value)] += 1
                value_map[key].add(value)

# 按配置名排序
sorted_keys = sorted(value_map.keys())

# 写入 CSV 文件
with output_csv.open('w') as f:
    f.write("Config,Count,Type\n")
    for key in sorted_keys:
        values = value_map[key]
        total_count = sum(counter[(key, val)] for val in values)
        if 'y' in values and 'n' in values:
            type_str = 'all'
        elif 'y' in values:
            type_str = 'y'
        else:
            type_str = 'n'
        f.write(f"{key},{total_count},{type_str}\n")

print(f"✅ 完成统计，总共 {len(sorted_keys)} 个配置项")
print(f"结果已保存到: {output_csv}")
