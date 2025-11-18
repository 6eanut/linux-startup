# Stack Canary

# 🔰 1. Stack Canary 是什么？

 **Stack Canary** （堆栈金丝雀）是一种防止 **栈溢出攻击（buffer overflow）** 的保护机制。

原理类似「金丝雀在煤矿里探毒气」：

1. 在栈上局部变量和返回地址之间放一个  **随机数** （canary）
2. 函数返回前检查它是否被改写
3. 如果被改写 → 程序立即终止（Kernel panic 或 abort）

目的是防止覆盖返回地址，从而劫持控制流。

---

# 🔰 2. Stack Canary 的基本布局

一个典型函数栈帧如下：

```
|------------------|
|  local buffers   |
|------------------|
|    canary        |  ← 随机数 
|------------------|
| saved frame ptr  |
| saved return addr|
|------------------|
```

如果攻击者假设进行栈溢出：

```
buffer[64]
```

写过界，就会先覆盖  **canary** ，检查时就能检测到异常。

---

# 🔰 3. Stack Canary 在用户态（glibc）是如何实现的？

用户态的 stack protector 由 GCC 提供，通过编译选项启用：

* `-fstack-protector`（保护某些函数）
* `-fstack-protector-strong`
* `-fstack-protector-all`

### 3.1 Canary 的来源：`__stack_chk_guard`

glibc 会在程序启动时初始化：

```c
extern uintptr_t __stack_chk_guard;
```

其值是一个随机数，通常来自：

* `AT_RANDOM`（ELF auxiliary vector）
* 16 bytes 的随机数据

---

### 3.2 编译器插桩：

函数入口：

```asm
mov __stack_chk_guard, %rax
mov %rax, -8(%rbp)
```

函数退出检查：

```asm
mov -8(%rbp), %rax
cmp %rax, __stack_chk_guard
jne __stack_chk_fail
```

失败处理：

```
__stack_chk_fail() → abort()
```

---

# 🔰 4. Linux 内核中的 Stack Canary

这是你可能最关心的部分。

启用方式：

```
CONFIG_STACKPROTECTOR
CONFIG_STACKPROTECTOR_STRONG
```

位置：

```
arch/*/include/asm/stackprotector.h
```

在内核中，Stack Canary  **不是从 AT_RANDOM 获取的** ，而是由内核自己初始化。

---

# 🔰 4.1 内核的 Canary 值：`__stack_chk_guard`

在 boot 时初始化：

* x86: `arch/x86/kernel/stackprotector.c`
* arm64: `arch/arm64/kernel/stackprotector.c`

例如 x86：

```c
unsigned long __stack_chk_guard;

void __init init_stack_canary(...)
{
    get_random_bytes(&__stack_chk_guard, sizeof(__stack_chk_guard));

    __stack_chk_guard &= CANARY_MASK;
    __stack_chk_guard |= CANARY_BASE;
}
```

其中典型的值：

* 低字节是 `00`（防止 `strcpy` 影响 canary 值）
* 其它字节全随机

---

# 🔰 4.2 内核函数插桩：

GCC 在需要保护的函数入口插入：

```c
current->stack_canary = __stack_chk_guard;
```

退出前检查：

```c
if (current->stack_canary != __stack_chk_guard)
    __stack_chk_fail();
```

对应内核实现：

```c
void __stack_chk_fail(void)
{
    panic("stack-protector: Kernel stack is corrupted\n");
}
```

所以内核一旦 Canary 被破坏：

* 直接 `panic()`
* 系统立即崩溃

防止继续执行被攻击后的代码。

---

# 🔰 5. Kernel Canary 的存放位置在哪里？

每个内核线程 **task_struct** 里有一个保存位置：

```
task_struct.stack_canary
```

并且在 context switch 时统一更新，确保每个进程都有独立的 canary。

---

# 🔰 6. 为什么 Canary 的最后一个字节是 0x00？

因为许多经典栈溢出使用 `strcpy()`/memcpy 等字符串操作，以 `\0` 作为结束符。

让最低字节为 `00`，可以避免：

* 用户空间的字符串操作意外修改 canary
* 传统 tail-zero 自然向右扩展覆盖 canary

---

# 🔰 7. Canary 能防御什么？

### 能防御：

* 经典栈溢出覆盖返回地址
* 覆盖 saved frame pointer
* 覆盖栈上局部变量以企图跳转

### 不能防御：

* 信息泄露（info leak）导致 canary 泄漏
* ret2libc 或 ROP 攻击在已知 canary 情况下绕过
* 写入到非连续栈区域
* 控制结构不在被保护区域（heap overflow）

---

# 🔰 8. Canary 与 KASAN/KPTI 的关系？

栈 canary 是  **build-time 静态保护** 。

KASAN 是运行时检测堆栈/heap 的溢出。

KPTI 是内核/用户态地址分离，与 canary 无关系。

---

# 🔰 9. Canary 在内核中如何被绕过（攻击者角度）

常见方法：

1. **信息泄露漏洞** （比如 /proc 泄露栈）泄漏 canary 值 → 绕过
2. **非连续写入（write-what-where）**

   不改变 canary，而是改写另一个指针区域 → 绕过
3. **覆盖超大结构时直接覆盖 saved RIP 而越过 canary**

   某些编译器布局漏洞
4. **没有被插桩的函数不会有 canary**

---

# 🔚 总结（最短版）

* Canary 是一个随机数，保存在栈上
* 函数返回前必须验证它
* 内核和用户态都有自己的实现方式
* Canary 被破坏 → 内核 panic 或进程 abort
* 主要防御传统 buffer overflow 攻击

注：并不是所有内核函数都会被插装stack canary，只有有潜在栈溢出风险的内核函数，才会被自动插装，这个编译器做的事情。
