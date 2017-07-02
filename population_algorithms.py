class PopulationAlgorithms:
    """
    Класс, реализующий основные операторы миграции агентов (элементов интерфейса), свойственные для все реализованных
    популяционных алгоритмов
    """
    def change_child_x(self, element, value):
        """ Функция, изменяющая координату x (left) всем дочерним узлам на указанное значение """
        element.left += value
        for child in element.children:
            self.change_child_x(child, value)

    def change_child_y(self, element, value):
        """ Функция, изменяющая координату y (top) всем дочерним узлам на указанное значение """
        element.top += value
        for child in element.children:
            self.change_child_y(child, value)

    def change_elements_x(self, elements, i, j):
        """ Функция, изменяющая положение i-ого и j-ого (и всех, что между ними) элементов списка children по оси x """
        if elements[i].left == elements[j].left:
            return
        min_x = min(elements[i].left, elements[j].left)
        max_x = max(elements[i].left, elements[j].left)
        if min_x == elements[i].left:
            correction = elements[j].width - elements[i].width
            for child in elements:
                if (child.left > min_x) and (child.left < max_x):
                    self.change_child_x(child, correction)
            self.change_child_x(elements[i], elements[j].left + correction - elements[i].left)
            self.change_child_x(elements[j], min_x - elements[j].left)
        else:
            correction = elements[i].width - elements[j].width
            for child in elements:
                if (child.left > min_x) and (child.left < max_x):
                    self.change_child_x(child, correction)
            self.change_child_x(elements[j], elements[i].left + correction - elements[j].left)
            self.change_child_x(elements[i], min_x - elements[i].left)

    def change_elements_y(self, elements, i, j):
        """ Функция, изменяющая положение i-ого и j-ого (и всех, что между ними) элементов списка children по оси y """
        if elements[i].top == elements[j].top:
            return
        min_y = min(elements[i].top, elements[j].top)
        max_y = max(elements[i].top, elements[j].top)
        if min_y == elements[i].top:
            correction = elements[j].height - elements[i].height
            for child in elements:
                if (child.top > min_y) and (child.top < max_y):
                    self.change_child_y(child, correction)
            self.change_child_y(elements[i], elements[j].top + correction - elements[i].top)
            self.change_child_y(elements[j], min_y - elements[j].top)
        else:
            correction = elements[i].height - elements[j].height
            for child in elements:
                if (child.top > min_y) and (child.top < max_y):
                    self.change_child_y(child, correction)
            self.change_child_y(elements[j], elements[i].top + correction - elements[j].top)
            self.change_child_y(elements[i], min_y - elements[i].top)

    def change_elements(self, element, i, j):
        """ Функция, изменяющая положение i-ого и j-ого (и всех, что между ними) элементов списка children """
        self.change_elements_x(element.children, i, j)
        self.change_elements_y(element.children, i, j)








