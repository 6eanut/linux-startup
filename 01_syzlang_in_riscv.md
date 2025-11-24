# Syzlang in RISC-V

这个标题想表达的意思不准确，接下来要做的事情是：

* RISC-V下的Linux支持哪些系统调用；
* syzkaller中，用syzlang编写的template中，对于这些系统调用的支持情况如何？

## 0 调研

syz-extract的使用：[syzkaller在github上的相关docs](https://github.com/google/syzkaller/blob/master/docs/syscall_descriptions.md)、[syzkaller在github上的相关issue](https://github.com/google/syzkaller/issues/590)

linux下各架构所支持的syscall：[一个arm开发者维护的开源项目
](https://gpages.juszkiewicz.com.pl/syscalls-table/syscalls.html)

---

syzkaller 是一个 template-based 模糊测试器，它的 fuzz 覆盖范围取决于：

* 哪些 syscall 在 syzlang 中被定义；
* 哪些参数常量在 syzlang 中被列出；

任何未写入 syzlang 的 syscall 或 syscall 分支（由参数值控制）都永远不会被 fuzz 到。

为了 fuzz 到 arch/riscv 下的架构相关代码，需要同时确保：

* RISC-V 专属 syscall（如 riscv_flush_icache、riscv_hwprobe等）已被 syzlang 描述；
* 通用 syscall 中 RISC-V 专属常量（如系统调用 prctl 的第一个参数 PR_RISCV_*）也已被 syzlang 描述。

否则 syzkaller 无法生成这些系统调用或架构相关分支永远无法被执行。
