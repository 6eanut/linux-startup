[https://lwn.net/ml/all/20250901164212.460229-6-ethan.w.s.graham@gmail.com/](https://lwn.net/ml/all/20250901164212.460229-6-ethan.w.s.graham@gmail.com/)

# 内核模糊测试框架（KFuzzTest）

## 概述

内核模糊测试框架（KFuzzTest）旨在将内核内部函数暴露给用户态模糊测试引擎。

该框架适用于测试无状态或低状态函数，这类函数难以通过系统调用接口访问，例如文件格式解析或复杂数据转换相关的例程。它提供了一种内核代码原位模糊测试方法，无需将代码构建为独立的用户态库，也无需对其依赖项进行桩处理。

框架包含四个主要组件：

1. 基于 `FUZZ_TEST` 宏的API，用于直接在内核源码树中定义测试目标。
2. 二进制序列化格式，用于将复杂的、含指针的数据结构从用户态传递到内核态。
3. `debugfs` 接口，用户态模糊测试器通过该接口提交序列化测试输入。
4. 嵌入在 `vmlinux` 二进制文件专用ELF段中的元数据，供外部工具发现可用的模糊测试目标。

> **警告**：KFuzzTest 是调试和测试工具。它将内核内部函数暴露给用户态，仅进行最少的校验，仅适用于受控测试环境。**绝不能**在生产内核中启用。

## 支持的架构

KFuzzTest 目前仅支持 x86_64 架构。

## 用法

要启用 KFuzzTest，需在配置内核时设置：

```bash
CONFIG_KFUZZTEST=y
```

该配置依赖 `CONFIG_DEBUGFS`（用于接收用户态输入）和 `CONFIG_DEBUG_KERNEL`（作为额外防护，防止 KFuzzTest 意外进入生产构建）。

可通过 `CONFIG_SAMPLE_KFUZZTEST` 启用 KFuzzTest 示例模糊测试目标的构建。

KFuzzTest 目前仅支持内置到内核的代码，因为核心模块在启动过程中会从专用ELF段中发现模糊测试目标、约束和注解。

### 声明 KFuzzTest 目标

模糊测试目标直接在 `.c` 文件中定义，通常与被测试函数位于同一文件。该过程主要包括三部分：定义输入结构、使用 `FUZZ_TEST` 宏编写测试主体，以及（可选）为模糊测试器添加元数据。

以下示例展示了如何为函数 `int process_data(const char *data, size_t len)` 创建模糊测试目标：

```c
/*
 * 1. 定义一个结构体，用于建模被测试函数的输入。
 *    每个字段对应函数所需的一个参数。
 */
struct process_data_inputs {
    const char *data;
    size_t len;
};

/*
 * 2. 使用 FUZZ_TEST 宏定义模糊测试目标。
 *    第一个参数是目标的唯一名称。
 *    第二个参数是上面定义的输入结构体。
 */
FUZZ_TEST(test_process_data, struct process_data_inputs)
{
    /*
     * 在此主体中，'arg' 变量是指向完全初始化的 'struct process_data_inputs' 的指针。
     */

    /*
     * 3.（可选）添加约束以定义前置条件。
     *    此检查确保 'arg->data' 不为 NULL。如果条件不满足，测试将提前退出。
     *    这也会创建元数据以告知模糊测试器。
     */
    KFUZZTEST_EXPECT_NOT_NULL(process_data_inputs, data);

    /*
     * 4.（可选）添加注解以提供语义提示。
     *    此注解告知模糊测试器 'len' 字段是 'data' 指向的缓冲区的长度。
     *    注解不会添加任何运行时检查。
     */
    KFUZZTEST_ANNOTATE_LEN(process_data_inputs, len, data);

    /*
     * 5. 使用提供的输入调用内核函数。
     *    内存错误（如对 'arg->data' 的越界访问）将被 KASAN 或其他内存错误检测工具捕获。
     */
    process_data(arg->data, arg->len);
}
```

KFuzzTest 提供两类宏以提升模糊测试质量：

- `KFUZZTEST_EXPECT_*`：这类宏定义约束，即测试继续执行必须满足的前置条件。内核会通过运行时检查强制执行这些约束。如果检查失败，当前测试运行将中止。该元数据帮助用户态模糊测试器避免生成无效输入。
- `KFUZZTEST_ANNOTATE_*`：这类宏定义注解，仅作为模糊测试器的语义提示。它们不添加任何运行时检查，仅用于帮助模糊测试器生成更智能、结构正确的输入。例如，KFUZZTEST_ANNOTATE_LEN 将大小字段与指针字段关联，这是 C 语言 API 中的常见模式。

### 元数据

`FUZZ_TEST`、`KFUZZTEST_EXPECT_*` 和 `KFUZZTEST_ANNOTATE_*` 宏将元数据分别嵌入到最终 `vmlinux` 二进制文件主 `.data` 段内的多个专用段中：`.kfuzztest_target`、`.kfuzztest_constraint` 和 `.kfuzztest_annotation`。

元数据的作用有两点：

1. 核心模块在启动时使用 `.kfuzztest_target` 段发现所有 `FUZZ_TEST` 实例，并创建对应的 `debugfs` 目录和 `input` 文件。
2. 用户态模糊测试器可从 `vmlinux` 二进制文件中读取该元数据，发现测试目标并了解其规则和结构，从而生成正确有效的输入。

`.kfuzztest_*` 段中的元数据由固定大小的 C 结构体数组组成（例如 `struct kfuzztest_target`）。这些结构体中诸如 `name` 或 `arg_type_name` 等指针字段存储的地址指向 `vmlinux` 二进制文件中的其他位置。解析 ELF 文件的用户态工具必须解析这些指针才能读取其引用的数据。例如，要获取目标名称，工具需执行以下步骤：

1. 从 `.kfuzztest_target` 段读取 `struct kfuzztest_target`。
2. 读取 `.name` 字段中的地址。
3. 使用该地址在二进制文件的其他位置（如 `.rodata`）定位并读取以空字符结尾的字符串。

### 工具依赖

为使用户态工具能够解析 `vmlinux` 二进制文件并利用 KFuzzTest 输出的元数据，内核必须编译时包含 DWARF 调试信息。这是工具理解 C 结构体布局、解析类型信息以及正确解释约束和注解的必要条件。

当 KFuzzTest 与自动化模糊测试工具配合使用时，应启用 `CONFIG_DEBUG_INFO_DWARF4` 或 `CONFIG_DEBUG_INFO_DWARF5`。

## 输入格式

KFuzzTest 目标通过向专用 `debugfs` 文件 `/sys/kernel/debug/kfuzztest/<test-name>/input` 写入数据，接收来自用户态的输入。

写入该文件的数据必须是单个二进制块，且遵循特定的序列化格式。该格式设计用于在扁平缓冲区中表示复杂的、含指针的 C 结构体，仅需一次从用户态到内核态的内存分配和复制操作。

输入数据首先以 8 字节头部为前缀，前四个字节为魔数（在 `<include/linux/kfuzztest.h>` 中定义为 `KFUZZTEST_HEADER_MAGIC`），后四个字节为版本号。

### 版本 0

在版本 0（即 8 字节头部中的版本号为 0）中，输入格式由三个主要部分按顺序组成：区域数组、重定位表和有效载荷。

```
+----------------+---------------------+-----------+----------------+
|  区域数组       |  重定位表           |  填充     |  有效载荷      |
+----------------+---------------------+-----------+----------------+
```

#### 区域数组

该组件是一个头部，描述有效载荷中的原始数据如何划分为逻辑内存区域。它包含区域计数，后跟 `struct reloc_region` 数组，每个条目定义一个区域，包含其大小和相对于有效载荷起始位置的偏移量。

```c
struct reloc_region {
    uint32_t offset;
    uint32_t size;
};

struct reloc_region_array {
    uint32_t num_regions;
    struct reloc_region regions[];
};
```

按照惯例，区域 0 表示作为参数传递给 `FUZZ_TEST` 主体的顶层输入结构体。后续区域通常表示该结构体字段所指向的数据缓冲区。区域数组条目必须按偏移量升序排列，且不得相互重叠。

为满足 C 语言对齐要求并防止潜在的硬件错误，每个区域数据的内存地址必须与其表示的类型正确对齐。框架会分配一个适用于任何 C 类型对齐要求的基础缓冲区。因此，生成输入的用户态工具负责计算有效载荷中每个区域的偏移量，以确保满足该对齐要求。

#### 重定位表

重定位表提供内核“激活”有效载荷的指令，即修补指针字段。它包含 `struct reloc_entry` 项数组。每个条目作为链接指令，指定：

- 需要修补的指针位置（通过区域 ID 和该区域内的偏移量标识）。
- 指针应指向的目标区域（通过目标区域 ID 标识）；若指针为 `NULL`，则使用 `KFUZZTEST_REGIONID_NULL`。

该表还指定其末尾与有效载荷起始位置之间的填充大小，该大小至少为 8 字节。

```c
struct reloc_entry {
    uint32_t region_id;
    uint32_t region_offset;
    uint32_t value;
};

struct reloc_table {
    uint32_t num_entries;
    uint32_t padding_size;
    struct reloc_entry entries[];
};
```

#### 有效载荷

有效载荷包含所有区域的原始二进制数据，按其指定的偏移量拼接在一起。

- 对齐：有效载荷的起始位置必须按其所有组成区域中最严格的对齐要求对齐。框架确保有效载荷内的每个区域都放置在满足其自身类型对齐要求的偏移量处。
- 填充与毒化：一个区域数据的末尾与下一个区域数据的起始位置之间的空间必须足够用于填充。在启用 KASAN 的构建中，KFuzzTest 会对这些未使用的填充区域进行毒化处理，以便精确检测相邻缓冲区之间的越界内存访问。该填充大小至少应等于 `<include/linux/kfuzztest.h>` 中定义的 `KFUZZTEST_POISON_SIZE` 字节。

## KFuzzTest 桥接工具

kfuzztest-bridge 程序是一款用户态工具，用于将随机字节流编码为 KFuzzTest 测试 harness 所需的结构化二进制格式。它允许用户以文本形式描述目标的输入结构，便于执行冒烟测试或将测试 harness 与基于二进制块的模糊测试引擎对接。

该工具设计简洁（无论是用法还是实现），其结构和领域特定语言（DSL）适用于较简单的使用场景。对于更高级的覆盖率引导模糊测试，建议使用 syzkaller，它对 KFuzzTest 目标提供更深入的支持。

### 用法

可通过 `make tools/kfuzztest-bridge` 构建该工具。若存在 libc 兼容性问题，可能需要在目标系统上构建该工具。

示例：

```bash
./kfuzztest-bridge \
    "foo { u32 ptr[bar] }; bar { ptr[data] len[data, u64]}; data { arr[u8, 42] };" \
    "my-fuzz-target" /dev/urandom
```

该命令接受三个参数：

1. 描述输入结构的字符串（见“文本格式”小节）。
2. 目标测试的名称，对应其在 `/sys/kernel/debug/kfuzztest/` 中的目录。
3. 提供随机数据流的文件路径，例如 `/dev/urandom`。

示例中的结构字符串对应以下 C 数据结构：

```c
struct foo {
    u32 a;
    struct bar *b;
};

struct bar {
    struct data *d;
    u64 data_len; /* 等于 42。 */
};

struct data {
    char arr[42];
};
```

### 文本格式

文本格式是 KFuzzTest 所用基于区域的二进制格式的人类可读表示形式，其语法定义如下：

```text
schema     ::= region ( ";" region )* [";"]
region     ::= identifier "{" type+ "}"
type       ::= primitive | pointer | array | length | string
primitive  ::= "u8" | "u16" | "u32" | "u64"
pointer    ::= "ptr" "[" identifier "]"
array      ::= "arr" "[" primitive "," integer "]"
length     ::= "len" "[" identifier "," primitive "]"
string     ::= "str" "[" integer "]"
identifier ::= [a-zA-Z_][a-zA-Z1-9_]*
integer    ::= [0-9]+
```

指针必须引用命名区域。要对原始缓冲区进行模糊测试，该缓冲区必须在其自身的区域中定义，如下所示：

```c
struct my_struct {
    char *buf;
    size_t buflen;
};
```

对应的文本描述如下：

```text
my_struct { ptr[buf] len[buf, u64] }; buf { arr[u8, n] };
```

其中 `n` 是定义 `buf` 区域内字节数组大小的整数。
