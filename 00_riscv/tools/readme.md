## Tools

**00 score config**

* [script](00_score_config.py)
* 给配置项清单打分：修改脚本中的配置项清单路径和Linux源码路径。能够计算在指定的Linux源码路径下的所有.c, .S, .h文件中
  * 总代码行数有多少/非空行有多少；
  * 文件数有多少；
  * 在被配置项管理的代码中，对于给定的配置项清单：
    * 被编译进内核的代码有多少；
    * 没有被编译进内核的代码有多少；
    * 以及统计数据：
      * 某个配置项被设置成y/n，导致：
        * 多少行代码被编译进内核；
        * 多少行代码没有被编译进内核。

**01 kernel function 2 syscall**

* [script00](01_00_find_kernelfunction_callers.py)
* 对于一个给定的内核函数，找到哪些函数会调用该内核函数：
  * 输入：`python script.py 要分析的内核函数名称 -s 指定内核源码路径 -d 递归查找的深度`
  * 输出：
    * 一个调用图，dot/png/json格式；
    * 一个分析过程，analysis.log；
    * 黄色是要分析的内核函数，蓝色是syscall_define。
* [script01](01_01_extract_syscall.py)
* 对上一步得到的dot文件做进一步的处理，因为上一步得到的png图可能太密了，啥也看不清，此时可以用这个脚本把syscall_define相关的提取出来
  * 输入：`python3 script.py -i out/callgraph.dot -o out/syscalls.dot -p out/syscalls.png`
  * 这样分析就方便多了

**02 find the common caller of func1 and func2**

* [script](02_our_caller.py)
* 想要知道内核中的两个内核函数是否会被同一内核函数先后调用，以及调用链：
  * 输入：python script.py func1 func2
  * 输出：
    * func1和func2各自的调用链；
    * 共同的调用链。
