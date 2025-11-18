#!/usr/bin/env python3
import argparse
import subprocess
import json
import os
import sys
import shutil
import datetime
import logging
from collections import defaultdict, deque
import re

SUSPICIOUS_NAMES = {
    # 基本类型/别名
    "bool", "void", "char", "short", "int", "long",
    "size_t", "ssize_t",
    "u8", "u16", "u32", "u64", "s8", "s16", "s32", "s64",
    "atomic_t",
    # 关键字/存储修饰
    "struct", "union", "enum",
    "static", "inline", "extern", "register",
    "const", "volatile", "signed", "unsigned",
    "typeof",
    # 其他
    "unknown"
}

FUNC_NAME_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def is_plausible_funcname(name: str) -> bool:
    # 合法的 C 标识符，且不在可疑集合里
    if not FUNC_NAME_RE.match(name or ""):
        return False
    if name in SUSPICIOUS_NAMES:
        return False
    return True

def looks_like_call(code_line: str, callee: str) -> bool:
    # 要求出现 callee( 的调用模式，避免把声明或注释当成调用
    if not code_line:
        return False
    pat = re.compile(r'\b' + re.escape(callee) + r'\s*\(')
    return pat.search(code_line) is not None

def setup_logger(log_path):
    logger = logging.getLogger("kcallers")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    ch.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def check_cmd_exists(cmd):
    return shutil.which(cmd) is not None

def ensure_cscope_db(src_dir, logger, force=False):
    out_path = os.path.join(src_dir, "cscope.out")
    if os.path.exists(out_path) and not force:
        logger.info("Found cscope database: %s", out_path)
        return True
    logger.info("Building cscope database in %s ...", src_dir)
    cmd = ["cscope", "-b", "-q", "-k", "-R"]
    try:
        subprocess.run(cmd, cwd=src_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info("cscope database built successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to build cscope database. stderr:\n%s", e.stderr)
        return False

def run_cscope_L3(src_dir, symbol, logger):
    # cscope -d -R -L3 <symbol> -> lines: "<file> <function> <line> <text>"
    cmd = ["cscope", "-d", "-R", "-L3", symbol]
    logger.debug("RUN: %s", " ".join(cmd))
    try:
        res = subprocess.run(cmd, cwd=src_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("cscope failed: %s\nstderr:\n%s", " ".join(cmd), e.stderr)
        return []
    lines = res.stdout.splitlines()
    if not lines:
        logger.debug("cscope returned 0 lines for symbol: %s", symbol)
        return []
    records = []
    logger.debug("cscope output for %s (%d lines):", symbol, len(lines))
    for line in lines:
        logger.debug("  %s", line)
        parts = line.strip().split(None, 3)
        if len(parts) < 3:
            # Unexpected; ignore
            continue
        file_path = parts[0]
        func_name = parts[1]
        try:
            lineno = int(parts[2])
        except ValueError:
            lineno = -1
        code = parts[3] if len(parts) >= 4 else ""
        # func_name is the caller function that contains a call to 'symbol'
        records.append({
            "caller": func_name,
            "callee": symbol,
            "file": file_path,
            "line": lineno,
            "code": code,
        })
    return records

def build_callers_graph(src_dir, start_symbol, logger, max_depth=None, include_regex=None, exclude_regex=None):
    import re
    inc_re = re.compile(include_regex) if include_regex else None
    exc_re = re.compile(exclude_regex) if exclude_regex else None

    # edges_details: callee -> caller -> [list of callsites]
    edges_details = defaultdict(lambda: defaultdict(list))
    # adjacency edges set for dedup
    edges_set = set()
    # nodes set
    nodes = set([start_symbol])

    # BFS upward from callee to callers
    q = deque()
    q.append((start_symbol, 0))
    visited = set()  # visited functions we have expanded (queried as callee)
    logger.info("Starting recursive search from: %s", start_symbol)

    while q:
        sym, depth = q.popleft()

        # 新增：如果当前符号本身不像函数名，跳过扩展
        if not is_plausible_funcname(sym):
            logger.warning("Skip expanding suspicious callee '%s' at depth %d (likely type/keyword from cscope misparse).", sym, depth)
            visited.add(sym)
            continue

        if sym in visited:
            continue
        visited.add(sym)

        # Depth control: expand only if under limit
        if max_depth is not None and depth >= max_depth:
            logger.info("Depth %d reached limit %d for symbol %s; stop expanding this branch.", depth, max_depth, sym)
            continue

        callers = run_cscope_L3(src_dir, sym, logger)
        if not callers:
            logger.info("No callers found for %s at depth %d.", sym, depth)
            continue

        logger.info("Found %d callers for %s at depth %d.", len(callers), sym, depth)

        accepted_callers = set()
        for rec in callers:
            caller = rec["caller"]
            code_line = rec["code"]
            file_path = rec["file"]
            lineno = rec["line"]

            # 过滤不合理的 caller 名称（例如 bool）
            if not is_plausible_funcname(caller):
                logger.warning(
                    "Discarding cscope caller '%s' for %s at %s:%s; "
                    "reason: implausible function name (likely type/keyword). Line: %s",
                    caller, sym, file_path, lineno, code_line
                )
                continue

            # 二次确认这是一个调用点：必须出现 callee(
            if not looks_like_call(code_line, sym):
                logger.warning(
                    "Discarding cscope caller '%s' for %s at %s:%s; "
                    "reason: line does not look like a call to '%s'. Line: %s",
                    caller, sym, file_path, lineno, sym, code_line
                )
                continue

            nodes.add(caller)
            edges_set.add((caller, sym))
            edges_details[sym][caller].append({
                "file": file_path,
                "line": lineno,
                "code": code_line,
            })
            accepted_callers.add(caller)

        # 只扩展通过过滤的 caller
        for c in accepted_callers:
            if c not in visited:
                q.append((c, depth + 1))

    # Build edges list with callsite counts
    edges = []
    for (caller, callee) in sorted(edges_set):
        callsites = edges_details.get(callee, {}).get(caller, [])
        edges.append({
            "caller": caller,
            "callee": callee,
            "callsites_count": len(callsites),
            "callsites": callsites,
        })

    # Node list
    nodes_list = [{"name": n, "is_start": (n == start_symbol)} for n in sorted(nodes)]

    graph = {
        "start_function": start_symbol,
        "generated_at": datetime.datetime.now().isoformat(),
        "nodes": nodes_list,
        "edges": edges,
        "note": "Edges are caller -> callee. callsites contains file:line snippets where caller invokes callee.",
    }
    return graph

def write_json(graph, out_json, logger):
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    logger.info("Wrote JSON: %s", out_json)

def graph_to_dot(graph):
    def is_syscall_macro_node(name: str) -> bool:
        # 命名里包含 SYSCALL_DEFINE 的都视作“syscall 宏定义节点”
        # 包括 SYSCALL_DEFINE0/1/… 和 COMPAT_SYSCALL_DEFINE*
        return "SYSCALL_DEFINE" in name

    node_lines = []
    edge_lines = []

    for n in graph.get("nodes", []):
        name = n["name"]
        is_start = n.get("is_start", False)
        safe = name.replace('"', r'\"')

        is_syscall = is_syscall_macro_node(name)

        if is_start and is_syscall:
            # 起点 + SYSCALL_DEFINE：双圆+蓝色填充
            node_lines.append(f'"{safe}" [shape=doublecircle, style=filled, fillcolor=lightskyblue, color=blue];')
        elif is_start:
            node_lines.append(f'"{safe}" [shape=doublecircle, style=filled, fillcolor=lightyellow, color=goldenrod];')
        elif is_syscall:
            node_lines.append(f'"{safe}" [shape=ellipse, style=filled, fillcolor=lightskyblue, color=blue];')
        else:
            node_lines.append(f'"{safe}" [shape=ellipse];')

    for e in graph.get("edges", []):
        caller = e["caller"].replace('"', r'\"')
        callee = e["callee"].replace('"', r'\"')
        label = str(e.get("callsites_count", 1))
        edge_lines.append(f'"{caller}" -> "{callee}" [label="{label}"];')

    dot = [
        "digraph Callers {",
        "  rankdir=TB;",
        "  node [fontname=Helvetica];",
        "  edge [fontname=Helvetica, arrowsize=0.7];",
    ]
    dot += ["  " + ln for ln in node_lines]
    dot += ["  " + ln for ln in edge_lines]
    dot.append("}")
    return "\n".join(dot)
def write_dot(dot_str, out_dot, logger):
    with open(out_dot, "w", encoding="utf-8") as f:
        f.write(dot_str)
    logger.info("Wrote DOT: %s", out_dot)

def render_dot(dot_path, out_img, logger):
    fmt = os.path.splitext(out_img)[1].lstrip(".").lower()
    if not check_cmd_exists("dot"):
        logger.warning("Graphviz 'dot' not found. Skipping image rendering. You can run: dot -T%s %s -o %s", fmt, dot_path, out_img)
        return False
    cmd = ["dot", f"-T{fmt}", dot_path, "-o", out_img]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info("Wrote image: %s", out_img)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("dot failed: %s\nstderr:\n%s", " ".join(cmd), e.stderr)
        return False

def main():
    ap = argparse.ArgumentParser(description="Build recursive callers graph using cscope (-L3).")
    ap.add_argument("symbol", help="Start function name (callee) to find its callers recursively.")
    ap.add_argument("-s", "--src", default=".", help="Kernel source root (where cscope.out resides). Default: current dir.")
    ap.add_argument("-o", "--out", default="out", help="Output directory. Default: ./out")
    ap.add_argument("-d", "--depth", type=int, default=None, help="Max recursion depth (0 means only direct callers). Default: unlimited.")
    ap.add_argument("--include", help="Only include callers whose name matches this regex.")
    ap.add_argument("--exclude", help="Exclude callers whose name matches this regex.")
    ap.add_argument("--rebuild-db", action="store_true", help="Force rebuild cscope database.")
    ap.add_argument("--img-format", choices=["png", "svg", "pdf"], default="png", help="Graph image format. Default: png")
    args = ap.parse_args()

    src_dir = os.path.abspath(args.src)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    log_path = os.path.join(out_dir, "analysis.log")
    logger = setup_logger(log_path)

    logger.info("Source dir: %s", src_dir)
    logger.info("Output dir: %s", out_dir)
    logger.info("Start symbol: %s", args.symbol)
    if args.depth is not None:
        logger.info("Max depth: %d", args.depth)

    if not check_cmd_exists("cscope"):
        logger.error("cscope not found. Please install it.")
        sys.exit(1)

    if not ensure_cscope_db(src_dir, logger, force=args.rebuild_db):
        sys.exit(1)

    graph = build_callers_graph(
        src_dir=src_dir,
        start_symbol=args.symbol,
        logger=logger,
        max_depth=args.depth,
        include_regex=args.include,
        exclude_regex=args.exclude,
    )

    out_json = os.path.join(out_dir, "callgraph.json")
    write_json(graph, out_json, logger)

    dot = graph_to_dot(graph)
    out_dot = os.path.join(out_dir, "callgraph.dot")
    write_dot(dot, out_dot, logger)

    out_img = os.path.join(out_dir, f"callgraph.{args.img_format}")
    render_dot(out_dot, out_img, logger)

if __name__ == "__main__":
    main()