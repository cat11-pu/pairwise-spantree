# pairwise-spantree

一个纯内存的并查集与最小生成树内核：路径压缩 + 按秩合并的并查集，
按边到达顺序增量加边的生成森林，以及按权重定序选边的 Kruskal。

- 只用 Python 标准库，不需要安装任何依赖，也不会发起任何网络请求。
- 不读时钟、不用随机数，同一组边的选取顺序唯一，任何一次运行的结果都是确定的。

## 目录

- spantree/core.py：内核实现（边、并查集、生成森林、Kruskal）
- tests/test_core.py：内核的行为测试

## 怎么跑测试

在项目根目录执行：

    python3 -m unittest discover -s tests -v

Windows 上把 python3 换成你的解释器路径，例如：

    C:/Users/<你>/AppData/Local/Programs/Python/Python313/python.exe -m unittest discover -s tests -v
