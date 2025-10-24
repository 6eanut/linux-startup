vDSO（virtual Dynamic Shared Object，虚拟动态共享对象）是 Linux 内核在每个用户进程地址空间里“映射进去”的一小段只读共享库。它提供了一些可以在用户态直接完成的“轻量级内核服务”的函数入口，让常用的只读查询不用陷入内核（避免一次系统调用的上下文切换），从而降低开销、提升性能。

它解决什么问题

- 常见的查询类系统调用（如 clock_gettime、gettimeofday、time、getcpu 等）本质是读数据或做简单计算，不一定非要切到内核态。
- vDSO 把这类函数的实现做成一个普通 ELF 共享库段，并附带一块只读数据页（vvar）存放内核维护的时间数据等，用户态函数直接读取这块数据并做插值计算。
- 如果硬件/内核条件不满足（比如缺少高精度时钟源或某些配置关闭），库函数会自动回退到真正的系统调用，不影响正确性。

它是怎么工作的

- 编译阶段：内核为各架构单独构建一个小的共享对象，源码在 arch/$ARCH/kernel/vdso/ 下；同时还有 vvar 页用于放时间数据等。
- 运行阶段：进程 exec 时，内核把 vDSO 和 vvar 映射到进程地址空间，并在进程的 auxv（/proc/self/auxv）里通过 AT_SYSINFO_EHDR 告诉动态链接器 vDSO 的基址。地址随机化（ASLR）生效。
- C 运行库（glibc、musl 等）启动时会查找 __vdso_* 符号，若存在就直接调用；不存在或不可用则回退为真正的系统调用。应用程序无感。

常见能通过 vDSO 加速的函数

- 以 __vdso_* 前缀导出，具体集合因架构和内核版本而异。典型包括：
  - __vdso_clock_gettime / __vdso_clock_gettime64
  - __vdso_gettimeofday
  - __vdso_clock_getres / __vdso_clock_getres_time64
  - __vdso_time
  - 有的架构还有 __vdso_getcpu 等
- 注意：只适用于“读数据、不修改内核状态”的场景。像 open、write、fork 之类都不可能放进 vDSO。

在 RISC-V 上

- 源码位置：arch/riscv/kernel/vdso/（如 vdso.S、vgettimeofday.c、vdso.lds.S 等），以及对应的 vvar 定义。
- 它会尽力使用 RISC-V 的计时机制（如 time CSR/平台提供的高精度时钟）做用户态插值；若硬件/固件不支持（例如没有低开销可读时钟源），相关 vDSO 函数会回退为系统调用，因此依然正确，只是少了性能优势。
- 具体导出的 __vdso_* 列表可直接看该目录的源码和链接脚本。

如何在系统上看到 vDSO

- 看映射：cat /proc/self/maps | grep -E '\[vdso\]|\[vvar\]'
- 看基址：用 C 取 AT_SYSINFO_EHDR
  - 例子:
    - #include <sys/auxv.h>
    - #include <stdio.h>
    - int main(){ printf("%p\n", (void*)getauxval(AT_SYSINFO_EHDR)); return 0; }
- 看导出符号（需要能读取映射）：某些系统允许从 /proc/self/map_files/把 [vdso] 区域导出来再用 readelf/objdump 查看符号；或者用 gdb 附加查看 [vdso] 区域符号。权限策略不同，可能需要 root。

如何在源码中查看 vDSO 提供了什么

- 进入内核源码的 arch/riscv/kernel/vdso/：
  - 查看 Makefile/链接脚本（vdso.lds.S）里的符号导出清单（__vdso_*）。
  - 具体实现代码通常在该目录的 .c/.S 文件中。
- 编译后，内核会把构建好的 vDSO 镜像嵌入到内核映像，运行时映射给进程。

性能验证思路

- glibc 的 clock_gettime() 会优先用 vDSO。你可以对比两种调用：
  - 直接调用 clock_gettime()（通常走 vDSO）
  - 强制系统调用路径：syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &ts)
- 计时对比调用开销，通常 vDSO 会更快（尤其在频繁调用场景）。

配置与开关

- 是否启用以及提供哪些符号由架构和 Kconfig 决定，默认大多数发行版内核都开启。
- 许多架构支持内核启动参数 vdso=0 关闭 vDSO 映射（依赖内核版本/架构实现，具体以 Documentation/admin-guide/kernel-parameters.txt 为准）。关闭后 libc 会自动回退到系统调用。

一句话总结

- vDSO 是内核映射到用户态的一小段共享库，用来加速只读型“系统调用”，典型是各种取时间的调用；可用即用，不可用自动回退，既提高性能又不改变语义。
