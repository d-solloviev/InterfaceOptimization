import math, os
from functools import partial
from PIL import ImageChops, Image
from heatmap import Heatmapper


class FitnessFunctions:
    @staticmethod
    def estimate_ff_value(tree, scale_x, scale_y, width, height, destination_heatmap, iteration):
        """ Функция, возвращаящая значение фитнесс-функции по различиям тепловых карт двух интерфейсов """
        # Внутренняя функция для получения точек интенсивности тепла не тепловой карте
        def get_points(child_tree, tree_root, heat_points, depth=0):
            max_depth = child_tree.get_max_depth()
            actual_depth = depth + (6 - max_depth)  # 6 - максимальное значение глубины для карты с 7 цветами
            # Добавляем точку в список вершин для построения тепловой карты
            if len(tree_root.children) == 0 and actual_depth >= 0:
                heat_points.append((int(tree_root.left / scale_x), int(tree_root.top / scale_y),
                                    int(tree_root.width / scale_x), int(tree_root.height / scale_y),
                                    actual_depth/6))
            for child in tree_root.children:
                get_points(child_tree, child, heat_points, depth+1)
            pass

        # Вызываем внутреннюю функция и получаем точки
        points = []
        get_points(tree, tree.root, points)

        # Формируем тепловую карту для дерева элементов
        _asset_file = partial(os.path.join, os.path.dirname(__file__), 'assets')
        image = Image.open(_asset_file('base.png'))
        image = image.resize((width, height))
        heatmap = Heatmapper(colours='default')
        heatmap = heatmap.heatmap_on_img(points, image)

        return FitnessFunctions.get_ff_value(destination_heatmap, heatmap)

    @staticmethod
    def get_ff_value(destination_heatmap, current_heatmap):
        """ Функция, вычисляющая значение фитнесс-функции по различиям тепловых карт двух интерфейсов """
        diff = ImageChops.difference(destination_heatmap, current_heatmap)
        h = diff.histogram()
        sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
        sum_of_squares = sum(sq)
        rms = math.sqrt(sum_of_squares / float(destination_heatmap.size[0] * destination_heatmap.size[1]))

        return rms

    @staticmethod
    def get_energy(tree, width, height):
        """ Функция, вычисляющая энергию взаимодействия системы зарядов """
        charges = []

        # Внутернняя функция, добваляющая элементы дерева в массив заярдов
        def add_charges(root_charge, depth=0):
            charges.append((root_charge.left, root_charge.top, root_charge.width, root_charge.height, depth))
            for charge in root_charge.children:
                add_charges(charge, depth+1)

        # Вызываем внутреннюю функцию и заполняем массив значениеми
        add_charges(tree.root)
        energy = 0

        for i in range(0, len(charges)):
            for j in range(i+1, len(charges)):
                charge1 = charges[i]
                charge2 = charges[j]

                # Расчёт значения заряда по размерам (длине и ширине) элемента и глубины в DOM дереве:
                # q = element.width * element.height * element.depth / (view.width * view.height) * 10
                q1 = int(charge1[2] * charge1[3] * charge1[4] * 100 / (width * height) * 20)
                q2 = int(charge2[2] * charge2[3] * charge2[4] * 100 / (width * height) * 20)

                # Расчёт расстояния между центрами элементов интерфейса
                r = int(math.sqrt(math.pow((charge1[0] + charge1[2] / 2 - charge2[0] - charge2[2] / 2), 2) +
                                  math.pow((charge1[1] + charge1[3] / 2 - charge2[1] - charge2[3] / 2), 2)))

                # Если расстояние между центрами не ноль, то прибавляем потенциал
                if r:
                    energy += q1 * q2 / r

        return energy

    @staticmethod
    def get_ff_value_charges(optimized_tree, width, height, initial_energy):
        """
        Функция, вычисляющая значение фитнесс-функции по различиям тепловых карт двух интерфейсов для алгоритма зарядов
        :return: значение фитнесс функции для алгоритма поиска системой зарядов
        """
        return math.fabs(FitnessFunctions.get_energy(optimized_tree, width, height) - initial_energy)

