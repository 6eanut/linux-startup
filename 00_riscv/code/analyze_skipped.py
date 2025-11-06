import csv
import re

def parse_config_file(config_path):
    config_map = {}
    with open(config_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                m = re.match(r"#\s*(CONFIG_[A-Za-z0-9_]+)\s+is\s+not\s+set", line)
                if m:
                    config_map[m.group(1)] = "n"
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                config_map[k.strip()] = v.strip()
    return config_map

def load_skipped_rows(skipped_csv_path):
    rows = []
    with open(skipped_csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                "file_line": row["file_line"],
                "output_lines": row.get("output_lines", ""),
                "unmet_conditions": row.get("unmet_conditions", "")
            })
    return rows

def load_fileline_output(fileline_output_csv_path):
    mapping = {}
    with open(fileline_output_csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            fl = row["file_line"]
            conds = row["output_lines"].split(";") if row["output_lines"] else []
            # 去重并清理
            cleaned = []
            seen = set()
            for c in conds:
                c = c.strip()
                if not c or "=" not in c:
                    continue
                k, v = c.split("=", 1)
                k = k.strip()
                v = v.strip()
                if (k, v) in seen:
                    continue
                seen.add((k, v))
                cleaned.append((k, v))
            mapping[fl] = cleaned
    return mapping

def compute_unmet_stats(skipped_rows):
    # 解析 "CONFIG_X=n (need y)" 形式
    unmet_re = re.compile(r"^\s*(CONFIG_[A-Za-z0-9_]+)\s*=\s*([^\s]+)\s*\(need\s*([^\s]+)\)\s*$")

    # 细粒度统计：按 (CONFIG, expected, actual)
    counts_by_cfg_expected_actual = {}
    # 聚合统计：按 (CONFIG, expected)
    counts_by_cfg_expected = {}
    # 还可以统计：按 (CONFIG, actual) 被阻止的行数
    blocked_by_actual = {}

    for row in skipped_rows:
        unmet_list = [x.strip() for x in row["unmet_conditions"].split(";") if x.strip()]
        for item in unmet_list:
            m = unmet_re.match(item)
            if not m:
                # 未能解析的格式，归类到一个保留桶
                key = ("__UNPARSEABLE__", item)
                counts_by_cfg_expected_actual[key] = counts_by_cfg_expected_actual.get(key, 0) + 1
                continue
            cfg, actual, expected = m.group(1), m.group(2), m.group(3)
            k1 = (cfg, expected, actual)
            counts_by_cfg_expected_actual[k1] = counts_by_cfg_expected_actual.get(k1, 0) + 1
            k2 = (cfg, expected)
            counts_by_cfg_expected[k2] = counts_by_cfg_expected.get(k2, 0) + 1
            k3 = (cfg, actual)
            blocked_by_actual[k3] = blocked_by_actual.get(k3, 0) + 1

    return counts_by_cfg_expected_actual, counts_by_cfg_expected, blocked_by_actual

def evaluate_line_conditions(conds, config_map, strict=True):
    """
    conds: list[(CONFIG, expected_value)]
    strict=True: 严格相等才算满足（与你原 evaluate_compilation 保持一致）
    返回 True/False
    """
    for k, expected in conds:
        actual = config_map.get(k, "n")
        if strict:
            if actual != expected:
                return False
        else:
            # 可选的宽松模式：把 m 视为“已编译”（满足 expected=y 或 expected=m）
            if expected == "y":
                if actual not in ("y", "m"):
                    return False
            elif expected == "m":
                if actual != "m":
                    return False
            else:
                if actual != expected:
                    return False
    return True

def compute_compiled_due_to_value(fileline_output_map, config_map, strict=True):
    """
    对于每个满足编译的行，把该行的每个条件 (CONFIG=VALUE) 计入其“编译贡献”。
    返回 dict[(CONFIG, VALUE)] -> compiled_line_count
    """
    compiled_due = {}
    for fl, conds in fileline_output_map.items():
        if not conds:
            continue
        if evaluate_line_conditions(conds, config_map, strict=strict):
            for k, v in conds:
                compiled_due[(k, v)] = compiled_due.get((k, v), 0) + 1
    return compiled_due

def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            w.writerow(row)

def run_stats(skipped_csv_path, fileline_output_csv_path, config_path,
              out_unmet_detail_csv="stats_unmet_detail.csv",
              out_unmet_agg_csv="stats_unmet_agg.csv",
              out_blocked_by_actual_csv="stats_blocked_by_actual.csv",
              out_compiled_due_csv="stats_compiled_due_to_value.csv",
              strict=True):
    # 加载输入
    skipped_rows = load_skipped_rows(skipped_csv_path)
    fileline_output_map = load_fileline_output(fileline_output_csv_path)
    config_map = parse_config_file(config_path)

    # 统计未满足
    counts_detail, counts_agg, blocked_by_actual = compute_unmet_stats(skipped_rows)

    # 统计“某配置值控制了多少行编进内核”
    compiled_due = compute_compiled_due_to_value(fileline_output_map, config_map, strict=strict)

    # 写出 CSV
    # 1) 细粒度：CONFIG, expected, actual, skipped_count
    rows_detail = []
    for (cfg, expected, actual), cnt in sorted(counts_detail.items(), key=lambda x: (-x[1], x[0])):
        rows_detail.append([cfg, expected, actual, cnt])
    write_csv(out_unmet_detail_csv, ["config", "expected", "actual", "skipped_count"], rows_detail)

    # 2) 聚合：CONFIG, expected, skipped_count
    rows_agg = []
    for (cfg, expected), cnt in sorted(counts_agg.items(), key=lambda x: (-x[1], x[0])):
        rows_agg.append([cfg, expected, cnt])
    write_csv(out_unmet_agg_csv, ["config", "expected", "skipped_count"], rows_agg)

    # 3) 被“实际值”阻止：CONFIG, actual, skipped_count
    rows_blocked = []
    for (cfg, actual), cnt in sorted(blocked_by_actual.items(), key=lambda x: (-x[1], x[0])):
        rows_blocked.append([cfg, actual, cnt])
    write_csv(out_blocked_by_actual_csv, ["config", "actual", "skipped_count"], rows_blocked)

    # 4) “实际值控制编译”：CONFIG, value, compiled_count
    rows_compiled_due = []
    for (cfg, val), cnt in sorted(compiled_due.items(), key=lambda x: (-x[1], x[0])):
        rows_compiled_due.append([cfg, val, cnt])
    write_csv(out_compiled_due_csv, ["config", "value", "compiled_count"], rows_compiled_due)

    # 控制台摘要
    print("[INFO] 统计完成：")
    print(f"- 未满足条件（细粒度）条目数: {len(rows_detail)}，输出: {out_unmet_detail_csv}")
    print(f"- 未满足条件（聚合）条目数: {len(rows_agg)}，输出: {out_unmet_agg_csv}")
    print(f"- 被某实际值阻止的统计条目数: {len(rows_blocked)}，输出: {out_blocked_by_actual_csv}")
    print(f"- 由某值控制编译的统计条目数: {len(rows_compiled_due)}，输出: {out_compiled_due_csv}")

if __name__ == "__main__":
    # 修改为你的文件路径
    skipped_csv = "/home/rv/mrvga/1106/skipped_lines.csv"
    fileline_output_csv = "/home/rv/mrvga/1106/fileline_output.csv"
    config_path = "/home/rv/mrvga/my-config"
    run_stats(skipped_csv, fileline_output_csv, config_path, strict=True)