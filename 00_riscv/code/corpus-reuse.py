# collect_paths.py

import os

def load_seed_paths(corpus_info_dir: str) -> dict:
    """
    加载所有种子及其触发路径地址。
    返回字典: {seed_hash: [addr1, addr2, ...]}
    """
    seeds = {}
    for fname in os.listdir(corpus_info_dir):
        fpath = os.path.join(corpus_info_dir, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r") as f:
            addrs = [line.strip() for line in f if line.strip()]
        seeds[fname] = addrs
    return seeds


# if __name__ == "__main__":
#     corpus_info_dir = "/home/rv/fuzzer-repo/kconfigfuzz/corpus-info"
#     seeds = load_seed_paths(corpus_info_dir)
#     print(f"共加载 {len(seeds)} 个种子")

# addr2fileline.py

import os
import subprocess
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil


def addr2line_batch(vmlinux_path: str, addrs: List[str]) -> Dict[str, str]:
    """批量调用 addr2line，一次处理多个地址"""
    if not addrs:
        return {}
    cmd = ["addr2line", "-e", vmlinux_path, "-f", "-p"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, _ = proc.communicate("\n".join(addrs))
    results = stdout.strip().splitlines()
    return dict(zip(addrs, results))


def convert_seed_addrs_parallel(vmlinux_path: str, seed_addrs: Dict[str, List[str]],
                                batch_size: int = 5000, num_threads: int = 8) -> Dict[str, List[str]]:
    """
    多线程 + 批量 addr2line 解析。
    - batch_size: 每个线程一次解析的地址数
    - num_threads: 并行线程数
    """
    # 1️⃣ 收集所有唯一地址
    unique_addrs = sorted({addr for addrs in seed_addrs.values() for addr in addrs})
    print(f"[INFO] 共 {len(unique_addrs)} 个唯一地址需要解析")

    # 2️⃣ 按批切分
    batches = [unique_addrs[i:i + batch_size] for i in range(0, len(unique_addrs), batch_size)]
    print(f"[INFO] 分成 {len(batches)} 批次，每批 {batch_size} 个地址，使用 {num_threads} 线程")

    addr_map = {}
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(addr2line_batch, vmlinux_path, batch): i for i, batch in enumerate(batches)}
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                result = future.result()
                addr_map.update(result)
                print(f"  → 批次 {batch_idx+1}/{len(batches)} 完成 ({len(result)} 条)")
            except Exception as e:
                print(f"[ERROR] 批次 {batch_idx+1} 失败: {e}")

    # 3️⃣ 映射回各种子
    seed_filelines = {}
    for seed, addrs in seed_addrs.items():
        seed_filelines[seed] = [addr_map.get(a, f"UNKNOWN:{a}") for a in addrs]

    return seed_filelines


# if __name__ == "__main__":
#     vmlinux_path = "/home/rv/vmlinux"
#     seeds = load_seed_paths("/home/rv/fuzzer-repo/kconfigfuzz/corpus-info")

#     result = convert_seed_addrs_parallel(vmlinux_path, seeds,
#                                          batch_size=5000,  # 每批次5000个地址
#                                          num_threads=30)    # 8线程

#     os.makedirs("corpus-mapped", exist_ok=True)
#     for seed, filelines in result.items():
#         with open(f"corpus-mapped/{seed}", "w") as f:
#             f.write("\n".join(filelines))



import os

def seed_triggers_riscv(mapped_dir: str, seed_hash: str) -> bool:
    """
    判断一个种子是否触发了 arch/riscv 下的代码路径。
    """
    seed_path = os.path.join(mapped_dir, seed_hash)
    try:
        with open(seed_path, "r") as f:
            for line in f:
                if "arch/riscv/" in line:
                    return True
    except FileNotFoundError:
        pass
    return False


def filter_non_riscv_seeds(mapped_dir: str, output_file: str):
    """
    扫描 mapped_dir，找出未触发 arch/riscv 代码的种子，
    把它们的 hash 写入 output_file。
    """
    non_riscv_seeds = []

    for seed_hash in os.listdir(mapped_dir):
        if not os.path.isfile(os.path.join(mapped_dir, seed_hash)):
            continue

        if not seed_triggers_riscv(mapped_dir, seed_hash):
            non_riscv_seeds.append(seed_hash)

    # 写出结果
    with open(output_file, "w") as f:
        f.write("\n".join(non_riscv_seeds))

    print(f"[+] 总计 {len(non_riscv_seeds)} 个种子不触发 arch/riscv，已写入 {output_file}")


# if __name__ == "__main__":
#     mapped_dir = "corpus-mapped"
#     output_file = "non_riscv_seeds.txt"

#     filter_non_riscv_seeds(mapped_dir, output_file)


import os
import subprocess


def run_cmd(cmd: list, cwd: str = None):
    """执行命令并实时打印输出"""
    print(f"[CMD] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"命令执行失败: {' '.join(cmd)}")


def unpack_corpus(db_path: str, out_dir: str):
    """解包 syzkaller corpus 数据库"""
    os.makedirs(out_dir, exist_ok=True)
    run_cmd(["/home/rv/fuzzer-repo/kconfigfuzz/bin/syz-db", "unpack", db_path, out_dir])


def remove_unwanted_seeds(seed_dir: str, remove_list_path: str):
    """根据 hash 清单删除对应的 seed 文件"""
    with open(remove_list_path, "r") as f:
        to_remove = [line.strip() for line in f if line.strip()]
    print(f"[INFO] 需要删除 {len(to_remove)} 个无关种子")

    removed, missing = 0, 0
    for h in to_remove:
        path = os.path.join(seed_dir, h)
        if os.path.exists(path):
            os.remove(path)
            removed += 1
        else:
            missing += 1
    print(f"[INFO] 已删除 {removed} 个，未找到 {missing} 个")


def repack_corpus(seed_dir: str, new_db_path: str):
    """重新打包 corpus"""
    run_cmd(["/home/rv/fuzzer-repo/kconfigfuzz/bin/syz-db", "pack", seed_dir, new_db_path])


if __name__ == "__main__":
    old_db = "/home/rv/fuzzer-repo/kconfigfuzz/workdir/corpus.db"
    new_db = "riscv.db"
    unpack_dir = "corpus-unpacked"
    remove_list = "non_riscv_seeds.txt"

    # 步骤执行
    unpack_corpus(old_db, unpack_dir)
    remove_unwanted_seeds(unpack_dir, remove_list)
    repack_corpus(unpack_dir, new_db)

    print(f"\n✅ 清理完成，新 corpus: {new_db}")
