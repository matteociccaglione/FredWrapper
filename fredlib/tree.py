"""
This module contains the CategoryTree class which can be used to represent a list of categories with a tree structure
"""

import networkx as nx
from matplotlib import pyplot as plt
from collections import Iterable






class CategoryTree(Iterable):
    """

    This class can be used to represent a list of categories with a tree structure

    """
    class _Node:
        """
        This class is private and undocumented, you must not use this class
        """

        def __init__(self, category):
            self.value = category
            self.key = category.category_id
            self.parent = None
            self.children = []

        def _add_parent(self, parent):
            self.parent = parent

        def _get_children(self):
            return self.children

        def _add_children(self, children):
            self.children = children

    def __init__(self, category_list):
        """
        Builder of the class. Do not use the constructor directly but use the from_list_to_tree function.

        :param category_list: A list of categories including the parent category (the root of this list)
        :type category_list: List[Category]
        """
        map_of_nodes = {}
        # self._G is used to build a printable tree
        self._G = nx.DiGraph(directed=True)
        self.count = len(category_list)
        list_of_id = []
        for cat in category_list:
            node = self._Node(cat)
            self._G.add_node(cat.category_id)
            list_of_id.append(cat.category_id)
            if not (cat.parent_id in map_of_nodes.keys()):
                map_of_nodes[cat.parent_id] = []
            map_of_nodes[cat.parent_id].append(node)

        for key in map_of_nodes.keys():
            if not (key in list_of_id) or key == 0:
                # This is the parent of the root!!
                if key == 0 and len(map_of_nodes[key]) > 1:
                    for node in map_of_nodes[key]:
                        if node.value.category_id == 0:
                            self.root = node
                            map_of_nodes[key].remove(node)
                            break
                else:
                    self.root = map_of_nodes[key][0]
                    map_of_nodes.pop(key)
                break
        parent = self.root
        list_of_parents = [parent]
        while len(list_of_parents) != 0:
            if not (list_of_parents[0].value.category_id in map_of_nodes.keys()):
                list_of_parents.pop(0)
                continue
            nodes = map_of_nodes[list_of_parents[0].value.category_id]
            for node in nodes:
                node._add_parent(list_of_parents[0])
                self._G.add_edge(list_of_parents[0].value.category_id, node.value.category_id)
            list_of_parents[0]._add_children(nodes)
            list_of_parents += nodes
            list_of_parents.pop(0)

    def __iter__(self):
        """
        Implement a BFS. You can use this method simply by iterating over the elements of the tree using a loop for example:
        for category in tree. Returns an object of type Category
        """
        queue = [self.root]

        while len(queue) > 0:
            yield queue[0].value
            node = queue.pop(0)
            queue.extend(node._get_children())

    def __get_node(self, item):
        queue = [self.root]
        while len(queue) > 0:
            for node in queue:
                if node.value.category_id == item:
                    return node
            new_queue = []
            for node in queue:
                new_queue.extend(node._get_children())
            queue = new_queue
        return None

    def __getitem__(self, item):
        """
        This method returns an object of type Category and can be used with the python [] operator, for example:
        root_category = tree [0]. Returns None if the category is not in the tree

        :param item: Must be the category_id of the category that you want to download
        :type item: int
        :return: The category requested, None if the category is not in the tree
        :rtype: Category
        """
        result = self.__get_node(item)
        if result is not None:
            return result.value
        return None

    def __to_list(self, root):
        list_of_parents = [root]
        list_of_nodes = []
        while len(list_of_parents) != 0:
            list_of_parents.extend(list_of_parents[0]._get_children())
            list_of_nodes.append(list_of_parents.pop(0).value)
        return list_of_nodes

    def subtree(self, category_id):
        """
        Use this method to build a subtree.

        :param category_id: The category_id of the root of the subtree
        :type category_id: int
        :return: A CategoryTree object representing the subtree, None if the category_id is not in the tree
        :rtype: CategoryTree
        """

        node = self.__get_node(category_id)
        if node is not None:
            list_of_nodes = self.__to_list(node)
            return CategoryTree(list_of_nodes)
        return None

    def __len__(self):
        return self.count

    def plot(self, fig_size=(14, 14), dpi:int=100, highlighted=None):
        """
        Use this method to print the entire tree on a graph. Each node of the tree will be represented by its category_id.
        The root of the tree is yellow, while the other nodes are blue.
        If you specify a highlighted value then the corresponding value will be red

        :param fig_size: A tuple representing the size of the matplotlib figure
        :type fig_size: (int,int)
        :param dpi: The dpi of the graph
        :type dpi: int
        :param highlighted: The category that you want to highlight, it will be drawn in red, defaults to None
        :type highlighted: Category
        """

        plt.figure(figsize=fig_size, dpi=dpi)
        color_map = []
        for node in self._G:
            if node == self.root.value.category_id:
                color_map.append("yellow")
                continue
            if highlighted is not None:
                if node == highlighted.category_id:
                    color_map.append("red")
                    continue
            color_map.append("blue")
        nx.draw(self._G, node_color=color_map, arrows=True, with_labels=True)
        plt.draw()
