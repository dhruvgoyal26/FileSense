"""
Tree Data Structure for representing hierarchical folder and file structures.
DSA-II Project Requirement: Tree Structure & Recursive Hierarchy.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Iterator
import os
from pathlib import Path


class TreeNode:
    """
    Node in the DirectoryTree representing either a folder or a file.
    
    DSA concept:
    - N-ary Tree Node
    - Stores parent-child pointers
    - Enables recursive traversal and hierarchical aggregation
    """

    def __init__(
        self,
        name: str,
        path: str,
        is_directory: bool = False,
        size: int = 0,
        parent: Optional[TreeNode] = None,
        file_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name: str = name
        self.path: str = os.path.normpath(path)
        self.is_directory: bool = is_directory
        self.size: int = size
        self.parent: Optional[TreeNode] = parent
        self.file_id: Optional[int] = file_id
        self.metadata: Dict[str, Any] = metadata or {}
        # Children mapped by child name for O(1) lookup
        self.children: Dict[str, TreeNode] = {}
        # Cached subtree size
        self._subtree_size: Optional[int] = None

    def add_child(self, child_node: TreeNode) -> TreeNode:
        """Add a child node to this node."""
        child_node.parent = self
        self.children[child_node.name] = child_node
        self.invalidate_size_cache()
        return child_node

    def remove_child(self, name: str) -> Optional[TreeNode]:
        """Remove a child by name."""
        if name in self.children:
            removed = self.children.pop(name)
            removed.parent = None
            self.invalidate_size_cache()
            return removed
        return None

    def get_child(self, name: str) -> Optional[TreeNode]:
        """Get direct child by name in O(1)."""
        return self.children.get(name)

    def get_sorted_children(self) -> List[TreeNode]:
        """
        Return children sorted folders-first, then alphabetically.
        Useful for UI tree representations.
        """
        return sorted(
            self.children.values(),
            key=lambda n: (not n.is_directory, n.name.lower()),
        )

    def invalidate_size_cache(self) -> None:
        """Invalidate cached subtree size up the parent chain."""
        self._subtree_size = None
        curr = self.parent
        while curr:
            curr._subtree_size = None
            curr = curr.parent

    def get_total_size(self) -> int:
        """
        Recursively compute total size of this node and all descendants.
        Uses caching for performance.
        """
        if not self.is_directory:
            return self.size

        if self._subtree_size is not None:
            return self._subtree_size

        total = 0
        for child in self.children.values():
            total += child.get_total_size()

        self._subtree_size = total
        return total

    def get_depth(self) -> int:
        """Calculate depth of this node from the root (root has depth 0)."""
        depth = 0
        curr = self.parent
        while curr:
            depth += 1
            curr = curr.parent
        return depth

    def traverse_preorder(self) -> Iterator[TreeNode]:
        """Preorder traversal (Parent first, then children)."""
        yield self
        for child in self.get_sorted_children():
            yield from child.traverse_preorder()

    def traverse_postorder(self) -> Iterator[TreeNode]:
        """Postorder traversal (Children first, then parent)."""
        for child in self.get_sorted_children():
            yield from child.traverse_postorder()
        yield self

    def count_descendants(self) -> tuple[int, int]:
        """
        Count (file_count, folder_count) in this subtree (excluding self).
        """
        files = 0
        folders = 0
        for node in self.traverse_preorder():
            if node is self:
                continue
            if node.is_directory:
                folders += 1
            else:
                files += 1
        return files, folders

    def to_dict(self) -> Dict[str, Any]:
        """Convert node and children to dictionary structure."""
        return {
            "name": self.name,
            "path": self.path,
            "is_directory": self.is_directory,
            "size": self.size,
            "total_size": self.get_total_size(),
            "file_id": self.file_id,
            "children": [c.to_dict() for c in self.get_sorted_children()],
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        kind = "Dir" if self.is_directory else "File"
        return f"<TreeNode({kind}, name='{self.name}', size={self.size}, children={len(self.children)})>"


class DirectoryTree:
    """
    High-level N-ary Tree structure representing a scanned root directory.
    
    Provides:
    - Quick node lookup by normalized path
    - Node insertion along path hierarchy
    - Preorder / Postorder / Level-order traversals
    - Aggregation metrics
    """

    def __init__(self, root_path: Optional[str] = None):
        self.root: Optional[TreeNode] = None
        self._path_map: Dict[str, TreeNode] = {}
        if root_path:
            self.set_root(root_path)

    def set_root(self, root_path: str) -> TreeNode:
        """Initialize or replace the root node."""
        norm_path = os.path.normpath(root_path)
        name = os.path.basename(norm_path) or norm_path
        self.root = TreeNode(
            name=name,
            path=norm_path,
            is_directory=True,
            size=0,
            parent=None,
        )
        self._path_map.clear()
        self._path_map[norm_path] = self.root
        return self.root

    def find_node(self, path: str) -> Optional[TreeNode]:
        """Find node by normalized path in O(1) via internal map."""
        norm_path = os.path.normpath(path)
        return self._path_map.get(norm_path)

    def insert_path(
        self,
        full_path: str,
        is_directory: bool,
        size: int = 0,
        file_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TreeNode:
        """
        Insert a node into the tree, automatically creating missing intermediate
        folder nodes if required.
        """
        norm_path = os.path.normpath(full_path)
        if norm_path in self._path_map:
            # Update existing
            node = self._path_map[norm_path]
            node.is_directory = is_directory
            node.size = size
            node.file_id = file_id
            if metadata:
                node.metadata.update(metadata)
            node.invalidate_size_cache()
            return node

        if not self.root:
            self.set_root(os.path.dirname(norm_path) or norm_path)

        parent_path = os.path.dirname(norm_path)
        parent_node = self.find_node(parent_path)

        # If parent does not exist, recursively insert parent folder
        if not parent_node and parent_path and parent_path != norm_path:
            parent_node = self.insert_path(parent_path, is_directory=True, size=0)

        if not parent_node:
            parent_node = self.root

        name = os.path.basename(norm_path) or norm_path
        new_node = TreeNode(
            name=name,
            path=norm_path,
            is_directory=is_directory,
            size=size,
            parent=parent_node,
            file_id=file_id,
            metadata=metadata,
        )

        parent_node.add_child(new_node)
        self._path_map[norm_path] = new_node
        return new_node

    def remove_path(self, path: str) -> Optional[TreeNode]:
        """Remove a node and all its descendants from tree and path map."""
        node = self.find_node(path)
        if not node:
            return None
        if node is self.root:
            self.root = None
            self._path_map.clear()
            return node

        # Remove all descendants from path map
        for desc in list(node.traverse_preorder()):
            self._path_map.pop(desc.path, None)

        if node.parent:
            node.parent.remove_child(node.name)
        return node

    def get_all_files(self) -> List[TreeNode]:
        """Return list of all file nodes in the tree."""
        if not self.root:
            return []
        return [n for n in self.root.traverse_preorder() if not n.is_directory]

    def get_all_folders(self) -> List[TreeNode]:
        """Return list of all folder nodes in the tree."""
        if not self.root:
            return []
        return [n for n in self.root.traverse_preorder() if n.is_directory]

    def count_nodes(self) -> tuple[int, int]:
        """Return (file_count, folder_count)."""
        if not self.root:
            return 0, 0
        files = 0
        folders = 0
        for n in self.root.traverse_preorder():
            if n.is_directory:
                folders += 1
            else:
                files += 1
        return files, folders

    def get_total_size(self) -> int:
        """Return total size of the entire tree."""
        if not self.root:
            return 0
        return self.root.get_total_size()
