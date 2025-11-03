
* **CONFIG_32BIT**

  启用 32 位目标支持（使内核以 32 位 ABI 或者为 32 位体系架构构建）。通常在多架构树或需要同时支持 32/64 位用户态时用到。
* **CONFIG_64BIT**

  启用 64 位内核支持（让内核构建为 64 位）；与 `CONFIG_32BIT` 互斥或在多目标场景下选择对应架构。
* **CONFIG_ACPI**

  启用 ACPI（高级配置与电源接口）支持，提供电源管理、设备发现、休眠等平台级能力（主要用于 x86/某些平台）。
* **CONFIG_ACPI_NUMA**

  让 ACPI 提供的拓扑信息用于 NUMA（非一致性内存访问）节点划分；当平台通过 ACPI 提供 NUMA 描述时使用。
* **CONFIG_ARCH_ENABLE_HUGEPAGE_MIGRATION**

  允许在该架构上将大页（hugepage）进行迁移（搬移物理页面以实现内存回收/平衡）；对于内存管理优化有用。
* **CONFIG_ARCH_ENABLE_THP_MIGRATION**

  允许透明大页（Transparent HugePages, THP）在该架构上被迁移；与 THP 内存管理/合并相关。
* **CONFIG_ARCH_RV64I**

  表示启用架构基本集（RISC-V 64-bit 基本整数指令集 RV64I）的支持；通常用于标注目标 ISA。
* **CONFIG_ARCH_SUPPORTS_KEXEC_PURGATORY**

  表示该架构支持 kexec 的 purgatory 阶段（用于在 kexec 跳转期间运行小段代码来保存状态或清理）。
* **CONFIG_ARCH_SUPPORTS_PMD_PFNMAP**

  表示架构支持在 PMD（Page Middle Directory）层级使用 PFNMAP（直接把物理帧号映射为无页表属性的映射），便于映射 I/O 或高内存区域。
* **CONFIG_ARCH_SUPPORTS_PUD_PFNMAP**

  同上，但作用于 PUD（Page Upper Directory）层级：支持在 PUD 级别把物理帧号直接映射进去。
* **CONFIG_AS_HAS_ULEB128**

  表示汇编器（as）支持 ULEB128 编码指令/数据（常用于 DWARF、某些表格的压缩编码）。
* **CONFIG_BINFMT_ELF_FDPIC**

  允许 ELF FDPIC（函数位置无关可执行，常见于某些嵌入式/可加载定位模式）二进制格式加载器支持。
* **CONFIG_BPF_JIT**

  启用 eBPF JIT 编译器——把 BPF 字节码即时编译成本地机器码以提高性能。
* **CONFIG_BUILTIN_DTB**

  把设备树二进制（DTB）直接编译进内核镜像（内核内置 DTB），常用于嵌入式设备。
* **CONFIG_BUILTIN_DTB_MODULE**

  与 `BUILTIN_DTB` 类似，但将内置 DTB 放到模块化方式（或以模块形式处理）；具体行为依架构/实现而异。
* **CONFIG_CC_HAS_ASM_GOTO_OUTPUT**

  表示当前 C 编译器支持 `asm goto` 并能处理带输出约束的 `asm goto`，影响内核中某些宏/断言的实现。
* **CONFIG_CC_IS_CLANG**

  表示正在使用 Clang 作为 C 编译器（而非 GCC），会启用/禁用与 Clang 相关的兼容性路径或补丁。
* **CONFIG_CFI**

  启用控制流完整性（Control Flow Integrity）相关功能（例如 CFI 检查）以防止控制流劫持。
* **CONFIG_COMPAT**

  启用与旧 ABI（二进制兼容性）的支持（例如在 64 位内核上支持运行 32 位用户态程序）。
* **CONFIG_COMPAT_MODULE**

  使兼容层（compat）以模块方式提供而非内置进内核。
* **CONFIG_CONTIG_ALLOC**

  启用连续（contiguous）内存分配器/支持，用于需要大块连续物理内存的设备或驱动（例如 DMA 连续内存）。
* **CONFIG_CPU_BIG_ENDIAN**

  将内核配置为以大端（big-endian）模式运行（影响字节序处理）。
* **CONFIG_CRASH_DUMP**

  启用崩溃转储支持（crash dump / vmcore 生成），用于捕获内核崩溃时的内存镜像以便调试。
* **CONFIG_DCACHE_WORD_ACCESS**

  表示数据缓存（D-cache）以字（word）为最小可访问单元；影响对内存访问对齐/缓存操作的假设。
* **CONFIG_DEBUG_BUGVERBOSE**

  在 BUG/BUG_ON 触发时提供更详细的调试信息（例如堆栈、位置、寄存器等），便于追踪致命 BUG。
* **CONFIG_DEBUG_PAGEALLOC**

  启用页分配器的调试（在释放后用特殊填充值标记等），用于捕捉内核对已释放内存的错误访问。
* **CONFIG_DEBUG_VIRTUAL**

  启用针对虚拟内存管理的额外调试检查（捕捉非法虚拟地址操作等）。
* **CONFIG_DEBUG_VM**

  启用虚拟内存子系统的额外调试信息（更详细的 VM 日志与断言）。
* **CONFIG_DYNAMIC_FTRACE**

  启用动态 ftrace（函数跟踪）支持，允许在运行时插入/移除跟踪点而不需要重启。
* **CONFIG_DYNAMIC_FTRACE_WITH_ARGS**

  使动态 ftrace 能够收集/传递函数参数（比纯地址跟踪更详细）。
* **CONFIG_DYNAMIC_FTRACE_WITH_CALL_OPS**

  启用 ftrace 所需的一些 call 操作抽象（实现细节，允许更灵活的调用/替换机制）。
* **CONFIG_DYNAMIC_FTRACE_WITH_DIRECT_CALLS**

  使 ftrace 使用直接调用替换（在某些架构上可以更高效地进行函数跳转替换）。
* **CONFIG_DYNAMIC_SIGFRAME**

  启用动态信号帧（signal frame）布局或处理方式，使内核能在运行时调整信号处理栈布局以适配安全性或 ABI 要求。
* **CONFIG_EFI**

  启用 EFI（UEFI）支持，允许通过 EFI 接口启动和交互（常用于 x86_64/arm64 平台的固件交互）。
* **CONFIG_EFI_EARLYCON**

  在系统引导早期通过 EFI 的控制台接口输出早期日志（early console via EFI）。
* **CONFIG_ERRATA_ANDES**

  开启对特定厂商（如 Andes）的处理器 errata（芯片缺陷）补丁或工作绕过。
* **CONFIG_ERRATA_MIPS**

  启用 MIPS 架构相关的 errata 补丁或对应工作绕过。
* **CONFIG_ERRATA_SIFIVE**

  为 SiFive（RISC-V 实现厂商）处理器应用 errata 补丁或特殊处理。
* **CONFIG_ERRATA_THEAD**

  为 Thead（芯片厂商）处理器应对 errata 的补丁/处理。
* **CONFIG_ERRATA_THEAD_MAE**

  Thead 公司某个具体 errata（MAE）相关的补丁开关。
* **CONFIG_EXECMEM**

  允许可执行与可写内存区域（exec + mem）— 控制可执行内存的允许与否，影响 JIT、动态代码生成的策略与安全性（通常与 W^X 策略相关）。
* **CONFIG_FLATMEM**

  选择一种内存模型（flat memory model），适用于物理内存简单、没有 NUMA 的系统；与 SPARSEMEM 等互斥。
* **CONFIG_FPU**

  启用浮点单元（FPU）支持（内核需要保存/恢复浮点上下文等）。
* **CONFIG_FRAME_POINTER**

  保持函数的帧指针（frame pointer，通常用于更可靠的回溯 / 调试），会影响优化与栈回溯质量。
* **CONFIG_FUNCTION_GRAPH_TRACER**

  启用函数图跟踪器（跟踪函数调用图、进入与退出，常用于性能分析）。
* **CONFIG_FUNCTION_TRACER**

  启用函数级别的跟踪（函数入口/出口事件跟踪）。
* **CONFIG_GENERIC_ATOMIC64**

  使用通用（纯软件）实现的 64 位原子操作（用于不支持原生 64 位原子指令的架构）。
* **CONFIG_GENERIC_BUG**

  启用内核中通用的 BUG 处理路径（用于报告 BUG、记录信息等），与平台相关的扩展。
* **CONFIG_GENERIC_BUG_RELATIVE_POINTERS**

  使 BUG 报告中使用相对指针格式以节省空间或便于位置无关的表示（实现细节）。
* **CONFIG_GENERIC_CLOCKEVENTS_BROADCAST**

  启用通用时钟事件广播机制（用于多核时钟事件同步等）。
* **CONFIG_GENERIC_TIME_VSYSCALL**

  允许使用 vDSO / vsyscall 提供的快速时间读取接口（legacy vsyscall 或 vDSO 方法）。
* **CONFIG_GUEST_PERF_EVENTS**

  允许在虚拟机（guest）中收集性能事件或允许 hypervisor 转发性能事件给 guest。
* **CONFIG_HAVE_ARCH_HUGE_VMAP**

  表示该架构支持“huge vmaps”（大型虚拟内存映射技术），影响内核如何构建高容量虚拟地址映射。
* **CONFIG_HOTPLUG_CPU**

  启用 CPU 热插拔支持，允许在运行时下线/上线 CPU（常用于节能或容错）。
* **CONFIG_IRQ_STACKS**

  为中断使用独立的内核栈（提供更好隔离与调试信息），通常在开启后为每个 CPU 分配单独中断栈。
* **CONFIG_IRQ_WORK**

  启用 irq_work 子系统，允许从中断上下文调度轻量工作到软中断或线程上下文执行。
* **CONFIG_KASAN**

  启用 Kernel Address SANitizer（内核地址消毒器），用于检测内核内存越界、使用后释放等内存错误（用于调试/验证）。
* **CONFIG_KASAN_GENERIC**

  使用通用（非架构特殊）实现的 KASAN 后端。
* **CONFIG_KASAN_SW_TAGS**

  使 KASAN 使用软件内存标签机制（tags）来检测错用/越界。
* **CONFIG_KASAN_VMALLOC**

  使 KASAN 也扩展到 vmalloc 分配的区域，检测 vmalloc 区域的错误访问。
* **CONFIG_KEXEC_CORE**

  启用 kexec 的核心支持（在崩溃或正常切换时加载另一个内核镜像）。
* **CONFIG_KEXEC_FILE**

  允许从文件系统加载 kexec 镜像（`kexec -l <file>` 的支持）。
* **CONFIG_KFENCE**

  启用 KFENCE（Kernel Electric Fence）——一种轻量的内核内存错误检测工具，低开销适合生产环境。
* **CONFIG_KGDB**

  启用内核调试器 KGDB 支持，通过串口或网络调试器连接调试内核。
* **CONFIG_KPROBES**

  启用 kprobes（动态内核探针），允许在运行时插入断点/探针并执行回调，常用于调试和观测。
* **CONFIG_KSTACK_ERASE**

  在释放内核栈时擦除内容以防止泄露敏感数据（安全性增强）。
* **CONFIG_MEMORY_HOTPLUG**

  启用内存热插拔（在运行时添加/移除物理内存并让内核在线识别并使用/下线），常用于服务器/云场景。
* **CONFIG_MMU**

  启用内存管理单元（MMU）支持；没有 MMU 的内核配置会不同（例如嵌入式 microcontroller）。
* **CONFIG_MODULES**

  允许加载/卸载内核模块（动态可加载对象），是模块化内核的基础。
* **CONFIG_MODULE_SECTIONS**

  允许模块使用特殊节（sections）来组织数据/代码，例如用于模块签名或元数据。
* **CONFIG_NUMA**

  启用 NUMA（非一致性内存访问）支持，内核将考虑节点亲和性进行内存/进程调度优化。
* **CONFIG_NUMA_BALANCING**

  启用自动 NUMA 平衡（内核会尝试迁移内存页以改善进程内存访问的本地性）。
* **CONFIG_PAGE_TABLE_CHECK**

  启用对页表更新/一致性的检查（用于调试页表相关错误）。
* **CONFIG_PARAVIRT**

  启用半虚拟化（paravirtualization）支持，让内核可以在虚拟化环境中以更高效/兼容的方式运行。
* **CONFIG_PCI**

  启用 PCI 总线支持（发现与驱动 PCI 设备所需的子系统）。
* **CONFIG_PERF_EVENTS**

  启用 perf 性能事件子系统（性能计数器、事件收集、分析工具支持）。
* **CONFIG_PM_SLEEP_SMP**

  与电源/睡眠相关，在 SMP（多处理器）系统上对 suspend/resume 的特殊处理支持。
* **CONFIG_PROC_FS**

  启用 /proc 文件系统（内核信息与进程信息虚拟文件系统）。
* **CONFIG_QUEUED_SPINLOCKS**

  启用排队自旋锁（queued spinlocks），一种可扩展的锁实现以改善高核数下的锁争用行为。
* **CONFIG_RANDOMIZE_BASE**

  启用内核地址空间随机化（KASLR 或相关），以增加安全性通过随机化基址。
* **CONFIG_RELOCATABLE**

  使内核镜像可重定位（可以被加载到不同地址而不需要重建），与内核随机化相关。
* **CONFIG_RISCV_ALTERNATIVE**

  在 RISC-V 架构上启用 `alternative` 机制（在运行时或引导时替换指令序列以适配 CPU 特性或 errata）。
* **CONFIG_RISCV_ALTERNATIVE_EARLY**

  允许更早阶段的 `alternative` 替换（在引导更早期就应用替换），用于早期兼容/补丁。
* **CONFIG_RISCV_BOOT_SPINWAIT**

  为 RISC-V 平台在启动时使用 spin/wait 指令序列（实现 CPU 空转等待的特定策略）。
* **CONFIG_RISCV_COMBO_SPINLOCKS**

  在 RISC-V 上使用“组合”自旋锁实现（可能混合了不同锁机制以获得更好性能/可扩展性）。
* **CONFIG_RISCV_DMA_NONCOHERENT**

  标识 RISC-V 平台的 DMA 是非一致性（non-coherent），内核会在 DMA 前后执行缓存管理操作（flush/invalidate）。
* **CONFIG_RISCV_ISA_C**

  启用 RISC-V 的 C 扩展（压缩指令集，RVC），减小代码体积并可能影响性能/对齐。
* **CONFIG_RISCV_ISA_FALLBACK**

  启用某种回退机制，当遇到不支持的指令/特性时提供 fallback 处理（实现兼容性）。
* **CONFIG_RISCV_ISA_SUPM**

  启用 RISC-V 的 SUPM 扩展（具体扩展名称依上下文，可能与 supervisor/特权模式相关）。
* **CONFIG_RISCV_ISA_SVNAPOT**

  启用 RISC-V 的某个特定地址/对齐或 PTE 表示的扩展（SVNAPOT，通常与页表条目或物理内存编码有关）。
* **CONFIG_RISCV_ISA_V**

  启用 RISC-V 向量扩展（Vector extension），用于矢量化运算（SIMD 类似能力）。
* **CONFIG_RISCV_ISA_VENDOR_EXT_ANDES**

  启用 Andes 厂商扩展支持（针对 Andes CPU 的自定义指令集扩展）。
* **CONFIG_RISCV_ISA_VENDOR_EXT_MIPS**

  启用 MIPS 厂商扩展支持（若 RISC-V 实现包含 MIPS 风格扩展）。
* **CONFIG_RISCV_ISA_VENDOR_EXT_SIFIVE**

  启用 SiFive 厂商扩展（SiFive 提供的自定义指令/特性）。
* **CONFIG_RISCV_ISA_VENDOR_EXT_THEAD**

  启用 Thead 厂商扩展支持（厂商特有扩展）。
* **CONFIG_RISCV_ISA_V_PREEMPTIVE**

  与向量扩展的抢占性上下文切换支持相关，表示向量寄存器抢占/保存策略的某种模式。
* **CONFIG_RISCV_ISA_ZACAS**

  启用 RISC-V 的 ZACAS 扩展（atomic compare-and-set 或原子相关扩展）。
* **CONFIG_RISCV_ISA_ZAWRS**

  启用 ZAWRS 扩展（具体为某原子或特殊指令扩展，厂商/实现相关）。
* **CONFIG_RISCV_ISA_ZBA**

  启用 ZBA（Byte/Bit 操作扩展，或与某些原子操作相关的标准扩展）。
* **CONFIG_RISCV_ISA_ZBB**

  启用 ZBB（位/字节位操作扩展，RISC-V 标准之一，用于位级指令增强）。
* **CONFIG_RISCV_ISA_ZBKB**

  启用 ZBKB 扩展（更细粒度的位/字节相关扩展）。
* **CONFIG_RISCV_ISA_ZICBOP**

  启用 ZICBOP（cache block operations）扩展，提供对缓存行/块操作的指令支持（例如加速某些内存带宽操作）。
* **CONFIG_RISCV_ISA_ZICBOZ**

  启用 ZICBOZ（cache block-zero 或类似）扩展，用于高效将缓存块清零等操作。
* **CONFIG_RISCV_MISALIGNED**

  允许处理或容忍（并提供处理路径）未对齐内存访问（捕获并在内核/硬件层面处理 misaligned loads/stores）。
* **CONFIG_RISCV_M_MODE**

  启用 RISC-V 的 M (machine) 模式支持或相关功能（最高权限级别的支持）。
* **CONFIG_RISCV_M_MODE_MODULE**

  以模块方式提供 M 模式相关支持（而非内置），取决于实现是否允许模块化 M 模式处理。
* **CONFIG_RISCV_NONSTANDARD_CACHE_OPS**

  允许使用非标准的缓存操作（vendor-specific cache op）以适配特定芯片的缓存行为。
* **CONFIG_RISCV_PMU_SBI**

  使用 SBI（Supervisor Binary Interface）来访问 PMU（性能监控单元）计数器和事件（在 RISC-V 虚拟化/环境中常见）。
* **CONFIG_RISCV_PROBE_UNALIGNED_ACCESS**

  在引导或运行时探测是否允许未对齐访问，并据此使能/禁用内核的相应处理路径。
* **CONFIG_RISCV_PROBE_VECTOR_UNALIGNED_ACCESS**

  针对向量指令探测未对齐访问支持（如果向量扩展允许未对齐访问则启用相关路径）。
* **CONFIG_RISCV_QUEUED_SPINLOCKS**

  在 RISC-V 上启用排队自旋锁实现以提升高并发下的可扩展性。
* **CONFIG_RISCV_SBI**

  启用对 SBI 接口的支持（RISC-V 常用的固件/运行时接口，用于时钟、中断、console 等服务）。
* **CONFIG_RISCV_SBI_MODULE**

  以模块形式提供 SBI 支持（而非内置），具体取决于内核/平台是否允许。
* **CONFIG_RISCV_SBI_V01**

  表示使用或兼容 SBI v0.1 版本接口（版本兼容选项）。
* **CONFIG_RISCV_SCALAR_MISALIGNED**

  针对标量（非向量）操作启用未对齐访问的处理或兼容路径。
* **CONFIG_RISCV_VECTOR_MISALIGNED**

  针对向量操作启用未对齐访问的处理或兼容路径。
* **CONFIG_SHADOW_CALL_STACK**

  启用 Shadow Call Stack（影子调用栈）——安全机制，用来保护返回地址不被篡改（增强控制流安全）。
* **CONFIG_SMP**

  启用对对称多处理（SMP，多核）的支持（多 CPU 调度、同步等机制）。
* **CONFIG_SMP_MODULE**

  以模块形式提供 SMP 支持（通常 SMP 是内核内置；该项表示某些 SMP 机制可以模块化）。
* **CONFIG_SOFTIRQ_ON_OWN_STACK**

  保证 softirq 在其自己的内核栈上运行（提高隔离/安全性，避免栈溢出污染）。
* **CONFIG_SPARSEMEM**

  使用 sparse memory 模型（适合内存很大或稀疏映射的系统），与 FLATMEM 互斥。
* **CONFIG_SPARSEMEM_VMEMMAP**

  在 sparsemem 模型中用 vmemmap（虚拟化的页表映射）来表示内存映射，用于内核对物理页的管理。
* **CONFIG_STACKPROTECTOR**

  启用栈保护（Stack Protector / canary），用于检测栈缓冲区溢出。
* **CONFIG_STACKPROTECTOR_PER_TASK**

  为每个任务（进程/线程）单独管理栈保护相关的数据（而非全局），可能提升隔离与安全性。
* **CONFIG_STRICT_KERNEL_RWX**

  强制内核内存页面的 RWX（可读/写/执行）限制，防止同时可写和可执行的内存区域，从安全角度限制可执行写内存。
* **CONFIG_SYSCTL**

  启用 sysctl 接口（通过 /proc/sys 或者内核 API 调整内核参数的能力）。
* **CONFIG_SYSFB**

  启用系统帧缓冲（system framebuffer）设备支持，允许内核早期或缺少显卡驱动时输出图形/控制台。
* **CONFIG_TOOLCHAIN_HAS_ZACAS**

  表示当前工具链（编译器/汇编器）支持 ZACAS（或类似）指令集扩展的代码生成。
* **CONFIG_TOOLCHAIN_HAS_ZBA**

  工具链支持 ZBA 扩展的代码生成。
* **CONFIG_TOOLCHAIN_HAS_ZBB**

  工具链支持 ZBB 扩展的代码生成。
* **CONFIG_TRANSPARENT_HUGEPAGE**

  启用透明大页（THP），内核会尝试自动把连续小页合并为大页以减少 TLB 压力并提升性能（也有潜在的延迟/内存占用影响）。
* **CONFIG_UPROBES**

  启用 uprobes（用户空间探针），可以在用户态程序的指令上插入探针以进行动态跟踪/调试。
* **CONFIG_VDSO_GETRANDOM**

  使 vDSO（虚拟动态共享对象）提供 `getrandom` 功能的直接实现，从而在用户态高速获取随机数据（避免系统调用开销）。
* **CONFIG_VMAP_STACK**

  使用 vmalloc/vmap 为内核栈分配虚地址（而非连续物理页面），有利于内核地址空间管理但可能影响性能/约束。
* **CONFIG_XIP_KERNEL**

  启用 XIP（eXecute In Place）内核支持，允许在只读存储（例如闪存）上直接执行内核代码以节省 RAM（常见于嵌入式）。
* **CONFIG_ZONE_DMA32**

  启用 DMA32 zone（低于 4GB 的内存区域）支持，使得需要 32 位 DMA 地址的设备可以在该 zone 中分配内存。
