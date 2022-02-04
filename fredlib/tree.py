import networkx as nx
from matplotlib import pyplot as plt
from collections import Iterable


class CategoryTree(Iterable):
    class _Node:
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
        map_of_nodes = {}
        self._G = nx.DiGraph(directed = True)
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
                if key == 0:
                    for node in map_of_nodes[key]:
                        if node.value.category_id == 0:
                            self.root = node
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
        queue = [self.root]

        while len(queue) > 0:
            yield queue[0]
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
        node = self.__get_node(category_id)
        if node is not None:
            list_of_nodes = self.__to_list(node)
            return CategoryTree(list_of_nodes)
        return None

    def __len__(self):
        return self.count

    def __str__(self):
        nx.draw(self._G, arrows=True, with_labels=True)
        plt.draw()
