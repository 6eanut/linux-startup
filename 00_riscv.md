# arch/riscv

## 1 配置项

目标是生成一系列配置项清单，这些配置项清单能cover住arch/riscv下的所有代码

### 1-1 undertaker工具

这是一个开源项目：[https://github.com/6eanut/original-undertaker-tailor](https://github.com/6eanut/original-undertaker-tailor)

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

### 1-2 cover每个文件所需要的config清单

undertaker的coverage功能能够生成若干config清单，这些清单的总和能够cover这个文件的所有代码，我这里写了一个脚本来完成这个事情，见[这里](00_riscv/code/configs_cover_file.sh)。

它的执行流程是这样的：

* 识别出arch/riscv目录下的所有.S, .c, .h文件，然后对其执行undertaker的coverage功能，这会在.S, .c, .h文件所在的路径下生成xxx.configx配置项清单；
* 该配置项清单会包含一些其他宏定义，所以需要扔掉，只保留CONFIG_XXX相关的，并且把这些配置项清单挪到一个干净的目录下，便于后续进行分析。

结果大致是[这样](00_riscv/code/configs_cover_file_result.txt)的。

## 2 系统调用
