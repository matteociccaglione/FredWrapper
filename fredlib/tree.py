import networkx as nx

class CategoryTree:
    class _Node:
        def __init__(self, category):
            self.value = category
            self.key = category.category_id
            self.parent = None

        def _add_parent(self, parent):
            self.parent = parent

        def _get_children(self):
            return self.children

        def _add_children(self, children):
            self.children = children

    def __init__(self, category_list):
        map_of_nodes = {}
        self._G = nx.DiGraph
        list_of_id = []
        for cat in category_list:
            node = self._Node(cat)
            self._G.add_node(cat.category_id)
            list_of_id.append(cat.category_id)
            if not (cat.parent_id in map_of_nodes.keys()):
                map_of_nodes[cat.parent_id] = []
            map_of_nodes[cat.parent_id].append(node)

        for key in map_of_nodes.keys():
            if not (key in list_of_id):
                # This is the parent of the root!!
                self.root = map_of_nodes[key][0]
                map_of_nodes.pop(key)
                list_of_id.remove(key)
                break
        parent = self.root
        list_of_parents = [parent]
        while len(list_of_parents) != 0:
            if not(list_of_parents[0].value.category_id in list_of_id):
                list_of_parents.pop(0)
                continue
            nodes = map_of_nodes[list_of_parents[0].value.category_id]
            for node in nodes:
                node._add_parent(list_of_parents[0])
                self._G.add_edge(list_of_parents[0].value.category_id,node.value.category_id)
            list_of_parents[0]._add_children(nodes)
            list_of_parents += nodes
            list_of_parents.pop(0)

    def __str__(self):
        nx.draw(self._G, arrows=True, with_labels=True)
