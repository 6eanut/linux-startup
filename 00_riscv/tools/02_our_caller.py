#!/usr/bin/env python3
"""
内核函数调用链分析工具
用于查找两个函数的调用链,并找出它们的共同调用者
"""

import subprocess
import sys
import re
from collections import defaultdict, deque

class CallChainAnalyzer:
    def __init__(self, max_depth=10):
        self.max_depth = max_depth
        self.call_graph = defaultdict(set)  # caller -> set of callees
        self.visited = set()
        
    def get_callers(self, function_name):
        """使用cscope查找调用指定函数的所有函数"""
        try:
            # -d: 不重新生成数据库
            # -L: 行模式查找
            # -3: 查找调用此函数的函数
            cmd = ['cscope', '-d', '-L', '-3', function_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            callers = set()
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                # 解析cscope输出: filename function_name line_number code
                parts = line.split(maxsplit=3)
                if len(parts) >= 2:
                    caller = parts[1]
                    # 过滤掉<global>等特殊标记
                    if caller != '<global>' and caller != function_name:
                        callers.add(caller)
            
            return callers
        except subprocess.TimeoutExpired:
            print(f"警告: 查询 {function_name} 超时", file=sys.stderr)
            return set()
        except Exception as e:
            print(f"错误: 查询 {function_name} 失败: {e}", file=sys.stderr)
            return set()
    
    def build_call_chain(self, target_function, current_depth=0):
        """递归构建调用链"""
        if current_depth >= self.max_depth:
            return
        
        if target_function in self.visited:
            return
        
        self.visited.add(target_function)
        print(f"{'  ' * current_depth}正在分析: {target_function} (深度: {current_depth})")
        
        callers = self.get_callers(target_function)
        
        for caller in callers:
            self.call_graph[caller].add(target_function)
            self.build_call_chain(caller, current_depth + 1)
    
    def get_all_callers(self, function_name):
        """获取所有调用指定函数的函数(包括间接调用)"""
        all_callers = set()
        
        def dfs(func):
            for caller, callees in self.call_graph.items():
                if func in callees and caller not in all_callers:
                    all_callers.add(caller)
                    dfs(caller)
        
        dfs(function_name)
        return all_callers
    
    def find_call_paths(self, start_func, target_func, max_paths=10):
        """查找从start_func到target_func的调用路径"""
        paths = []
        queue = deque([([start_func], {start_func})])
        
        while queue and len(paths) < max_paths:
            path, visited = queue.popleft()
            current = path[-1]
            
            if current == target_func:
                paths.append(path)
                continue
            
            if len(path) >= self.max_depth:
                continue
            
            # 查找current调用的函数
            for caller, callees in self.call_graph.items():
                if current == caller:
                    for callee in callees:
                        if callee not in visited:
                            new_visited = visited.copy()
                            new_visited.add(callee)
                            queue.append((path + [callee], new_visited))
        
        return paths

def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <函数1> <函数2>")
        print(f"示例: {sys.argv[0]} packet_pick_tx_queue some_other_function")
        sys.exit(1)
    
    func1 = sys.argv[1]
    func2 = sys.argv[2]
    
    print("=" * 80)
    print(f"分析函数调用链: {func1} 和 {func2}")
    print("=" * 80)
    
    # 分析第一个函数
    print(f"\n>>> 构建 {func1} 的调用链...")
    analyzer1 = CallChainAnalyzer(max_depth=8)
    analyzer1.build_call_chain(func1)
    callers1 = analyzer1.get_all_callers(func1)
    
    print(f"\n>>> 构建 {func2} 的调用链...")
    analyzer2 = CallChainAnalyzer(max_depth=8)
    analyzer2.build_call_chain(func2)
    callers2 = analyzer2.get_all_callers(func2)
    
    # 找出共同的调用者
    common_callers = callers1.intersection(callers2)
    
    print("\n" + "=" * 80)
    print("分析结果")
    print("=" * 80)
    
    print(f"\n{func1} 的调用者数量: {len(callers1)}")
    print(f"{func2} 的调用者数量: {len(callers2)}")
    print(f"共同调用者数量: {len(common_callers)}")
    
    if common_callers:
        print(f"\n共同调用者列表 (可能先后调用 {func1} 和 {func2}):")
        for i, caller in enumerate(sorted(common_callers), 1):
            print(f"  {i}. {caller}")
        
        # 对每个共同调用者,尝试找出调用路径
        print(f"\n详细调用路径:")
        for caller in sorted(list(common_callers)[:5]):  # 只显示前5个
            print(f"\n  [{caller}]")
            
            # 找到从caller到func1的路径
            paths1 = analyzer1.find_call_paths(caller, func1, max_paths=3)
            if paths1:
                print(f"    到 {func1} 的路径:")
                for path in paths1[:2]:
                    print(f"      {' -> '.join(path)}")
            
            # 找到从caller到func2的路径
            paths2 = analyzer2.find_call_paths(caller, func2, max_paths=3)
            if paths2:
                print(f"    到 {func2} 的路径:")
                for path in paths2[:2]:
                    print(f"      {' -> '.join(path)}")
    else:
        print(f"\n未找到共同调用者")
        print(f"这两个函数可能没有被同一个函数直接或间接调用")
    
    # 显示部分调用者示例
    if callers1:
        print(f"\n{func1} 的部分调用者示例:")
        for caller in sorted(list(callers1)[:10]):
            print(f"  - {caller}")
    
    if callers2:
        print(f"\n{func2} 的部分调用者示例:")
        for caller in sorted(list(callers2)[:10]):
            print(f"  - {caller}")

if __name__ == '__main__':
    main()
