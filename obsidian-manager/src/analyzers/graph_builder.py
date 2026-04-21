from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class GraphNode:
    name: str
    tags: list[str] = field(default_factory=list)
    word_count: int = 0
    in_degree: int = 0
    out_degree: int = 0


class NoteGraph:
    """Lightweight directed graph for note connections (no networkx required)."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[tuple[str, str]] = []
        self._adj: dict[str, list[str]] = defaultdict(list)
        self._rev_adj: dict[str, list[str]] = defaultdict(list)

    def add_node(self, name: str, tags: list[str], word_count: int) -> None:
        self.nodes[name] = GraphNode(name=name, tags=tags, word_count=word_count)

    def add_edge(self, src: str, dst: str) -> None:
        if src not in self.nodes or dst not in self.nodes:
            return
        self.edges.append((src, dst))
        self._adj[src].append(dst)
        self._rev_adj[dst].append(src)
        self.nodes[src].out_degree += 1
        self.nodes[dst].in_degree += 1

    def find_hubs(self, top_n: int = 5) -> list[tuple[str, int]]:
        """Return top_n nodes by in-degree (backlink count)."""
        ranked = sorted(self.nodes.values(), key=lambda n: n.in_degree, reverse=True)
        return [(n.name, n.in_degree) for n in ranked[:top_n]]

    def bfs_related(self, start: str, max_depth: int = 3) -> list[tuple[str, int]]:
        """BFS from start node, returns (node_name, depth) pairs."""
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        result: list[tuple[str, int]] = []
        while queue:
            current, depth = queue.popleft()
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            result.append((current, depth))
            for neighbour in self._adj.get(current, []) + self._rev_adj.get(current, []):
                if neighbour not in visited:
                    queue.append((neighbour, depth + 1))
        return result

    def detect_clusters_simple(self) -> dict[str, list[str]]:
        """Cluster by dominant tag prefix (simple non-ML fallback)."""
        clusters: dict[str, list[str]] = defaultdict(list)
        for name, node in self.nodes.items():
            if node.tags:
                # Use first tag's top-level as cluster key
                prefix = node.tags[0].lstrip("#").split("/")[0]
            else:
                prefix = "без_тегов"
            clusters[prefix].append(name)
        return dict(clusters)

    @property
    def stats(self) -> dict[str, int]:
        return {
            "total_notes": len(self.nodes),
            "total_edges": len(self.edges),
        }
