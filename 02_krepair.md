# krepair

## 0 小试牛刀

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
