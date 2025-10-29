
[https://github.com/torvalds/linux/blob/master/Documentation/process/adding-syscalls.rst](https://github.com/torvalds/linux/blob/master/Documentation/process/adding-syscalls.rst)

# 添加新系统调用

本文档介绍了在Linux内核中添加新系统调用所需涉及的工作，这些工作是对 :ref:`Documentation/process/submitting-patches.rst <submittingpatches>` 中常规提交建议的补充。

## 系统调用的替代方案

添加新系统调用时，首先要考虑的是是否有更合适的替代方案。尽管系统调用是用户空间与内核之间最传统、最直观的交互方式，但还存在其他可选方式——应根据接口需求选择最适配的方案。

- 如果涉及的操作可抽象为类文件系统对象的形式，那么创建新的文件系统或设备可能更为合理。这种方式还能更轻松地将新功能封装到内核模块中，而无需将其编译到主内核里。

  - 若新功能涉及内核需通知用户空间某事件已发生的操作，那么为相关对象返回一个新的文件描述符，可让用户空间通过 ``poll``/``select``/``epoll`` 接收该通知。
  - 然而，对于无法映射为 :manpage:`read(2)`/:manpage:`write(2)` 类操作的功能，就必须通过 :manpage:`ioctl(2)` 请求来实现，这可能导致API不够直观。
- 若仅需暴露运行时系统信息，在sysfs（参见 ``Documentation/filesystems/sysfs.rst``）或 ``/proc`` 文件系统中新增一个节点可能更合适。但访问这些机制需要挂载相应的文件系统，而在某些场景下（如命名空间、沙箱或chroot环境），文件系统可能并未挂载。此外，避免在debugfs中添加任何API，因为它不被视为面向用户空间的“生产级”接口。
- 若操作特定于某个文件或文件描述符，那么新增一个 :manpage:`fcntl(2)` 命令选项可能更恰当。但 :manpage:`fcntl(2)` 是一个多路复用的系统调用，隐藏了大量复杂性，因此该选项仅适用于以下情况：新功能与现有 :manpage:`fcntl(2)` 功能高度类似，或新功能非常简单（例如获取/设置与文件描述符相关的简单标志）。
- 若操作特定于某个任务或进程，那么新增一个 :manpage:`prctl(2)` 命令选项可能更合适。与 :manpage:`fcntl(2)` 类似，:manpage:`prctl(2)` 也是一个复杂的多路复用系统调用，因此最好仅用于与现有 ``prctl()`` 命令几乎类似的功能，或用于获取/设置与进程相关的简单标志。

## API设计：为扩展预留空间

新系统调用是内核API的一部分，必须提供长期支持。因此，务必在内核邮件列表中明确讨论接口设计，且为接口的未来扩展做好规划至关重要。

（系统调用表中充斥着因未提前规划扩展而产生的历史案例，以及对应的后续系统调用——例如 ``eventfd``/``eventfd2``、``dup2``/``dup3``、``inotify_init``/``inotify_init1``、``pipe``/``pipe2``、``renameat``/``renameat2``。因此，应从内核的历史中吸取教训，从一开始就为扩展做好准备。）

对于仅需接收少量参数的简单系统调用，实现未来可扩展性的首选方式是为其添加一个 ``flags`` 参数。为确保用户空间程序能在不同内核版本间安全使用 ``flags``，需检查 ``flags`` 值是否包含未知标志，若存在则拒绝执行系统调用（返回 ``EINVAL``），代码示例如下：

```c
if (flags & ~(THING_FLAG1 | THING_FLAG2 | THING_FLAG3))
    return -EINVAL;
```

（若暂未使用任何 ``flags`` 值，则需检查 ``flags`` 参数是否为0。）

对于需要接收大量参数的复杂系统调用，更推荐的做法是将大部分参数封装到一个结构体中，通过指针传入。这类结构体可通过包含一个 ``size`` 参数来支持未来扩展，示例如下：

```c
struct xyzzy_params {
    u32 size; /* 用户空间需设置 p->size = sizeof(struct xyzzy_params) */
    u32 param_1;
    u64 param_2;
    u64 param_3;
};
```

只要后续新增的字段（如 ``param_4``）设计为“取值为0时保持原有行为”，就能应对版本不匹配的两种情况：

- 为处理较新的用户空间程序调用较旧内核的场景，内核代码需检查结构体预期大小之外的内存是否为0（实际等效于检查 ``param_4 == 0``）。
- 为处理较旧的用户空间程序调用较新内核的场景，内核代码可将较小的结构体实例零扩展（实际等效于设置 ``param_4 = 0``）。

可参考 :manpage:`perf_event_open(2)` 以及 ``perf_copy_attr()`` 函数（位于 ``kernel/events/core.c``），了解该方法的具体实现示例。

## API设计：其他注意事项

若新系统调用允许用户空间引用内核对象，则应使用文件描述符作为该对象的句柄——既然内核已具备文件描述符的使用机制和明确语义，就无需再设计新类型的用户空间对象句柄。

若新的 :manpage:`xyzzy(2)` 系统调用会返回一个新的文件描述符，那么 ``flags`` 参数中应包含一个等效于为新文件描述符设置 ``O_CLOEXEC`` 的值。这样能避免用户空间在 ``xyzzy()`` 调用与 ``fcntl(fd, F_SETFD, FD_CLOEXEC)`` 调用之间出现时间窗口漏洞：若其他线程中意外发生 ``fork()`` 和 ``execve()``，可能会导致文件描述符泄露给被执行的程序。（但需注意，不要直接复用 ``O_CLOEXEC`` 常量的实际值，因为它与架构相关，且属于已较为拥挤的 ``O_*`` 标志编号空间。）

若系统调用返回新的文件描述符，还需考虑在该文件描述符上使用 :manpage:`poll(2)` 系列系统调用的场景。内核通常通过将文件描述符设为“可读”或“可写”状态，向用户空间通知对应内核对象上发生的事件。

若新的 :manpage:`xyzzy(2)` 系统调用包含文件名参数，形式如下：

```c
int sys_xyzzy(const char __user *path, ..., unsigned int flags);
```

则需考虑是否提供 :manpage:`xyzzyat(2)` 版本更为合适，形式如下：

```c
int sys_xyzzyat(int dfd, const char __user *path, ..., unsigned int flags);
```

这种设计能让用户空间更灵活地指定目标文件，尤其支持通过 ``AT_EMPTY_PATH`` 标志对已打开的文件描述符执行操作，相当于免费实现了 :manpage:`fxyzzy(3)` 功能：

- ``xyzzyat(AT_FDCWD, path, ..., 0)`` 等效于 ``xyzzy(path,...)``
- ``xyzzyat(fd, "", ..., AT_EMPTY_PATH)`` 等效于 ``fxyzzy(fd, ...)``

（关于 \*at() 系列调用的设计原理，可参考 :manpage:`openat(2)` 手册页；关于 ``AT_EMPTY_PATH`` 的使用示例，可参考 :manpage:`fstatat(2)` 手册页。）

若新的 :manpage:`xyzzy(2)` 系统调用包含描述文件内偏移量的参数，应将其类型设为 ``loff_t``，确保即使在32位架构上也能支持64位偏移量。

若新的 :manpage:`xyzzy(2)` 系统调用涉及特权功能，则需通过相应的Linux能力位（使用 ``capable()`` 函数检查）进行管控，具体可参考 :manpage:`capabilities(7)` 手册页。应选择与相关功能对应的现有能力位，但需避免将大量关联度较低的功能归到同一个能力位下——这违背了能力机制“拆分root权限”的设计初衷。尤其要避免新增对已过度泛化的 ``CAP_SYS_ADMIN`` 能力的使用场景。

若新的 :manpage:`xyzzy(2)` 系统调用需操作调用进程之外的其他进程，则需通过 ``ptrace_may_access()`` 函数进行限制：仅当调用进程与目标进程拥有相同权限，或具备必要能力时，才能对目标进程执行操作。

最后需注意，部分非x86架构对系统调用参数有特殊要求：若参数明确为64位类型，最好将其放在奇数位参数位置（即第1、3、5个参数），以便使用连续的32位寄存器对存储。（若参数是通过指针传入的结构体成员，则无需考虑此问题。）

## API提案

为便于新系统调用的审核，建议将补丁集拆分为多个独立部分。至少应包含以下几个独立的提交（每个提交的详细说明见下文）：

- 系统调用的核心实现，以及对应的函数原型、通用编号、Kconfig配置变更和降级存根实现。
- 为特定架构（通常是x86，包括x86_64、x86_32和x32）适配新系统调用的代码。
- 通过 ``tools/testing/selftests/`` 中的自测试程序，演示用户空间如何使用新系统调用。
- 新系统调用的手册页草稿，可在封面邮件中以纯文本形式提供，或作为补丁提交到（独立的）手册页仓库。

与内核API的任何变更一样，新系统调用提案的邮件应抄送 linux-api@vger.kernel.org 邮件列表。

## 通用系统调用实现

新的 :manpage:`xyzzy(2)` 系统调用的主要入口函数名为 ``sys_xyzzy()``，但无需显式定义该入口，而是通过对应的 ``SYSCALL_DEFINEn()`` 宏来添加。其中，“n”表示系统调用的参数个数，宏的参数依次为系统调用名称以及各参数的（类型，名称）对。使用该宏能让新系统调用的元数据可被其他工具访问。

还需在 ``include/linux/syscalls.h`` 中为新入口函数添加对应的函数原型，并标记为 ``asmlinkage``，以匹配系统调用的调用方式：

```c
asmlinkage long sys_xyzzy(...);
```

部分架构（如x86）有自己的架构特定系统调用表，但其他多个架构共享一个通用系统调用表。需在 ``include/uapi/asm-generic/unistd.h`` 的列表中添加新系统调用的条目：

```c
#define __NR_xyzzy 292
__SYSCALL(__NR_xyzzy, sys_xyzzy)
```

同时，需更新 ``__NR_syscalls`` 的计数以反映新增的系统调用。需注意，若在同一合并窗口中新增多个系统调用，新系统调用的编号可能会因冲突而调整。

文件 ``kernel/sys_ni.c`` 为每个系统调用提供了返回 ``-ENOSYS`` 的降级存根实现，需在此处也添加新系统调用的条目：

```c
COND_SYSCALL(xyzzy);
```

新的内核功能及其对应的系统调用通常应设为可选，因此需为其添加一个 ``CONFIG`` 选项（通常在 ``init/Kconfig`` 中）。新增 ``CONFIG`` 选项需遵循以下规则：

- 描述该选项所管控的新功能和系统调用。
- 若需对普通用户隐藏该选项，应将其依赖于 ``EXPERT`` 选项。
- 在Makefile中，将实现新功能的源文件与 ``CONFIG`` 选项关联（例如 ``obj-$(CONFIG_XYZZY_SYSCALL) += xyzzy.o``）。
- 务必验证关闭新 ``CONFIG`` 选项后，内核仍能正常编译。

综上，需提交包含以下内容的补丁：

- 新功能的 ``CONFIG`` 选项（通常在 ``init/Kconfig`` 中）。
- 入口函数的 ``SYSCALL_DEFINEn(xyzzy, ...)`` 定义。
- ``include/linux/syscalls.h`` 中的对应函数原型。
- ``include/uapi/asm-generic/unistd.h`` 中的通用表条目。
- ``kernel/sys_ni.c`` 中的降级存根实现。

.. _syscall_generic_6_11:

### 6.11版本及之后

从内核6.11版本开始，以下架构的通用系统调用实现不再需要修改 ``include/uapi/asm-generic/unistd.h``：

- arc
- arm64
- csky
- hexagon
- loongarch
- nios2
- openrisc
- riscv

取而代之的是，需更新 ``scripts/syscall.tbl``，并在必要时调整 ``arch/*/kernel/Makefile.syscalls``。

由于 ``scripts/syscall.tbl`` 是多个架构共享的通用系统调用表，需在此表中添加新条目：

```
468   common   xyzzy     sys_xyzzy
```

需注意，在 ``scripts/syscall.tbl`` 中添加“common”ABI类型的条目会影响所有共享该表的架构。若需进行有限范围的变更或架构特定的变更，可考虑使用架构特定的ABI或定义新的ABI。

若引入新的ABI（如 ``xyz``），还需相应更新 ``arch/*/kernel/Makefile.syscalls``：

```
syscall_abis_{32,64} += xyz (...)
```

综上，需提交包含以下内容的补丁：

- 新功能的 ``CONFIG`` 选项（通常在 ``init/Kconfig`` 中）。
- 入口函数的 ``SYSCALL_DEFINEn(xyzzy, ...)`` 定义。
- ``include/linux/syscalls.h`` 中的对应函数原型。
- ``scripts/syscall.tbl`` 中的新条目。
- （必要时）``arch/*/kernel/Makefile.syscalls`` 中的Makefile更新。
- ``kernel/sys_ni.c`` 中的降级存根实现。

## x86系统调用实现

要为x86平台适配新系统调用，需更新主系统调用表。假设新系统调用无特殊情况（特殊情况见下文），需在 ``arch/x86/entry/syscalls/syscall_64.tbl`` 中添加“common”条目（适用于x86_64和x32）：

```
333   common   xyzzy     sys_xyzzy
```

并在 ``arch/x86/entry/syscalls/syscall_32.tbl`` 中添加“i386”条目：

```
380   i386     xyzzy     sys_xyzzy
```

同样需注意，若在相关合并窗口中存在编号冲突，这些编号可能会被调整。

## 兼容性系统调用（通用）

对于大多数系统调用，即使用户空间程序是32位的，也可调用相同的64位实现——即便系统调用参数包含显式指针，内核也会透明处理。

但在以下两种场景中，需实现兼容性层以处理32位与64位之间的大小差异：

第一种场景：64位内核同时支持32位用户空间程序，需解析（``__user`` 标记的）内存区域中可能包含的32位或64位值。当系统调用参数满足以下条件时，必须实现兼容性层：

- 指针的指针。
- 指向包含指针的结构体的指针（如 ``struct iovec __user *``）。
- 指向可变大小整数类型（``time_t``、``off_t``、``long`` 等）的指针。
- 指向包含可变大小整数类型的结构体的指针。

第二种场景：系统调用的某个参数在32位架构上也显式声明为64位类型（如 ``loff_t`` 或 ``__u64``）。此时，32位应用程序传入64位内核的值会被拆分为两个32位值，需在兼容性层重新组合。

（需注意，若系统调用参数是指向显式64位类型的指针，则**无需**实现兼容性层。例如，:manpage:`splice(2)` 中类型为 ``loff_t __user *`` 的参数，无需为其实现 ``compat_`` 版本的系统调用。）

兼容性版本的系统调用名为 ``compat_sys_xyzzy()``，通过 ``COMPAT_SYSCALL_DEFINEn()`` 宏添加，使用方式与 ``SYSCALL_DEFINEn`` 类似。该版本的实现运行在64位内核中，接收32位参数并进行必要的处理（通常，``compat_sys_`` 版本会将参数转换为64位，然后调用 ``sys_`` 版本，或两者共同调用一个通用的内部实现函数）。

还需在 ``include/linux/compat.h`` 中为兼容性入口函数添加对应的函数原型，并标记为 ``asmlinkage``，以匹配系统调用的调用方式：

```c
asmlinkage long compat_sys_xyzzy(...);
```

若系统调用涉及在32位和64位系统上内存布局不同的结构体（如 ``struct xyzzy_args``），则需在 ``include/linux/compat.h`` 中定义该结构体的兼容性版本（``struct compat_xyzzy_args``），其中每个可变大小字段需使用与 ``struct xyzzy_args`` 中对应类型匹配的 ``compat_`` 类型。之后，``compat_sys_xyzzy()`` 函数可使用该 ``compat_`` 结构体解析32位调用的参数。

例如，若 ``struct xyzzy_args`` 包含以下字段：

```c
struct xyzzy_args {
    const char __user *ptr;
    __kernel_long_t varying_val;
    u64 fixed_val;
```
