class Node:
    """
    Класс, описывающий узел дерева, содержащий всю необходимую информацию об элементе интерфейса
    """
    def __init__(self, tag_name, id_name, class_name, width, height, top, left, identifier=0):
        self.tag_name = tag_name
        self.id_name = id_name
        self.class_name = class_name
        self.width = width
        self.height = height
        self.top = top
        self.left = left
        self.children = []
        self.identifier = identifier

    def add_child(self, child):
        """ Функция, добавляющая узел (child) в список дочерних (children) """
        self.children.append(child)

    def description(self):
        """ Функция, выводящая инфо об узле """
        print(self.tag_name, self.id_name if self.id_name else "-", self.class_name if self.class_name else "-",
              "({}, {}, {}, {})".format(self.left, self.top, self.width, self.height), len(self.children),
              "#{}".format(self.identifier))


class Tree:
    """
    Класс, описывающий дерево элементов интерфейса
    """
    def __init__(self, root):
        self.root = root

    def draw_tree(self, element="", depth=0):
        """ Функция, выводящая форматированное инфо обо всех узлах дерева """
        if element == "":
            element = self.root
        print("\t" * depth, end="")
        element.description()
        for child in element.children:
            self.draw_tree(child, depth+1)

    def get_max_depth(self):
        """
        Функция, находящая максимальную глубину дерева элементов
        :return: максимальная глубина дерева элементов
        """
        max_depth = 0

        def get_max_depth(element, depth=0):
            nonlocal max_depth
            if depth > max_depth:
                max_depth = depth

            for child in element.children:
                get_max_depth(child, depth+1)

        get_max_depth(self.root)
        return max_depth





