"""spantree.core 的行为测试：并查集合并、环检测、Kruskal 选边与连通性查询。"""

import unittest

from spantree.core import (DisjointSet, Edge, SpanningForest, kruskal,
                           make_edge, minimum_spanning_weight)


def _independent_forest_weight(size, edges):
    """独立复算最小生成森林的总权重：枚举全部边子集，取最小者。"""
    best = None
    for mask in range(1 << len(edges)):
        chosen = [edge for index, edge in enumerate(edges) if mask & (1 << index)]
        weight = _spanning_forest_weight(size, edges, chosen)
        if weight is not None and (best is None or weight < best):
            best = weight
    return best


def _spanning_forest_weight(size, edges, chosen):
    """chosen 是生成森林时返回它的总权重，否则返回 None。"""
    parent = list(range(size))

    def root(node):
        while parent[node] != node:
            node = parent[node]
        return node

    weight = 0
    for edge in chosen:
        left = root(edge.u)
        right = root(edge.v)
        if left == right:
            return None
        parent[left] = right
        weight += edge.weight
    for edge in edges:
        if root(edge.u) != root(edge.v):
            return None
    return weight


class SpanTreeCoreTest(unittest.TestCase):
    """覆盖并查集、生成森林、最小生成森林与非法输入。"""

    def test_union_merges_components_and_reports_count(self):
        """每合并一次分量数减一，合并完的分量成员与代表元要能对上。"""
        ds = DisjointSet(8)
        self.assertTrue(ds.union(0, 1))
        self.assertTrue(ds.union(2, 3))
        self.assertTrue(ds.union(0, 2))
        self.assertEqual(ds.component_count(), 5)
        self.assertEqual(ds.roots(), [0, 4, 5, 6, 7])
        self.assertFalse(ds.union(3, 3))
        self.assertEqual(ds.component_of(3), (0, 1, 2, 3))
        self.assertEqual(ds.component_of(6), (6,))
        self.assertEqual(ds.component_count(), 5)
        with self.assertRaises(ValueError):
            ds.find(8)

    def test_find_compresses_every_node_on_the_path(self):
        """查找之后，查找路径上的每个顶点都要直接挂在代表元下面。"""
        ds = DisjointSet(16)
        for pair in ((0, 2), (4, 6), (0, 4), (8, 10), (12, 14), (8, 12), (0, 8)):
            self.assertTrue(ds.union(*pair))
        path = ds.path_to_root(14)
        self.assertGreaterEqual(len(path), 4)
        root = ds.find(14)
        self.assertEqual(root, path[-1])
        for node in path:
            self.assertEqual(ds.parent_of(node), root)
        self.assertEqual(ds.depth(14), 1)

    def test_union_by_rank_keeps_trees_shallow(self):
        """按秩合并之后，树高要有对数上界，不能退化成一条长链。"""
        ds = DisjointSet(64)
        for step in range(63):
            self.assertTrue(ds.union(step, step + 1))
        self.assertLessEqual(ds.max_depth(), 6)
        self.assertEqual(ds.component_count(), 1)
        self.assertEqual(ds.find(0), ds.find(63))

    def test_connected_covers_the_whole_component(self):
        """连通性查询要认整个分量，不能只看谁是代表元。"""
        ds = DisjointSet(8)
        ds.union(0, 1)
        ds.union(2, 3)
        ds.union(0, 2)
        self.assertTrue(ds.connected(1, 3))
        self.assertTrue(ds.connected(3, 1))
        self.assertTrue(ds.connected(2, 2))
        self.assertTrue(ds.connected(0, 3))
        self.assertFalse(ds.connected(0, 4))
        self.assertFalse(ds.connected(6, 7))

    def test_make_edge_normalises_endpoints(self):
        """端点的先后顺序不影响这条边，排序键也要用规范后的端点。"""
        forward = make_edge(2, 7, 5)
        backward = make_edge(7, 2, 5)
        self.assertEqual(forward.endpoints(), (2, 7))
        self.assertEqual(backward.endpoints(), (2, 7))
        self.assertEqual(forward, backward)
        self.assertEqual(forward.key(), (5, 2, 7))
        with self.assertRaises(TypeError):
            make_edge(0, 1, "5")
        with self.assertRaises(TypeError):
            make_edge(0, 1.0, 5)

    def test_kruskal_builds_a_minimum_spanning_forest(self):
        """选边结果要正好是那五条，总权重与边数都按森林的口径。"""
        edges = [make_edge(0, 1, 1), make_edge(1, 2, 2), make_edge(2, 3, 2),
                 make_edge(0, 3, 3), make_edge(2, 5, 3), make_edge(3, 4, 4),
                 make_edge(4, 5, 5)]
        forest = kruskal(6, edges)
        chosen = [(edge.u, edge.v, edge.weight) for edge in forest.edges()]
        self.assertEqual(chosen, [(0, 1, 1), (1, 2, 2), (2, 3, 2),
                                  (2, 5, 3), (3, 4, 4)])
        self.assertTrue(all(isinstance(edge, Edge) for edge in forest.edges()))
        self.assertEqual(forest.total_weight(), 12)
        self.assertEqual(len(forest.edges()), 6 - forest.component_count())
        self.assertEqual(forest.component_count(), 1)
        self.assertTrue(forest.connected(0, 5))

    def test_incremental_add_edge_rejects_cycles(self):
        """成环的边要被拒绝并留档，被接受的边要真的把分量并起来。"""
        forest = SpanningForest(5)
        self.assertTrue(forest.add_edge(0, 1, 4))
        self.assertTrue(forest.add_edge(1, 2, 1))
        self.assertTrue(forest.add_edge(3, 4, 2))
        self.assertFalse(forest.add_edge(0, 2, 7))
        self.assertFalse(forest.add_edge(4, 3, 9))
        self.assertEqual([(edge.u, edge.v, edge.weight) for edge in forest.edges()],
                         [(0, 1, 4), (1, 2, 1), (3, 4, 2)])
        self.assertEqual([(edge.u, edge.v, edge.weight) for edge in forest.rejected()],
                         [(0, 2, 7), (3, 4, 9)])
        self.assertEqual(forest.total_weight(), 7)
        self.assertEqual(forest.component_count(), 2)
        self.assertTrue(forest.connected(1, 2))
        self.assertTrue(forest.connected(3, 4))
        self.assertFalse(forest.connected(2, 3))

    def test_minimum_spanning_weight_matches_independent_recompute(self):
        """总权重必须等于独立复算出来的最小值，不能把便宜的边直接相加。"""
        edges = [make_edge(0, 1, 1), make_edge(1, 2, 1), make_edge(2, 0, 1),
                 make_edge(0, 3, 4), make_edge(3, 4, 10)]
        expected = _independent_forest_weight(5, edges)
        self.assertEqual(expected, 16)
        self.assertEqual(minimum_spanning_weight(5, edges), expected)
        self.assertEqual(kruskal(5, edges).total_weight(), expected)

    def test_ties_and_input_order_give_the_same_forest(self):
        """权重并列时按端点定序，同一组边换个输入顺序结果要完全一样。"""
        edges = [make_edge(0, 1, 1), make_edge(1, 3, 1), make_edge(3, 2, 1),
                 make_edge(2, 0, 1), make_edge(0, 3, 5)]
        expected = [(0, 1, 1), (0, 2, 1), (1, 3, 1)]
        for order in (edges, list(reversed(edges))):
            forest = kruskal(4, order)
            chosen = [(edge.u, edge.v, edge.weight) for edge in forest.edges()]
            self.assertEqual(chosen, expected)
            self.assertEqual(forest.total_weight(), 3)
            self.assertEqual(forest.component_count(), 1)


if __name__ == "__main__":
    unittest.main()
