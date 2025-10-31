## 🧩 一、ARCH 是什么？

**ARCH** 表示 **目标架构（Target Architecture）** ，也就是你要编译的目标 CPU 架构。

它直接决定了编译器的目标代码格式、汇编指令集、内核架构目录等。

常见取值：

| ARCH          | 含义                      | 对应目录            |
| ------------- | ------------------------- | ------------------- |
| `x86`       | 32/64 位 Intel/AMD 架构   | `arch/x86/`       |
| `arm`       | 32 位 ARM 架构            | `arch/arm/`       |
| `arm64`     | 64 位 ARM 架构（AArch64） | `arch/arm64/`     |
| `riscv`     | RISC-V 架构               | `arch/riscv/`     |
| `mips`      | MIPS 架构                 | `arch/mips/`      |
| `loongarch` | 龙芯 LoongArch 架构       | `arch/loongarch/` |

在 Linux 编译时，`ARCH` 变量会控制使用哪个 `arch/$(ARCH)/` 目录下的代码。

例如：

```bash
make ARCH=riscv defconfig
```

会去用 `arch/riscv/` 下面的 Kconfig 和头文件。

---

## 🧬 二、SUBARCH 是什么？

**SUBARCH** 表示 **宿主机架构（Host Architecture）** ，也就是你当前运行 `make` 的机器架构。

它通常用于**交叉编译时**帮助脚本判断是否需要调用交叉编译器。

比如，在 `Makefile` 里，通常有这样的逻辑：

```makefile
SUBARCH := $(shell uname -m)
ARCH ?= $(SUBARCH)
```

然后 `uname -m` 的结果：

| 运行平台     | `uname -m`输出 | SUBARCH 值  |
| ------------ | ---------------- | ----------- |
| x86_64 主机  | `x86_64`       | `x86_64`  |
| aarch64 主机 | `aarch64`      | `aarch64` |
| riscv64 主机 | `riscv64`      | `riscv64` |

所以如果你不指定 `ARCH`，编译系统会默认：

```bash
ARCH = SUBARCH
```

也就是“本机编译本机”。

如果要交叉编译，就必须手动指定目标架构。

---

**不是“子架构（sub-architecture）”的意思，而是“宿主机架构（the subordinate architecture of the build host）”的历史命名遗留。**

下面我详细解释这段历史和语义演变 👇

---

## 🕰 一、历史来源（从内核顶层 Makefile 而来）

在 Linux 内核顶层 `Makefile` 的早期版本（2000 年代初），有这样一段代码：

```makefile
SUBARCH := $(shell uname -m)
ARCH ?= $(SUBARCH)
```

这段逻辑出现在  **Linux 2.6 时代** 。

当时的设计意图是：

* 让 `SUBARCH` 表示 **编译主机的体系结构** （即 `uname -m`）；
* 如果用户没有手动指定 `ARCH`，则默认目标架构等于宿主架构。

也就是说：

> “SUBARCH” 是指当前主机的  **‘subordinate architecture value’** ，用来辅助确定最终的 ARCH 值。

它的“sub”其实来自 **“辅助/次级” (subordinate)** 的语义，而不是“子架构（sub-architecture）”。

---

## 🧩 二、为什么不是叫 HOSTARCH？

很合理的疑问是：

> 既然它表示宿主机的架构，为什么不用更直观的 `HOSTARCH` 呢？

答案是：

* **早期内核构建系统**的“host/target”区分还不完善；
* 一些脚本（比如 `scripts/kconfig`、`scripts/mkmakefile`）会把 SUBARCH 传递到子 Makefile；
* 它并不总是严格表示 “host architecture”，而是用于 **推断出合适的默认 ARCH 值** ；
* 因此它被称为 “sub architecture variable”，即“辅助架构变量”或“次级架构变量”。

可以理解为：

> SUBARCH 是一个“用于推导 ARCH 的辅助变量”。
