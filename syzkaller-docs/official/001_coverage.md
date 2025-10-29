https://github.com/google/syzkaller/blob/master/docs/coverage.md

# 覆盖率

`syzkaller` 采用 [ sanitizer 覆盖率（追踪模式）](https://clang.llvm.org/docs/SanitizerCoverage.html#tracing-pcs) 和 [KCOV](https://www.kernel.org/doc/html/latest/dev-tools/kcov.html) 收集覆盖率数据。sanitizer 覆盖率也支持 `gcc` 编译器，KCOV 则兼容部分其他操作系统。注：gVisor 的覆盖率实现完全不同。

覆盖率基于编译器在目标代码中插入的「覆盖率探测点」实现。覆盖率探测点通常对应代码的 [基本块](https://en.wikipedia.org/wiki/Basic_block) 或 [控制流图边（CFG edge）](https://en.wikipedia.org/wiki/Control-flow_graph)——具体取决于编译时使用的编译器和插桩模式。例如 Linux 系统搭配 clang 时，默认模式为控制流图边；搭配 gcc 时，默认模式为基本块。需要注意的是，覆盖率探测点由编译器在中端阶段插入，而此阶段已完成大量代码转换和优化过程。因此，最终的覆盖率数据可能与源代码关联性较弱。比如，可能出现未覆盖行之后紧跟已覆盖行的情况，或者在预期应有探测点的位置未发现探测点（反之亦然）——这可能是由于编译器拆分了基本块，或通过条件移动指令替代了控制流结构等原因导致。尽管如此，覆盖率评估仍具有重要实用价值，可帮助了解模糊测试的整体进度，但使用时需理性看待其局限性。

Linux 内核相关的覆盖率详情可参考 [此处](linux/coverage.md)。

## 网页界面

点击 `cover` 链接后，将显示内核构建目录下的所有目录。每个目录会标注覆盖率百分比（格式为 `X% of N`）或 `---`。`X% of N` 表示当前已覆盖 N 个探测点中的 X%；`---` 表示该目录暂无任何覆盖率数据。

点击目录可查看其中的文件及子目录，每个源代码文件同样会标注覆盖率百分比或 `---`。

点击任意 C 语言文件，将进入源代码视图。该视图采用特定颜色标识覆盖率状态，颜色定义可参考 [coverTemplate](/pkg/cover/report.go#L504)，具体说明如下：

点击任意文件的覆盖率百分比，可查看该文件中每个函数的覆盖率详情。

### 已覆盖：黑色（#000000）

该行关联的所有程序计数器（PC）值均已被覆盖。左侧数字表示触发该行 PC 值执行的测试用例数量，点击该数字可打开最后一次执行的测试用例。下图展示了完全覆盖的代码行样式：

![代码行完全覆盖](coverage_covered.png?raw=true)

### 部分覆盖：橙色（#c86400）

该行关联多个 PC 值，但并非全部被执行。源代码行左侧同样有可点击的数字，点击后可打开触发对应 PC 值的最新测试用例。下图展示了部分覆盖的代码行样式：

![代码行包含已执行和未执行的 PC 值](coverage_both.png?raw=true)

### 弱未覆盖：深红色（#c80000）

该行所在的函数（符号）未获得任何覆盖率，即该函数从未被执行。需注意，若编译器将某个符号优化内联，该行代码实际会编译到其他符号中，这可能导致颜色标识的含义难以判断。下图展示了弱未覆盖的代码行样式（该行关联的 PC 值所在函数均未执行）：

![该行关联的 PC 值未执行，且其所在函数也未执行](coverage_weak-uncovered.png?raw=true)

### 未覆盖：红色（#ff0000）

该行未被覆盖，但所在函数（符号）已被执行，且该行关联的 PC 值属于该函数。下图展示了未覆盖的代码行样式：

![该行关联的 PC 值均未执行，但所在函数已执行](coverage_uncovered.png?raw=true)

### 未插桩：灰色（#505050）

该行关联的 PC 值未被插桩，或该源代码行未生成任何目标代码。下图展示了未插桩代码的样式：

![未插桩的代码行](coverage_not_instrumented.png?raw=true)

## syz-cover 工具

syzkaller 仓库中提供了一个轻量工具，可基于原始覆盖率数据生成覆盖率报告，工具位于 [syz-cover](/tools/syz-cover)，编译命令如下：

```bash
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o ./bin/syz-cover github.com/google/syzkaller/tools/syz-cover
```

通过运行 `syz-manager` 可获取原始覆盖率数据：

```bash
wget http://localhost:<你的 syz-manager 端口>/rawcover
```

将原始覆盖率数据传入 `syz-cover` 即可生成报告：

```bash
./bin/syz-cover --config <你的 syzkaller 配置文件路径> rawcover
```

也可导出包含函数覆盖率的 CSV 文件：

```bash
./bin/syz-cover --config <你的 syzkaller 配置文件路径> --csv <导出文件名> rawcover
```

或导出包含行覆盖率信息的 JSON 文件：

```bash
./bin/syz-cover --config <你的 syzkaller 配置文件路径> --json <导出文件名> rawcover
```

要不要我帮你整理一份 **syzkaller 覆盖率功能核心操作清单**，方便你快速查阅关键命令和界面标识含义？
