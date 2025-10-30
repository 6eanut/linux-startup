#!/usr/bin/env bash

# set -x

# 定义源目录和目标目录
source_dir="/home/rv/mrvga/linux-6.18-rc3/arch/riscv"
target_base_dir="/home/rv/mrvga/temp"

if [[ ! -d "$source_dir" ]]; then
  echo "错误：目录不存在：$source_dir" >&2
fi

# 使用 find 找到扩展名为 .c .h .S 的文件，使用 -print0 + read -d '' 以安全处理空格和特殊字符
find "$source_dir" -type f \( -name '*.c' -o -name '*.h' -o -name '*.S' \) -print0 |
while IFS= read -r -d '' file; do
    undertaker -j coverage "$file"
done

# 创建目标基础目录
mkdir -p "$target_base_dir"

# 使用find直接处理，避免中间数组
find "$source_dir" -type f \( -name "*config[0-9]" -o -name "*config[0-9][0-9]" \) | while read -r file; do
    # 跳过空文件
    if [ ! -s "$file" ]; then
        continue
    fi
    
    # 获取相对路径和目标路径
    relative_path="${file#$source_dir/}"
    target_file="$target_base_dir/$relative_path"
    target_dir=$(dirname "$target_file")
    
    # 创建目标目录
    mkdir -p "$target_dir"
    
    # 过滤CONFIG行，并检查是否有输出
    if grep "CONFIG" "$file" > /tmp/temp_$$ 2>/dev/null && [ -s /tmp/temp_$$ ]; then
        mv /tmp/temp_$$ "$target_file"
        original_lines=$(wc -l < "$file")
        processed_lines=$(wc -l < "$target_file")
    else
        rm -f /tmp/temp_$$ 2>/dev/null
    fi
done

find "$target_base_dir" -type d -empty -delete
