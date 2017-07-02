from population_algorithms import PopulationAlgorithms
import random

MOVE_CHANCE = 0.3


class Charges(PopulationAlgorithms):
    """
    Класс, реализующий алгоритм поиска системой зарядов
    """
    def move_charges(self, tree, chance=MOVE_CHANCE):
        """
        Функция, выполняющая перемещение агентов популяции (случайное изменение положения элементов дерева)
        Используется в алгоритмах пчелиной колонии и поиска системой зарядов
        """
        def move(element):
            if len(element.children) > 1:
                if chance > random.random():
                    # Формируем случайные индексы из номеров дочерних узлов
                    index1 = random.randint(0, len(element.children)-1)
                    index2 = random.randint(0, len(element.children)-1)
                    while index1 == index2:
                        index2 = random.randint(0, len(element.children)-1)
                    # Меняем местрами элементы с установленными номерами, если это не пункты меню li
                    if not (element.children[index1].tag_name == "li" and element.children[index2].tag_name == "li"):
                        self.change_elements(element, index1, index2)

            for child in element.children:
                move(child)

        # Вызываем внутреннюю функцию, передавая ей корень дерева
        move(tree.root)







