"""Trie-based query autocomplete.

Stores past search queries in a prefix tree (Trie) and returns
frequency-ranked suggestions for a prefix. This is intentionally
independent of search/ranking/analytics — it only knows about query
strings and how often each was searched.
"""


def normalize(text):
    """Match the cache's query normalization: lowercase, collapse spaces."""
    return " ".join(text.lower().split())


class TrieNode:
    __slots__ = ("children", "is_query", "frequency", "last_searched")

    def __init__(self):
        self.children = {}
        # Whether a complete query ends at this node, and its stats.
        self.is_query = False
        self.frequency = 0
        self.last_searched = None


class QueryTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, query, frequency=1, last_searched=None):
        """Add a query (or bump its frequency by `frequency`)."""
        query = normalize(query)
        if not query:
            return

        node = self.root
        for char in query:
            node = node.children.setdefault(char, TrieNode())

        node.is_query = True
        node.frequency += frequency
        if last_searched is not None:
            node.last_searched = last_searched

    def _find_node(self, prefix):
        node = self.root
        for char in prefix:
            node = node.children.get(char)
            if node is None:
                return None
        return node

    def suggest(self, prefix, limit=5):
        """Return up to `limit` queries under `prefix`, most frequent first."""
        prefix = normalize(prefix)
        start = self._find_node(prefix)
        if start is None:
            return []

        # Collect every complete query in this subtree.
        matches = []  # (query_text, frequency)
        stack = [(start, prefix)]
        while stack:
            node, text = stack.pop()
            if node.is_query:
                matches.append((text, node.frequency))
            for char, child in node.children.items():
                stack.append((child, text + char))

        # Rank by frequency (desc), then alphabetically for stable ties.
        matches.sort(key=lambda item: (-item[1], item[0]))
        return [text for text, _ in matches[:limit]]
