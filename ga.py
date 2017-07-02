import random, copy
from population_algorithms import PopulationAlgorithms
from fitness_functions import FitnessFunctions

MUTATE_CHANCE = 0.3
PRINT_INFO = 0


class GA(PopulationAlgorithms):
    """
    Класс, реализующий генетический алгоритм с основными операторами: скрещиванием и мутациями
    """
    def mutation(self, tree, chance):
        """ Функция, выпролняющая мутацию (случайное изменение положения элементов дерева) """
        def check_children(element):
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
                check_children(child)

        # Вызываем внутреннюю функцию, передавая ей корень дерева
        check_children(tree.root)

    def crossing_over(self, tree1, tree2):
        """ Функция, выполняющая кроссинговер (обмен свойств расположения элеметов между двумя деревьями) """
        def modify_child(result_element, element2):
            # С шансом 50% берём свойства (позиционирование всех дочерних элементов для result_element) от element2
            if random.random() > 0.5:
                for result_child in result_element.children:
                    for child2 in element2.children:
                        if result_child.identifier == child2.identifier:
                            self.change_child_x(result_child, child2.left-result_child.left)
                            self.change_child_y(result_child, child2.top-result_child.top)
            # Если не берём свойства от element2 - то изменяем позиционирование его дочерних элементов
            else:
                for result_child in result_element.children:
                    for child2 in element2.children:
                        if result_child.identifier == child2.identifier:
                            self.change_child_x(child2, result_child.left-child2.left)
                            self.change_child_y(child2, result_child.top-child2.top)

            for result_child in result_element.children:
                for child2 in element2.children:
                    if result_child.identifier == child2.identifier:
                        # Рекурсивно вызываем функцию
                        modify_child(result_child, child2)

        # Создаём 3 дерева, которые будут потомками от двух деревьев-родителей tree1 и tree2 и формируем их структуру
        child_trees = [copy.deepcopy(tree1), copy.deepcopy(tree1), copy.deepcopy(tree1)]
        for result_tree in child_trees:
            modify_child(result_tree.root, copy.deepcopy(tree2.root))

        return child_trees

    def evolution(self, three_parents, scale_x, scale_y, width, height, destination_heatmap, iteration):
        """ Основной процесс рабоыт генетического алгоритма """
        # =========================================================================================================
        # 1. Запускаем скрещивание с возможными вариантами родителей (3 родителя => 3 комбинации => 9 вариантов)
        # =========================================================================================================
        child_trees = []
        for i in range(0, len(three_parents)):
            for j in range(i + 1, len(three_parents)):
                child_trees.extend(self.crossing_over(three_parents[i], three_parents[j]))

        # =========================================================================================================
        # 2. Запускаем случайные мутации для полученных вариантов
        # (шанс мутации: MUTATE_CHANCE, шанс изменения внешнего вида на каждом уровне дерева - тоже MUTATE_CHANCE)
        # =========================================================================================================
        for child in child_trees:
            if random.random() < MUTATE_CHANCE:
                self.mutation(child, MUTATE_CHANCE)

        # =========================================================================================================
        # 3. Оцениваем приспособленность всех особей с помощью тепловой карты
        # =========================================================================================================
        number = 1
        child_trees_ff_values = []
        for child_tree in child_trees:
            ff_value = FitnessFunctions.estimate_ff_value(child_tree, scale_x, scale_y, width, height,
                                                          destination_heatmap, iteration)
            child_trees_ff_values.append(ff_value)
            if PRINT_INFO:
                print("Child {} FF value:".format(number), ff_value)
            number += 1

        # =========================================================================================================
        # 4. Производим селекцию, оставляя лишь 3 из 9 особей (2 с лучшим показателем FF и 1 случайную)
        # =========================================================================================================
        first_new_parent_index = child_trees_ff_values.index(min(child_trees_ff_values))
        child_trees_ff_values.pop(first_new_parent_index)
        second_new_parent_index = child_trees_ff_values.index(min(child_trees_ff_values))
        # Увеличиваем значение индекса на 1, если второй максимальный элемент был за первым (т.к. первый мы удалили)
        if second_new_parent_index >= first_new_parent_index:
            second_new_parent_index += 1
        third_new_parent_index = random.randint(0, len(child_trees) - 1)
        while third_new_parent_index == first_new_parent_index or third_new_parent_index == second_new_parent_index:
            third_new_parent_index = random.randint(0, len(child_trees) - 1)

        if PRINT_INFO:
            print("New parent indexes:", first_new_parent_index, second_new_parent_index, third_new_parent_index)
            print()

        # =========================================================================================================
        # 5. Формируем новых родителей
        # =========================================================================================================
        new_parents = [child_trees[first_new_parent_index], child_trees[second_new_parent_index],
                       child_trees[third_new_parent_index]]

        # =========================================================================================================
        # 6. Возвращаем сформированных родителей
        # =========================================================================================================
        return new_parents








