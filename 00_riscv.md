# arch/riscv

## 1 配置项

目标是生成一系列配置项清单，这些配置项清单能cover住arch/riscv下的所有代码

### 1-1 undertaker工具

这是一个开源项目：[https://github.com/6eanut/original-undertaker-tailor](https://github.com/6eanut/original-undertaker-tailor)

#### 1-1-0 从源码编译构建

```shell
make localpuma
# 这里可能需要配一下puma的环境变量，从makefile里面找思路
make
PREFIX=/pathto/undertaker make install
```

下面介绍一下它的部分功能。

#### 1-1-1 blockrange

对file进行分析，看该文件中的哪些行会被配置项管辖

```shell
undertaker -j blockrange file
```

例如，对于[arch/riscv/mm/pmem.c](00_riscv/code/pmem.c)而言，分析得到的结果是：

```shell
$ undertaker -j blockrange arch/riscv/mm/pmem.c
arch/riscv/mm/pmem.c:B00:0:0
arch/riscv/mm/pmem.c:B0:14:19
arch/riscv/mm/pmem.c:B1:26:31
```

即第14-19行和第26-31行会被配置项管理。

#### 1-1-2 cpppc_decision

生成Bi和宏定义的映射

```shell
undertaker -j cpppc_decision file
```

blockrange生成的是config Bi控制着哪些代码行，config Bi是谁未知，cpppc_decision可以生成Bi到宏定义的映射。

注意：这里不仅包含CONFIG_XXX，还有一些与配置项无关的宏定义。

#### 1-1-3 coverage

会对file进行分析，生成多个config清单，这些config清单组合在一起能让这个文件的coverage最大化

```shell
undertaker -j coverage file
```

例如，对于[arch/riscv/mm/cacheflush.c](00_riscv/code/cacheflush.c)而言，分析得到的结果是产生两个文件在arch/riscv/mm下：

```shell
# arch/riscv/mm/cacheflush.c.config1
CONFIG_MMU=y
CONFIG_SMP=y
# arch/riscv/mm/cacheflush.c.config2
CONFIG_MMU=y
CONFIG_SMP=n
```

对于coverage模式，还有一些其他的额外选项，比如-C min用来指定生成尽可能少的配置组合，但速度会变慢；-C min_decision/simple_decision会依赖判定覆盖而非语句覆盖。

#### 1-1-4 blockpc

用于分析某个文件的某一行(甚至某一列)被哪个配置项管理。

```shell
$ undertaker -j arch/riscv/mm/cacheflush.c:180:1
B2
&& ( B2 <-> (CONFIG_SMP) )
&& B00
```

#### 1-1-5 blockconf

用于分析想要cover到某个文件的某一行，需要开启/关闭什么配置项。

```shell
$ undertaker -j blockconf arch/riscv/mm/cacheflush.c:180
CONFIG_SMP=y
```

#### 1-1-6 undertaker-linux-tree

先在linux目录下执行undertaker-kconfigdump来生成model文件，然后运行undertaker-linux-tree来检测是否有dead代码。(目前在生成model时不支持riscv)

### 1-2 cover每个文件所需要的config清单(尚未考虑Makefile的影响，后续需要补上)

undertaker的coverage功能能够生成若干config清单，这些清单的总和能够cover这个文件的所有代码，我这里写了一个脚本来完成这个事情，见[这里](00_riscv/code/file2config.sh)。

它的执行流程是这样的：

* 识别出arch/riscv目录下的所有.S, .c, .h文件，然后对其执行undertaker的coverage功能，这会在.S, .c, .h文件所在的路径下生成xxx.configx配置项清单；
* 该配置项清单会包含一些其他宏定义，所以需要扔掉，只保留CONFIG_XXX相关的，并且把这些配置项清单挪到一个干净的目录下，便于后续进行分析。

结果大致是[这样](00_riscv/code/configs_cover_file_result.txt)的。

然后借助golem工具的-e选项，输入由前面undertaker的coverage选项生成的config，进而生成整个linux的config清单。

```shell
export ARCH=riscv
golem -e include/asm/uaccess.h.config5
```

理论上可以直接对这327个config进行扩展，得到linux的.config；但是这太多了，而且得到的.config们可能有重复的，所以需要做处理。

### 1-3 cover arch/riscv的最少config清单数

一个比较容易想到的strawman approach是：现在已知哪个配置组合可以cover哪个文件，那么如果配置组合A包含配置组合B，就可以把配置组合B所cover的文件放到配置组合A所cover的文件下面并把配置组合B删掉，这样能减少配置组合数。

实现脚本在[这里](00_riscv/code/config2files.py)。这一步可以从327个配置组合缩减到155个配置组合。接下来的缩减思路分为两种情况：

* 情况1：配置组合A和配置组合B中的config完全无交集，需要看看这两组配置组合能否合并？
* 情况2：配置组合A和配置组合B中的config有交集
  * 情况2-1：config在A中是y/m，而在B中是n，这意味着两个配置组合只能分别生成相应的linux .config。
  * 情况2-2：config在A和B中都是y/m，此时和情况1类似。

太复杂了....换个思路，先把管理arch/riscv的配置项中，取值单一的(y/n)给处理了，看看能不能打开/关闭，然后再去看取值y和n都有的，这一步的分析用[脚本](00_riscv/code/analyze_config.py)。












## 2 系统调用

一个思路：对于一个系统调用，能获得其所触发的addr，转换成file:line，然后看在不在arch/riscv下面，如果在的话，记录下来。然后在变异和生成的时候，疯狂往里插。
