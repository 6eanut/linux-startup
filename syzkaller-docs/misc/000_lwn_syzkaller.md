# Syzkaller in LWN

[https://lwn.net/Articles/677764/](https://lwn.net/Articles/677764/)

# 基于覆盖率引导的 syzkaller 内核模糊测试

## 用户态模糊测试

模糊测试的基本思路的是向程序输入大量随机数据，观察程序是否崩溃，这一方法已存在许久。但单纯随机生成数据的简单实现效率极低，只能发现一些表层漏洞。要挖掘更深层次的漏洞，可采用“基于模板”的模糊测试工具：它会根据被测程序的可能/有效模式（即模板）生成输入变体，而这些模板信息需要为每个特定目标（或目标类别）手动创建。

不过近年来，“基于覆盖率引导”的模糊测试工具应运而生，其中最知名的是米哈乌·扎莱夫斯基（Michał Zalewski）的 american fuzzy lop（LWN 曾在 9 月报道过）和 Clang 的 LibFuzzer。这类工具无需特定目标的模板，而是通过对被测二进制文件进行插桩编译，暴露代码覆盖率信息。模糊测试工具会通过变异现有输入，保存能触发新代码路径的输入用例，不断扩充测试用例集，从而最大化代码覆盖率。

除了检测直接崩溃，模糊测试工具与暴露潜在漏洞的工具结合使用时效果更佳，例如 Clang 的 sanitizer 系列——这些编译器选项会在生成的代码中添加插桩逻辑，使不正确的行为在运行时触发错误提示：

- AddressSanitizer（ASAN）：检测内存访问错误。
- ThreadSanitizer（TSAN）：检测不同线程间的数据竞争。
- MemorySanitizer（MSAN）：检测未初始化读取，即代码行为依赖未初始化的内存内容。
- UndefinedBehaviorSanitizer（UBSAN）：检测 C/C++ 中各类明确规定为未定义行为的用法。

（大多数 sanitizer 已从 Clang 移植到 GCC，但仍有部分最实用的工具首先在 Clang/LLVM 中出现，甚至仅支持 Clang/LLVM——这也是人们期待 LLVMLinux 项目取得圆满成功的另一个原因。）

## 内核模糊测试

Linux 内核无疑需要处理不可信的用户输入，因此成为模糊测试的重要目标。由于内核关注度极高，开发者已为其不同领域（如文件系统或 perf_event 子系统）编写了专门的基于模板的模糊测试工具。在系统调用接口测试方面，目前主要使用的工具是 Trinity 模糊测试器，它通过系统调用专属模板实现对内核的智能模糊测试。

近几个月，维尤科夫（Vyukov）和谷歌团队将基于覆盖率引导的模糊测试引入内核领域，推出了 syzkaller，该工具采用混合架构。与 Trinity 类似，syzkaller 依赖指示每个系统调用参数范围的模板，同时结合代码覆盖率反馈来指导模糊测试过程。

插桩需求使得 syzkaller 的部署比 Trinity 更为复杂。首先，生成所需覆盖率数据的编译器选项（-fsanitize-coverage=trace-pc）是近期才添加到 GCC 中的，因此内核需要使用最新版本的 GCC 进行编译。

值得一提的是，琼斯（Jones）过去曾考虑为 Trinity 加入反馈引导模糊测试功能，但当时的覆盖率工具速度过慢，未能实现。而 syzkaller 的谷歌开发团队主要由编译器开发者组成，而非内核开发者，这使得他们能更轻松地升级工具以满足测试需求。

另一个复杂点在于，覆盖率数据需要按任务跟踪，并通过内核的 debugfs 节点（/sys/kernel/debug/kcov）导出到用户空间。相关内核补丁（含启用相关编译器选项的 CONFIG_KCOV 配置）目前正在讨论中，预计不久后会合并入主线。

如前所述，将系统调用模糊测试与暴露潜在漏洞的工具结合使用，能达到最佳漏洞挖掘效果。内核版本的 AddressSanitizer（KASAN）是最易启用的 sanitizer（已作为 CONFIG_KASAN 编译选项集成到内核中），同时启用各类内核调试功能也有助于发现内核内部 API 的不当使用，例如：

- CONFIG_PROVE_LOCKING：检测潜在死锁。
- CONFIG_PROVE_RCU：检测使用 RCU（读-复制-更新）机制的代码中的潜在漏洞。
- CONFIG_DEBUG_ATOMIC_SLEEP：发现原子操作段中调用可能导致睡眠的函数的代码。

启用这些选项后，那些原本 99% 概率下不会显现的漏洞，会通过错误提示暴露出来（相应地，这类漏洞在第 100 次出现时也更难排查和修复）。

完成上述准备工作后，即可在运行插桩内核的 QEMU 虚拟机集群上运行 syzkaller。下图展示了 syzkaller 各进程的架构（红色文本为配置项），该图源自项目官方文档。

（架构图说明：工作目录 dir 下包含崩溃日志目录 dir/crashes/crashN-T、测试用例集目录 dir/corpus/*；syz-manager 负责虚拟机管理，通过 scp、ssh RPC 与虚拟机通信；虚拟机中的 sshd 调用 syz-fuzzer，syz-fuzzer 接收输入并通过 syz-executor 执行系统调用；覆盖率信息通过 /sys/kernel/debug/kcov 导出；内核相关文件包括 vmlinux 和 kernel 文件；配置项含 sshkey 文件路径等。）

## 测试结果

为展示 syzkaller 的实际效果，我们尝试复现 2015 年 10 月首次报告的 System V 共享内存处理中的空指针解引用漏洞。通过 syzkaller 配置文件中的 enable_syscalls 参数，我们将测试的系统调用范围限定在该邮件线程中提及的调用，从而加快测试进程。同时，我们确保测试内核支持完整的命名空间功能，这使得模糊测试工具能在独立的沙箱中运行测试用例，互不干扰（通过 dropprivs 配置标志启用）。这一特性在处理共享内存等进程间资源时尤为实用。

模糊测试运行期间，syzkaller 会启动一个简易 Web 服务器，方便用户查看测试进度。主状态页会显示测试统计数据和已测试的系统调用列表，每个系统调用都提供以下链接：

- 用例集页面：展示包含该系统调用的已执行系统调用序列。例如，remap_file_pages() 的页面可能会显示“shmget-shmat-remap_file_pages”这样的序列摘要。
- 覆盖率页面：显示该系统调用在特定用例输入或所有相关用例输入中命中的内核源代码部分（需内核配置 CONFIG_DEBUG_INFO，且系统 PATH 中包含 addr2line 工具）。
- 优先级页面：显示随机生成其他系统调用与该调用组合时的权重策略。这些权重部分基于参数类型兼容性（例如，syzkaller 更可能组合两个均接收套接字文件描述符参数的系统调用），部分基于该调用对在当前用例集中的出现频率（频率高表明该组合曾有效命中新代码路径）。

运行一段时间后，syzkaller 会生成包含内核 oops 信息的报告文件，其中记录了执行过的系统调用序列以及空指针解引用的日志输出。将 oops 输出中的主要错误地址传入 addr2line 工具，可定位到问题出在 shm_lock() 函数——该函数在处理 remap_file_pages() 系统调用时，由 shm_open() 调用。

但报告文件中包含 204 个不同的系统调用序列，我们需要进一步缩小范围，找到触发漏洞的精确序列。syz-repro 工具可辅助完成这一过程：它以配置文件和崩溃报告文件为输入，首先筛选出触发崩溃的特定序列（通常是日志输出前的少数几个序列），然后通过生成简化版本的序列并验证是否仍能触发崩溃，反复最小化该序列。

在我们的示例中，经过 syz-repro 几次迭代后，得到了一个较短的系统调用序列：

```
mmap(&(0x7f0000000000)=nil, (0x2000), 0x3, 0x32, \
         0xffffffffffffffff, 0x0)
r0 = shmget(0x5, (0x2000), 0x200, &(0x7f0000b03000)=nil)
shmat(r0, &(0x7f0000b03000)=nil, 0x6000)
shmctl(r0, 0x3, &(0x7f0000000000+0xe4b)={ \
       0x3, <r1=>0xffffffffffffffff, 0x0, 0xffffffffffffffff, \
	   0xffffffffffffffff, 0x1, 0xfa, 0x3, 0xee, 0x10000, 0x6520, \
	   0x5, 0xffffffffffffffff, 0x0, 0x0})
shmctl(r0, 0xe, &(0x7f0000000000+0x28f)={ \
       0x1000, <r2=>0xffffffffffffffff, \
	   <r3=>0xffffffffffffffff, 0x0, <r4=>0x0, 0x7, \
	   0x100000000, 0x5, 0x6, 0x0, 0x2, 0x4, <r5=>0x0, \
	   0xffffffffffffffff, 0xef0})
shmctl(r0, 0xc, &(0x7f0000002000-0x50)={ \
       0x80, r1, r4, r2, r3, 0x7, 0x10000, 0x5, 0xff, 0x80000000, \
	   0x9, 0x3, r5, 0xffffffffffffffff, 0x2})
shmctl(r0, 0x0, &(0x7f0000001000-0x50)={ \
       0x1, 0x0, 0x0, 0xffffffffffffffff, 0x0, 0x1, 0x5, 0x5059, \
	   0x3, 0x6301, 0x8001, 0xfffffffffffffffd, 0xffffffffffffffff, \
       0x0, 0x6})
remap_file_pages(&(0x7f0000b03000)=nil, (0x2000), 0x0, 0x7, \
                 0x21dd964cfba54855)
```

为验证这是可复现的漏洞场景，我们将该系统调用脚本传入 syzkaller 的 syz-prog2c 工具，生成了一个 100 行左右的程序，可在测试内核上复现该问题。

此时，通过人工干预可进一步简化程序。观察 shmctl() 调用可知，前两次调用分别用于 IPC_INFO 和 SHM_INFO，均仅从内核读取数据，不进行任何修改。此外，SHM_UNLOCK 调用可能是无效操作（因未执行过锁定操作）。移除这些调用及其数据配置后，得到一个极短的程序，仍能复现该空指针解引用漏洞（目前该漏洞的修复补丁已在推进中）：

```c
#include <unistd.h>
#include <sys/syscall.h>
#include <string.h>

long r[5];

int main()
{
	memset(r, -1, sizeof(r));
	r[0] = syscall(SYS_mmap, 0x20000000ul, 0x2000ul, 0x3ul, 0x32ul,
	               0xfffffffffffffffful, 0x0ul);
	r[1] = syscall(SYS_shmget, 0x5ul, 0x2000ul, 0x200ul, 0x20b03000ul, 0, 0);
	r[2] = syscall(SYS_shmat, r[1], 0x20b03000ul, 0x6000ul, 0, 0, 0);
	r[3] = syscall(SYS_shmctl, r[1], 0x0ul, 0x20000fb0ul, 0, 0, 0);
	r[4] = syscall(SYS_remap_file_pages, 0x20b03000ul, 0x2000ul,
	               0x0ul, 0x7ul, 0x21dd964cfba54855ul, 0);
	return 0;
}
```

并非所有漏洞都能如此轻松地复现和隔离。若涉及持久化或全局资源，漏洞可能仅在多个测试程序交互时触发（当 procs 配置项大于 1 时）。更常见的情况是，漏洞仅在同一程序的多个线程交互时触发——模糊测试会刻意在多个线程中并行执行系统调用，这虽能提高漏洞发现概率，但会增加复现场景的排查难度。（启用 KTSAN 编译内核对发现多线程问题尤为有帮助，它能使潜在的数据竞争显性化。）

为辅助漏洞复现，syzkaller 提供了 syz-execprog 工具，支持通过多种选项重新运行崩溃脚本。-threaded 选项控制是否在多线程中运行脚本，若启用该选项，-collide 选项可强制线程并行执行系统调用。-repeat 选项则允许重复运行脚本任意次数，以捕获偶发漏洞（heisenbug）。

尽管这些工具无法保证生成简单的复现场景，但实际使用效果良好——大多数 syzkaller 生成的漏洞报告都包含简短的复现程序，极大简化了漏洞定位和修复流程。测试用例集也可作为新版本内核快速回归测试的有用资源。

## 未来规划

syzkaller 项目正处于积极开发阶段，进展迅速。如前所述，GCC 所需补丁已提交上游，将在下一代版本中包含；相应的内核补丁正在讨论中。一旦两者默认集成，运行 syzkaller 的复杂度将仅略高于 Trinity。

由于 syzkaller 是基于模板和覆盖率引导的混合式模糊测试工具，若能提供系统调用使用模式的相关信息，其测试效果将更佳。为此，syzkaller 开发者希望与内核开发者合作，审核并扩展对特定内核子系统的支持（这可能需要优化系统调用模板机制）。他们还计划突破目前主要支持 x86_64 架构的限制，扩展更多架构支持，并进一步自动化复现程序的提取和简化流程。

总体而言，syzkaller 是内核测试工具集的重要补充，其成功案例也印证了：对于任何处理用户输入的软件项目，模糊测试都应被视为最佳实践。
