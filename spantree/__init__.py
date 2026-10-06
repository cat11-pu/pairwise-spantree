"""spantree：并查集与最小生成树内核。

对外入口：
    DisjointSet              并查集：路径压缩 + 按秩合并
    SpanningForest           按边到达顺序增量加边的生成森林
    Edge                     一条带权无向边
    make_edge                构造并规范化一条边
    kruskal                  按权重升序选边，得到最小生成森林
    minimum_spanning_weight  最小生成森林的总权重
"""

from .core import (DisjointSet, Edge, SpanningForest, kruskal, make_edge,
                   minimum_spanning_weight)

__all__ = ["DisjointSet", "Edge", "SpanningForest", "kruskal", "make_edge",
           "minimum_spanning_weight"]
