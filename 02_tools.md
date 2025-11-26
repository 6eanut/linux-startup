## krepair

一个工具：接收一个配置项清单和一个补丁文件，生成若干配置项清单，这些配置项清单能够覆盖补丁文件所做的代码修改。

### 0 小试牛刀

生成patch文件：

```shell
git diff riscv-for-linus-6.18-rc6..riscv-for-linus-6.18-rc7 -- arch/riscv > rc6-rc7-riscv.diff
```

编译安装krepair：

```shell
sudo apt install -y python3-setuptools python3-dev openjdk-17-jdk
git clone https://github.com/paulgazz/kmax.git
cd kmax
python3 -m venv ~/kmax_env/
source ~/kmax_env/bin/activate
pip3 install ./
```

修复配置项：

```shell
klocalizer -v -a riscv --repair .config --include-mutex rc6-rc7.diff > klocalizer.log 2>&1
```

编译构建内核：

```shell
KCONFIG_CONFIG=./0-riscv.config make LLVM=1 ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- olddefconfig
KCONFIG_CONFIG=./0-riscv.config make LLVM=1 ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu-
```

结果：

编译出来的内核没法启动！

## ctags

一个工具：用于找到linux内核中所有的全局变量。

### 0 小试牛刀

安装：

```shell
sudo apt install universal-ctags
```

找到linux内核中的全局变量：

```shell
ctags -R --fields=+n --c-kinds=v --extras=+q .
# -R 递归扫描目录
# --fields=+n 让tags文件包含行号
# --c-kinds=v 让ctags记录变量(variable)
# --extras=+q 仅追踪定义的符号，声明类的不显示
# . 从当前目录开始
# 生成的结果文件在tags中
```
