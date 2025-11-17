# HowToSubmitABug

https://llvm.org/docs/HowToSubmitABug.html

# 如何提交 LLVM 错误报告

## 引言 - 遇到错误了？

如果你在使用 LLVM 时遇到错误，我们非常希望了解相关情况。本文档将说明你可以采取哪些措施，以提高错误被快速修复的概率。

🔒 如果你认为该错误与安全相关，请遵循《如何报告安全问题？》的指引。🔒

你至少需要完成两件事。首先，判断错误是导致编译器崩溃，还是编译器编译程序出错（即编译器成功生成可执行文件，但运行结果不符合预期）。根据错误类型，按照相关章节的说明缩小错误范围，让修复者能更轻松地定位问题。

一旦你获得了简化的测试用例，请前往 LLVM 错误跟踪系统，填写表单并提供必要详情（注意：若不确定，无需选择标签，直接提交即可）。错误描述应包含以下信息：

- 重现问题所需的所有信息。
- 触发错误的简化测试用例。
- 你获取 LLVM 的来源（若并非来自我们的 Git 仓库）。

感谢你帮助我们完善 LLVM！

---

## 崩溃类错误

编译器中的错误通常会导致其崩溃——这往往是由某种断言失败引起的。关键是要确定崩溃发生在 Clang 前端，还是 LLVM 某个库（如优化器或代码生成器）中。

要判断崩溃的组件（前端、中端优化器或后端代码生成器），请按崩溃发生时的方式运行 `clang` 命令，并添加以下额外命令行选项：

- `emit-llvm -Xclang -disable-llvm-passes`：若添加这些选项（禁用优化器和代码生成器）后 `clang` 仍崩溃，则崩溃发生在前端。请直接查看“前端错误”章节。
- `emit-llvm`：若添加此选项（禁用代码生成器）后 `clang` 崩溃，则你遇到的是中端优化器错误。请直接查看“中端错误”章节。
- 若上述两种情况均不成立，则为后端代码生成器崩溃。请直接查看“代码生成器错误”章节。

### 前端错误

当 `clang` 崩溃时，编译器会生成预处理文件和一个用于重现 `clang` 命令的脚本。例如，你会看到类似以下的提示：

**请将以下文件附加到错误报告中：**
预处理源文件及相关运行脚本位于：
clang: 注意：诊断信息：/tmp/foo-xxxxxx.c
clang: 注意：诊断信息：/tmp/foo-xxxxxx.sh

creduce 工具可帮助将预处理文件简化为仍能复现问题的最小代码量。建议你使用 creduce 进行代码简化，为开发者提供便利。你可以使用 `clang/utils/creduce-clang-crash.py` 脚本处理 clang 生成的文件，自动创建用于检查编译器崩溃的测试用例。

cvise 是 `creduce` 的替代工具。

### 中端优化器错误

若确定错误导致优化器崩溃，请通过以下命令将测试用例编译为 `.bc` 文件：`-emit-llvm -O1 -Xclang-disable-llvm-passes -c -o foo.bc`。其中 `-O1` 至关重要，因为 `-O0` 会为所有函数添加 `optnone` 属性，而许多优化过程不会作用于带有 `optnone` 属性的函数。之后运行：

`opt -O3 foo.bc -disable-output`

- 若未崩溃，请遵循“前端错误”章节的说明操作。
- 若发生崩溃，可通过以下 bugpoint 命令进行调试：`bugpoint foo.bc -O3`

运行该命令后，提交错误报告，并附上 bugpoint 生成的操作说明和简化后的 `.bc` 文件。

若 bugpoint 无法复现崩溃，`llvm-reduce` 是另一种简化 LLVM IR 的工具。创建一个能复现崩溃的脚本，然后运行：

`llvm-reduce --test=path/to/script foo.bc`

该命令会生成仍能复现崩溃的简化 IR。请注意，`llvm-reduce` 目前尚不成熟，可能会出现崩溃情况。

若上述方法均无效，可在运行 `opt` 命令时添加 `--print-before-all --print-module-scope` 选项，在每个优化过程前导出 IR，从而获取崩溃前的 IR。请注意，该操作会产生大量输出信息。

### 后端代码生成器错误

若确定错误导致代码生成器崩溃，请在原有编译选项的基础上，添加 `-emit-llvm -c -o foo.bc` 选项，将源文件编译为 `.bc` 文件。获得 foo.bc 后，以下命令中应有一个会执行失败：

- `llc foo.bc`
- `llc foo.bc -relocation-model=pic`
- `llc foo.bc -relocation-model=static`
- 若均未崩溃，请遵循“前端错误”章节的说明操作。
- 若其中某个命令崩溃，可通过以下对应的 bugpoint 命令进行简化（选择与失败命令对应的选项）：

  - `bugpoint -run-llc foo.bc`
  - `bugpoint -run-llc foo.bc --tool-args-relocation-model=pic`
  - `bugpoint -run-llc foo.bc --tool-args-relocation-model=static`

运行命令后，提交错误报告，并附上 bugpoint 生成的操作说明和简化后的 `.bc` 文件。若 bugpoint 运行异常，请提交 “foo.bc” 文件以及导致 llc 崩溃的选项。

### LTO 错误

若使用 `-flto` 选项时，在 LLVM LTO 阶段遇到崩溃错误，请按以下步骤诊断并报告问题：

在原有编译选项的基础上，添加以下选项将源文件编译为 `.bc`（位码）文件：
`export CFLAGS="-flto -fuse-ld=lld" CXXFLAGS="-flto -fuse-ld=lld" LDFLAGS="-Wl,-plugin-opt=save-temps"`

这些选项会启用 LTO，并保存编译过程中生成的临时文件，以便后续分析。

在 Windows 系统中，应使用 lld-link 作为链接器。请调整编译选项如下：

- 向链接器选项添加 `/lldsavetemps`。
- 若通过编译器驱动程序链接，需添加 `/link /lldsavetemps`，将该选项传递给链接器。

使用上述指定选项会生成四个中间位码文件：

- a.out.0.0.preopt.bc（应用任何链接时优化（LTO）之前）
- a.out.0.2.internalize.bc（应用初始优化之后）
- a.out.0.4.opt.bc（应用一系列深度优化之后）
- a.out.0.5.precodegen.bc（LTO 完成但尚未转换为机器码之前）

运行以下命令之一，定位问题来源：

- `opt "-passes=lto<O3>" a.out.0.2.internalize.bc`
- `llc a.out.0.5.precodegen.bc`

若其中某个命令崩溃，可通过以下 llvm-reduce 命令进行简化（使用与失败命令对应的 bc 文件）：
`llvm-reduce --test reduce.sh a.out.0.2.internalize.bc`

#### reduce.sh 脚本示例

```bash
#!/bin/bash -e
path/to/not --crash path/to/opt "-passes=lto<O3>" $1 -o temp.bc  2> err.log
grep -q "It->second == &Insn" err.log
```

上述脚本中，我们过滤了失败的断言信息。

运行命令后，提交错误报告，并附上 llvm-reduce 生成的操作说明和简化后的 `.bc` 文件。

---

## 编译错误

若 clang 成功生成可执行文件，但运行结果不符合预期，可能是程序本身存在错误，也可能是编译器存在错误。首先需要确认问题并非由未定义行为导致（例如读取未初始化的变量）。尤其要检查程序在各类 sanitizer（如 `clang-fsanitize=undefined,address`）和 valgrind 工具下是否能正常运行。我们追踪的许多“LLVM 错误”，最终被证实是待编译程序自身的问题，而非 LLVM 的错误。

一旦确定程序本身无错，你需要选择编译程序所用的代码生成器（如 LLC 或 JIT），并可选择一系列要运行的 LLVM 优化过程。例如：

`bugpoint -run-llc [... 优化过程 ...] file-to-test.bc --args -- [程序参数]`

bugpoint 会尝试将优化过程列表缩小到导致错误的单个过程，并尽可能简化位码文件，为你提供帮助。它会输出一条信息，说明如何重现最终发现的错误。

OptBisect 页面提供了另一种查找异常优化过程的方法。

### 错误代码生成

与调试由异常优化过程导致的编译错误类似，你可以使用 `bugpoint` 调试由 LLC 或 JIT 导致的错误代码生成问题。在这种情况下，`bugpoint` 的工作流程是尝试将代码缩小到一个被其中一种方式错误编译的函数。但为保证正确性，必须运行整个程序，因此 `bugpoint` 会使用 C 后端编译它认为不受影响的代码，然后链接生成的共享对象。

#### 调试 JIT：

```bash
bugpoint -run-jit -output=[正确输出文件] [位码文件]  \
         --tool-args -- [传递给 lli 的参数]              \
         --args -- [程序参数]
```

#### 调试 LLC：

```bash
bugpoint -run-llc -output=[正确输出文件] [位码文件]  \
         --tool-args -- [传递给 llc 的参数]              \
         --args -- [程序参数]
```

#### 特别说明：

若你正在调试 `llvm/test` 目录下已存在的 MultiSource 或 SPEC 测试用例，有一种更简便的方法可调试 JIT、LLC 和 CBE。使用预定义的 Makefile 目标，它会传递 Makefile 中指定的程序选项：

```bash
cd llvm/test/../../program
make bugpoint-jit
```

`bugpoint` 运行成功后，会生成两个位码文件：一个安全文件（可通过 C 后端编译）和一个测试文件（LLC 或 JIT 对其进行了错误的代码生成，从而导致错误）。

要重现 `bugpoint` 发现的错误，只需执行以下步骤：

1. 从安全位码文件重新生成共享对象：

```bash
llc -march=c safe.bc -o safe.c
gcc -shared safe.c -o safe.so
```

2. 若调试 LLC，将测试位码编译为本地代码并链接共享对象：

```bash
llc test.bc -o test.s
gcc test.s safe.so -o test.llc
./test.llc [程序选项]
```

3. 若调试 JIT，加载共享对象并提供测试位码：

```bash
lli -load=safe.so test.bc [程序选项]
```
