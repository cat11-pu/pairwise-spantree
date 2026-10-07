"""spantree：并查集与最小生成树内核。

组件：
    Edge                     一条带权无向边：u、v 与 weight
    make_edge                构造一条边，并把端点规范成 u <= v
    DisjointSet              并查集：路径压缩 + 按秩合并
    SpanningForest           按边到达顺序增量加边的生成森林
    kruskal                  按 (权重, u, v) 升序选边，得到最小生成森林
    minimum_spanning_weight  最小生成森林的总权重

约定：
    * 顶点用 0..size-1 的整数编号，边一律无向，端点规范成 u <= v；
    * 选边顺序唯一：先按权重升序，权重并列按 u 升序，再并列按 v 升序，
      所以同一组边无论以什么顺序给出，选出的森林完全相同；
    * 只接受连接两个不同分量的边：接受一条边就合并这两个分量，因此已接受
      的边两两不成环，边数等于顶点数减去连通分量数，每个分量接受的边数
      等于该分量的顶点数减一；
    * 并查集按秩合并（秩是树高的上界，秩为 r 的树至少有 2 的 r 次方个顶点），
      查找之后查找路径上的顶点都直接挂在代表元上；
    * 全程只依赖入参与内部状态：不读文件、不打印、不读时钟、不用随机数，
      同一组输入永远得到同一份结果。
"""

__all__ = ["Edge", "make_edge", "DisjointSet", "SpanningForest",
           "kruskal", "minimum_spanning_weight"]


def _require_int(value, label):
    """要求 value 是整数（布尔不算整数）。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s 必须是整数" % (label,))
    return value


class Edge:
    """一条带权无向边。u、v 是顶点编号，weight 是权重。"""

    __slots__ = ("u", "v", "weight")

    def __init__(self, u, v, weight):
        self.u = _require_int(u, "u")
        self.v = _require_int(v, "v")
        self.weight = _require_int(weight, "weight")

    def endpoints(self):
        """两个端点。"""
        return (self.u, self.v)

    def key(self):
        """选边顺序的排序键：先权重，再 u，再 v。"""
        return (self.weight, self.u, self.v)

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return self.key() == other.key()

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __lt__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return self.key() < other.key()

    def __hash__(self):
        return hash(self.key())

    def __repr__(self):
        return "Edge(u=%d, v=%d, weight=%d)" % (self.u, self.v, self.weight)


def make_edge(u, v, weight):
    """构造一条无向边，并把端点规范成 u <= v。"""
    _require_int(u, "u")
    _require_int(v, "v")
    _require_int(weight, "weight")
    if u > v:
        u, v = v, u
    return Edge(u, v, weight)


class DisjointSet:
    """并查集：按秩合并 + 路径压缩。

    size 个顶点，编号 0..size-1，初始时各自独立成一个分量。
    """

    def __init__(self, size):
        _require_int(size, "size")
        if size < 0:
            raise ValueError("size 不能为负: %r" % (size,))
        self._size = size
        self.parent = list(range(size))
        self.rank = [0] * size

    def size(self):
        """顶点数。"""
        return self._size

    def _node(self, node):
        """校验顶点编号落在 0..size-1 内。"""
        _require_int(node, "顶点编号")
        if not 0 <= node < self._size:
            raise ValueError("顶点编号越界: %r" % (node,))
        return node

    def find(self, node):
        """返回 node 所在分量的代表元，并把查找路径上的顶点都直接挂到它下面。"""
        self._node(node)
        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while node != root:
            next_node = self.parent[node]
            self.parent[node] = root
            node = next_node
        return root

    def union(self, x, y):
        """合并 x 与 y 所在的两个分量；返回是否真的发生了合并。"""
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return False
        if self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        elif self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        return True

    def connected(self, x, y):
        """x 与 y 是否在同一个连通分量里。"""
        return self.find(x) == self.find(y)

    def roots(self):
        """所有分量的代表元（升序列表）。"""
        return sorted({self.find(node) for node in range(self._size)})

    def component_count(self):
        """当前连通分量数。"""
        return len(self.roots())

    def component_of(self, node):
        """node 所在分量的全部顶点（升序元组）。"""
        root = self.find(node)
        return tuple(item for item in range(self._size) if self.find(item) == root)

    def parent_of(self, node):
        """node 当前的父顶点（不改动结构）。"""
        return self.parent[self._node(node)]

    def rank_of(self, node):
        """node 所在分量的秩。"""
        return self.rank[self.find(node)]

    def depth(self, node):
        """node 走到代表元的步数（不改动结构）。"""
        self._node(node)
        steps = 0
        while self.parent[node] != node:
            node = self.parent[node]
            steps += 1
        return steps

    def max_depth(self):
        """所有顶点深度的最大值。"""
        if self._size == 0:
            return 0
        return max(self.depth(node) for node in range(self._size))

    def path_to_root(self, node):
        """node 到代表元的完整路径（含两端，不改动结构）。"""
        self._node(node)
        path = [node]
        while self.parent[node] != node:
            node = self.parent[node]
            path.append(node)
        return path


class SpanningForest:
    """按边到达顺序增量加边得到的生成森林。

    只接受连接两个不同分量的边，被拒绝的边单独留存，便于核对。
    """

    def __init__(self, size):
        self._size = size
        self._ds = DisjointSet(size)
        self._edges = []
        self._rejected = []

    def size(self):
        """顶点数。"""
        return self._size

    def would_close_cycle(self, u, v):
        """在当前森林里再连一条 (u, v) 会不会成环。"""
        return self._ds.connected(u, v)

    def add_edge(self, u, v, weight):
        """按到达顺序增量加边；返回是否接受（两端此前不连通才接受）。"""
        edge = make_edge(u, v, weight)
        if self.would_close_cycle(edge.u, edge.v):
            self._rejected.append(edge)
            return False
        self._edges.append(edge)
        self._ds.union(edge.u, edge.v)
        return True

    def edges(self):
        """已接受的边，按到达顺序。"""
        return list(self._edges)

    def rejected(self):
        """被拒绝的边，按到达顺序。"""
        return list(self._rejected)

    def total_weight(self):
        """已接受边的权重之和。"""
        return sum(edge.weight for edge in self._edges)

    def component_count(self):
        """当前连通分量数。"""
        return self._ds.component_count()

    def connected(self, u, v):
        """当前森林里 u 与 v 是否连通。"""
        return self._ds.connected(u, v)


def kruskal(size, edges):
    """按 (权重, u, v) 升序依次选边，返回最小生成森林。"""
    forest = SpanningForest(size)
    ordered = sorted(edges, key=lambda item: item.key())
    for edge in ordered:
        forest.add_edge(edge.u, edge.v, edge.weight)
    return forest


def minimum_spanning_weight(size, edges):
    """最小生成森林的总权重。"""
    return kruskal(size, edges).total_weight()
