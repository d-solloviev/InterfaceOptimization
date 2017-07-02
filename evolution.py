from PyQt5.QtCore import QThread
from time import sleep
import copy

from ga import GA
from bees import Bees
from charges import Charges

MUTATE_CHANCE = 0.3
MAX_COUNT_ITERATIONS = 99
MAX_COUNT_USELESS_ITERATIONS = 49
MAX_FF_DIFFERENCE = 10
SAVE_HEATMAP = 0


class EvolutionThread(QThread):
    """
    Класс, реализующий отдельный поток выполнения выбранного алгоритма оптимизации
    """
    def __init__(self, garnet_blocks):
        super(EvolutionThread, self).__init__()
        self.garnet_blocks = garnet_blocks

    def start_ga(self):
        """ Функция, запускающая оптимизацию с помощью генетического алгоритма """
        ga = GA()

        # Принимаем первым родителем тестируемый интерфейс, вторым - его мутированную версию
        other_parent = copy.deepcopy(self.garnet_blocks.optimized_tree)
        ga.mutation(other_parent, MUTATE_CHANCE)

        # Выполняем скрещивание выбранных родителей и получаем 3 новых варианта
        three_parents = ga.crossing_over(self.garnet_blocks.optimized_tree, other_parent)

        # Сохраняем изображения на диск, если требуется
        heatmap_number = 1
        if SAVE_HEATMAP:
            self.save_generation_heatmaps(three_parents, heatmap_number)
        heatmap_number += 1

        # Получаем 3 новых варианта дочерних деревьев из 3-х с помощью ГА
        new_parents = ga.evolution(three_parents, self.garnet_blocks.optimized_scale_x,
                                   self.garnet_blocks.optimized_scale_y, self.garnet_blocks.ui.optimizedView.width(),
                                   self.garnet_blocks.ui.optimizedView.height(), self.garnet_blocks.destination_heatmap,
                                   heatmap_number)
        if SAVE_HEATMAP:
            self.save_generation_heatmaps(new_parents, heatmap_number)
        heatmap_number += 1
        self.garnet_blocks.optimized_tree = new_parents[0]
        self.garnet_blocks.events.generation_completed.emit("ga")

        # Продолжаем эволюцию, пока не выполнится одно из условий окончиния:
        # 1. Превышено максимальное количество итераций
        # 2. Превышено максимальное количество итераций, в течение которых результат не улучшился
        # 3. Найден результат с допустимым значением фитнесс-функции
        while self.garnet_blocks.count_iterations < MAX_COUNT_ITERATIONS and \
                self.garnet_blocks.count_useless_iterations < MAX_COUNT_USELESS_ITERATIONS and \
                self.garnet_blocks.best_ff_value > MAX_FF_DIFFERENCE:
            # Получаем 3 новых варианта дочерних деревьев из 3-х с помощью ГА
            new_parents = ga.evolution(three_parents, self.garnet_blocks.optimized_scale_x,
                                       self.garnet_blocks.optimized_scale_y,
                                       self.garnet_blocks.ui.optimizedView.width(),
                                       self.garnet_blocks.ui.optimizedView.height(),
                                       self.garnet_blocks.destination_heatmap, heatmap_number)
            if SAVE_HEATMAP:
                self.save_generation_heatmaps(new_parents, heatmap_number)
            heatmap_number += 1
            self.garnet_blocks.optimized_tree = new_parents[0]
            self.garnet_blocks.events.generation_completed.emit("ga")

        # Показываем лучший из найденных
        self.garnet_blocks.optimized_tree = copy.deepcopy(self.garnet_blocks.best_tree)
        self.garnet_blocks.events.generation_completed.emit("ga")

    def start_bees(self):
        """ Функция, запускающая оптимизацию с помощью алгоритма пчелиной колонии """
        bees = Bees()

        # Продолжаем перемещение, пока не выполнится одно из условий окончиния:
        # 1. Превышено максимальное количество итераций
        # 2. Превышено максимальное количество итераций, в течение которых результат не улучшился
        # 3. Найден результат с допустимым значением фитнесс-функции
        while self.garnet_blocks.count_iterations < MAX_COUNT_ITERATIONS and \
                self.garnet_blocks.count_useless_iterations < MAX_COUNT_USELESS_ITERATIONS and \
                self.garnet_blocks.best_ff_value > MAX_FF_DIFFERENCE:
            # Получаем 3 новых варианта дочерних деревьев из 3-х с помощью алгоритма пчелиной колонии
            bees.move_bees(self.garnet_blocks.optimized_tree)
            self.garnet_blocks.events.generation_completed.emit("bees")
            sleep(1)

        # Показываем лучший из найденных
        self.garnet_blocks.optimized_tree = copy.deepcopy(self.garnet_blocks.best_tree)
        self.garnet_blocks.events.generation_completed.emit("bees")

    def start_charges(self):
        """ Функция, запускающая оптимизацию с помощью алгоритма поиска системой зарядов """
        charges = Charges()

        # Продолжаем перемещение, пока не выполнится одно из условий окончиния:
        # 1. Превышено максимальное количество итераций
        # 2. Превышено максимальное количество итераций, в течение которых результат не улучшился
        # 3. Найден результат с допустимым значением фитнесс-функции
        while self.garnet_blocks.count_iterations < MAX_COUNT_ITERATIONS and \
                self.garnet_blocks.count_useless_iterations < MAX_COUNT_USELESS_ITERATIONS and \
                self.garnet_blocks.best_ff_value > MAX_FF_DIFFERENCE:
            # Получаем 3 новых варианта дочерних деревьев из 3-х с помощью алгоритма системы зарядов
            charges.move_charges(self.garnet_blocks.optimized_tree)
            self.garnet_blocks.events.generation_completed.emit("charges")
            sleep(1)

        # Показываем лучший из найденных
        self.garnet_blocks.optimized_tree = copy.deepcopy(self.garnet_blocks.best_tree)
        self.garnet_blocks.events.generation_completed.emit("charges")

    def save_generation_heatmaps(self, trees, heatmap_number):
        """
        Функция, выполняющая сохранение изображений тепловых карт на диск
        :param trees: список деревьев, описывающих различные варианты интерфейса, по которым строятся тепловые карты
        :param heatmap_number: номер поколения интерфейсов, отражённый названии сохранённого файла
        """
        child_number = 0
        for tree in trees:
            self.garnet_blocks.save_heatmap(tree, "heatmap{}-{}".format(heatmap_number, child_number))
            child_number += 1

    def run(self):
        """ Запуск выбранного алгоритма оптимизации согласно radioButton """
        # В зависимости от выбранного radio_button, выполняем эволюцию тем или иным алгоритмом
        if self.garnet_blocks.ui.gaRadioButton.isChecked():
            self.start_ga()
        elif self.garnet_blocks.ui.beesRadioButton.isChecked():
            self.start_bees()
        elif self.garnet_blocks.ui.chargesRadioButton.isChecked():
            self.start_charges()
