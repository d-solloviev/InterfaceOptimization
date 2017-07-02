import sys, os, copy, json
from functools import partial

from PIL import Image, ImageQt
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QPixmap

from heatmap import Heatmapper
from node import Node, Tree
from user_interface import UiMainWindow
from evolution import EvolutionThread
from fitness_functions import FitnessFunctions

PRINT_INFO = 0


class InterfaceOptimization:
    """
    Класс, реализующий пользовательский интерфейс и обработчики событий от него
    """
    def __init__(self):
        # Создаём графический пользовательский интерфейс программы при помощи PyQt
        app = QtWidgets.QApplication(sys.argv)
        self.main_window = QtWidgets.QMainWindow()
        self.ui = UiMainWindow()
        self.ui.setupUi(self.main_window)
        self.main_window.show()

        # Инициализируем в конструкторе 3 будущих дерева элементов интерфейсов
        self.initial_tree = None
        self.optimized_tree = None
        self.best_tree = None

        # Создаём 2 графических сцены - для эталонного вида интерфейса и для модифицированного алгоритмами
        self.initial_scene = QtWidgets.QGraphicsScene()
        self.optimized_scene = QtWidgets.QGraphicsScene()

        # Создаём графическме группы для раздельного отображения схемы расположения элементов и тепловой карты
        self.initial_tree_group = QtWidgets.QGraphicsItemGroup()
        self.initial_heatmap_group = QtWidgets.QGraphicsItemGroup()
        self.optimized_tree_group = QtWidgets.QGraphicsItemGroup()
        self.optimized_heatmap_group = QtWidgets.QGraphicsItemGroup()

        # Инициализируем коэффициенты пропорциональности реальных размеров и размеров на graphicsView
        self.initial_scale_x = 1
        self.initial_scale_y = 1
        self.optimized_scale_x = 1
        self.optimized_scale_y = 1

        # Идентификатор узлов дерева
        self.identifier = 1

        # Инициализируем списки точек для тепловых карт
        self.initial_points = []
        self.optimized_points = []

        # Контроль доступности кнопок управления
        self.loaded_interfaces = [False, False]

        # Параметры оптимизации
        self.count_iterations = 0
        self.count_useless_iterations = 0
        self.best_ff_value = 0
        self.current_ff_value = 0

        # PIL изображения тепловых карт
        self.destination_heatmap = None
        self.current_heatmap = None

        # Энергия системы зарядов эталонного интерфейса и коэффициент пропорциональности ФФ алгоритма системы зарядов
        self.initial_energy = 0

        # Создаём экземпляр класса событий
        self.events = Events()
        self.events.generation_completed[str].connect(self.update_generation)

        # Поток для выполнения процесса эволюции по выбранному алгоритму
        self.evolution = None

        # Инициализируем обработчики нажатия кнопок
        self.ui.loadButton.clicked.connect(self.load_destination)
        self.ui.loadButton2.clicked.connect(self.load_test)
        self.ui.elementsCheckBox.stateChanged.connect(self.show_elements)
        self.ui.heatmapCheckBox.stateChanged.connect(self.show_heatmaps)
        self.ui.gaRadioButton.clicked.connect(self.update_ff_statistics)
        self.ui.beesRadioButton.clicked.connect(self.update_ff_statistics)
        self.ui.chargesRadioButton.clicked.connect(self.update_ff_statistics)
        self.ui.startButton.clicked.connect(self.start_evolution)

        # Запускаем бесконечный цикл обработки событий в PyQt
        sys.exit(app.exec_())

    def update_generation(self, algorithm):
        """
        Обработчик события получения нового поколения интерфейсов одним из алгоритмов
        :param algorithm: название алгоритма - "ga" | "bees" | "charges"
        """
        # Перерисовываем элементы дерева на QGraphicsView
        self.update_interface()

        # Пересчитываем статистику и выводим её
        self.count_iterations += 1
        if algorithm == "ga" or algorithm == "bees":
            self.current_ff_value = FitnessFunctions.get_ff_value(self.destination_heatmap, self.current_heatmap)
        else:
            self.current_ff_value = \
                FitnessFunctions.get_ff_value_charges(self.optimized_tree, self.ui.optimizedView.width(),
                                                      self.ui.optimizedView.height(), self.initial_energy)

        if self.current_ff_value < self.best_ff_value:
            self.best_ff_value = self.current_ff_value
            self.count_useless_iterations = 0
            self.best_tree = copy.deepcopy(self.optimized_tree)
        else:
            self.count_useless_iterations += 1
        self.show_statistics()

    def load_destination(self):
        """ Обработчик нажатия на верхнюю кнопку load, загружает эталонный интерфейс """
        self.load_json(self.ui.initialView, self.initial_scene, self.initial_points)

    def load_test(self):
        """ Обработчик нажатия на верхнюю кнопку load, загружает тестируемый интерфейс """
        self.load_json(self.ui.optimizedView, self.optimized_scene, self.optimized_points)

    def load_json(self, view, scene, points):
        """
        Фунция, выводящая openFileDialog и выполняющая загрузку указанного JSON файла с интерфейсом
        :param view: левый или правый graphicsView
        :param scene: одна из сцен, присвоенных graphicsView
        :param points: точки, описывающие положения тепловых зон на тепловой карте
        """
        file_name = QtWidgets.QFileDialog.getOpenFileName(self.main_window, 'Load file', './', "*.json")

        if file_name[0]:
            # Открываем json файл и считываем данные
            with open(file_name[0]) as data_file:
                data = json.load(data_file)

            # Создаём корень дерева элементов
            root = Node(data["tagName"], data["id"], data["className"], data["clientWidth"],
                        data["clientHeight"], data["clientTop"], data["clientLeft"])
            children = data["children"]
            tree = Tree(root)

            if view == self.ui.initialView:
                self.initial_tree = tree
                self.loaded_interfaces[0] = True
                if PRINT_INFO:
                    print("====================== INITIAL TREE ======================")
            else:
                self.optimized_tree = tree
                self.best_tree = copy.deepcopy(tree)
                self.loaded_interfaces[1] = True
                if PRINT_INFO:
                    print("====================== OPTIMIZED TREE ======================")

            # Вызываем функцию заполнения дерева и выводим структуру дерева
            self.identifier = 1
            self.fill_tree(root, children)
            if PRINT_INFO:
                tree.draw_tree()
                print()

            # Рисуем элементы дерева на QGraphicsView
            self.draw_interface(view, scene, tree, points)

            # Обнуляем статистику
            self.count_iterations = 0
            self.count_useless_iterations = 0

            # Делаем доступными кнопки управления отображением
            self.enable_check_buttons()

            # Если оба интерфейса загружены - делаем доступными кнопки управления алгоритмами оттимизации
            if self.loaded_interfaces[0] and self.loaded_interfaces[1]:
                self.enable_algorithm_buttons()
                self.initial_energy = FitnessFunctions.get_energy(self.initial_tree, self.ui.optimizedView.width(),
                                                                  self.ui.optimizedView.height())

    def fill_tree(self, root, children):
        """
        Функция, добавляющая узлу дерева (root) дочерние узлы, содержащиеся в children, типа Node (файл node.py)
        :param root: узел, к которому добавляются дочерние
        :param children: список дочерних узлов
        """
        for child in children:
            child_node = Node(child["tagName"], child["id"], child["className"], child["clientWidth"],
                              child["clientHeight"],
                              child["clientTop"], child["clientLeft"], self.identifier)
            root.add_child(child_node)
            self.identifier += 1

            new_root = child_node
            new_children = child["children"]
            self.fill_tree(new_root, new_children)

    def draw_interface(self, view, scene, tree, points):
        """ Функция, отрисовывающая начальный вид интерфейса с помощью PyQt """
        # Очищаем сцену для рисования новых элементов
        scene.clear()

        view.setScene(scene)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Добавление границ каждой сцене, чтобы GraphicsView не пытался размещать по центру элементы
        scene.addLine(0, 0, view.width(), 0, QPen(QColor(255, 255, 255)))
        scene.addLine(view.width(), 0, view.width(), view.height(), QPen(QColor(255, 255, 255)))
        scene.addLine(view.width(), view.height(), 0, view.height(), QPen(QColor(255, 255, 255)))
        scene.addLine(0, view.height(), 0, 0, QPen(QColor(255, 255, 255)))

        # Создаём графическме группы для раздельного отображения схемы расположения элементов и тепловой карты
        if view == self.ui.initialView:
            self.initial_tree_group = QtWidgets.QGraphicsItemGroup()
            self.initial_heatmap_group = QtWidgets.QGraphicsItemGroup()
            tree_group = self.initial_tree_group
            heatmap_group = self.initial_heatmap_group
        else:
            self.optimized_tree_group = QtWidgets.QGraphicsItemGroup()
            self.optimized_heatmap_group = QtWidgets.QGraphicsItemGroup()
            tree_group = self.optimized_tree_group
            heatmap_group = self.optimized_heatmap_group

        # Определяем коэффициенты пропорциональности размеров элементов дерева и размеров на форме (2px = границы)
        if scene == self.initial_scene:
            self.initial_scale_x = tree.root.width / (view.width() - 2)
            self.initial_scale_y = tree.root.height / (view.height() - 2)
            scale_x = self.initial_scale_x
            scale_y = self.initial_scale_y
        else:
            self.optimized_scale_x = tree.root.width / (view.width() - 2)
            self.optimized_scale_y = tree.root.height / (view.height() - 2)
            scale_x = self.optimized_scale_x
            scale_y = self.optimized_scale_y

        # Заполняем созданные графические группы элементами и тепловыми картами соответственно
        points.clear()
        self.fill_tree_group(tree, tree.root, tree_group, points, scale_x, scale_y)
        self.fill_heatmap_group(view, points, heatmap_group)

        # Добавляем на сцены соответственные группы элементов и теповых карт
        scene.addItem(tree_group)
        scene.addItem(heatmap_group)

    def update_interface(self):
        """ Функция, выполняющая перерисовку сцены после изменения дерева """
        # Очищаем сцену  группы для рисования новых элементов
        self.optimized_scene.clear()
        self.optimized_tree_group = QtWidgets.QGraphicsItemGroup()
        self.optimized_heatmap_group = QtWidgets.QGraphicsItemGroup()

        # Заполняем созданные графические группы элементами и тепловыми картами соответственно
        points = []
        self.fill_tree_group(self.optimized_tree, self.optimized_tree.root, self.optimized_tree_group, points,
                             self.optimized_scale_x, self.optimized_scale_y)
        self.fill_heatmap_group(self.ui.optimizedView, points, self.optimized_heatmap_group)

        # Добавляем на сцены соответственные группы элементов и теповых карт
        if self.ui.elementsCheckBox.isChecked():
            self.optimized_scene.addItem(self.optimized_tree_group)
        if self.ui.heatmapCheckBox.isChecked():
            self.optimized_scene.addItem(self.optimized_heatmap_group)

    # Функция для заполнения графической группы элементами веб-странице в виде прямоугольников и получения списка
    # кортежей, представляющих точки вида (x, y, width, height, intensity)
    def fill_tree_group(self, tree, tree_root, group, points, scale_x, scale_y, depth=0):
        """
        Функция для заполнения графической группы элементами веб-странице в виде прямоугольников и получения списка
        кортежей, представляющих точки вида (x, y, width, height, intensity)
        """
        element = QtWidgets.QGraphicsRectItem(int(tree_root.left / scale_x), int(tree_root.top / scale_y),
                                              int(tree_root.width / scale_x), int(tree_root.height / scale_y))
        element.setPen(QPen(QColor(0, 0, 0)))
        element.setBrush(QBrush(QColor(125, 125, 125, 50)))
        group.addToGroup(element)

        if len(tree_root.children) == 0:
            text_label = tree_root.tag_name
            if tree_root.id_name:
                text_label += "#{0}".format(tree_root.id_name)
            if tree_root.class_name:
                text_label += "#{0}".format(tree_root.class_name)
            text = QtWidgets.QGraphicsSimpleTextItem(text_label, element)
            text.setPos(tree_root.left / scale_x + 2, tree_root.top / scale_y + 2)

        max_depth = tree.get_max_depth()
        actual_depth = depth + (6 - max_depth)  # 6 - максимальное значение глубины для карты с 7 цветами

        # Добавляем точку в список вершин для построения тепловой карты
        if len(tree_root.children) == 0 and actual_depth >= 0:
            points.append((int(tree_root.left / scale_x), int(tree_root.top / scale_y),
                           int(tree_root.width / scale_x), int(tree_root.height / scale_y), actual_depth/6))

        for child in tree_root.children:
            self.fill_tree_group(tree, child, group, points, scale_x, scale_y, depth+1)

    def fill_heatmap_group(self, view, points, group):
        """
        Функция для заполнения графической группы элементами тепловой карты, т.е. точками, описывающими интенсивность
        расположения элементов на данном конкретном месте интерфейса
        """
        _asset_file = partial(os.path.join, os.path.dirname(__file__), 'assets')

        image = Image.open(_asset_file('base.png'))
        image = image.resize((view.width(), view.height()))

        heatmap = Heatmapper(colours='default')
        heatmap = heatmap.heatmap_on_img(points, image)

        # Сохраняем в переменную класса PIL изображение тепловой карты
        if view == self.ui.initialView:
            self.destination_heatmap = heatmap
        else:
            self.current_heatmap = heatmap

        qt_image = ImageQt.ImageQt(heatmap)
        pixmap = QPixmap().fromImage(qt_image)
        qpixmap = QtWidgets.QGraphicsPixmapItem(pixmap)
        group.addToGroup(qpixmap)

    def enable_check_buttons(self):
        """ Функция, делающая доступными кнопки отображения """
        self.ui.elementsCheckBox.setEnabled(True)
        self.ui.heatmapCheckBox.setEnabled(True)

    def enable_algorithm_buttons(self):
        """ Функция, делающая доступными кнопки управления популяционными алгоритмами """
        self.ui.gaRadioButton.setEnabled(True)
        self.ui.beesRadioButton.setEnabled(True)
        self.ui.chargesRadioButton.setEnabled(True)
        self.ui.startButton.setEnabled(True)

        if self.ui.gaRadioButton.isChecked() or self.ui.beesRadioButton.isChecked():
            self.best_ff_value = self.current_ff_value = \
                FitnessFunctions.get_ff_value(self.destination_heatmap, self.current_heatmap)
        if self.ui.chargesRadioButton.isChecked():
            self.best_ff_value = self.current_ff_value = \
                FitnessFunctions.get_ff_value_charges(self.optimized_tree, self.ui.optimizedView.width(),
                                                      self.ui.optimizedView.height(), self.initial_energy)

        self.show_statistics()

    def show_elements(self):
        """ Функция, показывающая/скрывающая скилетоны веб-интерфейса """
        if self.ui.elementsCheckBox.isChecked():
            self.initial_scene.addItem(self.initial_tree_group)
            self.optimized_scene.addItem(self.optimized_tree_group)
        else:
            self.initial_scene.removeItem(self.initial_tree_group)
            self.optimized_scene.removeItem(self.optimized_tree_group)

    def show_heatmaps(self):
        """ Функция, показывающая/скрывающая тепловые карты веб-интерфейса """
        if self.ui.heatmapCheckBox.isChecked():
            self.initial_scene.addItem(self.initial_heatmap_group)
            self.optimized_scene.addItem(self.optimized_heatmap_group)
        else:
            self.initial_scene.removeItem(self.initial_heatmap_group)
            self.optimized_scene.removeItem(self.optimized_heatmap_group)

    def start_evolution(self):
        """ Функция, проверяющая, какой алгоритм эволюции выбран, и запускающая его на выполнение """
        self.evolution = EvolutionThread(self)
        self.evolution.start()

    def save_heatmap(self, tree, save_name):
        """ Функция, возвращаящая значение фитнесс-функции по различиям тепловых карт двух интерфейсов """
        # Внутренняя функция для получения точек интенсивности тепла не тепловой карте
        def get_points(tree, tree_root, points, depth=0):
            max_depth = tree.get_max_depth()
            actual_depth = depth + (6 - max_depth)  # 6 - максимальное значение глубины для карты с 7 цветами
            # Добавляем точку в список вершин для построения тепловой карты
            if len(tree_root.children) == 0 and actual_depth >= 0:
                points.append((int(tree_root.left / self.optimized_scale_x),
                               int(tree_root.top / self.optimized_scale_y),
                               int(tree_root.width / self.optimized_scale_x),
                               int(tree_root.height / self.optimized_scale_y), actual_depth/6))
            for child in tree_root.children:
                get_points(tree, child, points, depth+1)
            pass

        # Вызываем внутреннюю функция и получаем точки
        points = []
        get_points(tree, tree.root, points)

        # Формируем тепловую карту для дерева элементов
        _asset_file = partial(os.path.join, os.path.dirname(__file__), 'assets')
        image = Image.open(_asset_file('base.png'))
        image = image.resize((self.ui.optimizedView.width(), self.ui.optimizedView.height()))
        heatmap = Heatmapper(colours='default')
        heatmap = heatmap.heatmap_on_img(points, image)
        heatmap.save('.\heatmaps\{}.png'.format(save_name))

    def show_statistics(self):
        """ Функция, выводящая текущую статистику работы выбранного алгоритма """
        self.ui.iterationsLabel.setText("{}".format(self.count_iterations))
        self.ui.uselessIterationsLabel.setText("{}".format(self.count_useless_iterations))

        if self.ui.gaRadioButton.isChecked() or self.ui.beesRadioButton.isChecked():
            self.ui.bestFFLabel.setText("{:.0f}".format(self.best_ff_value))
            self.ui.currentFFLabel.setText("{:.0f}".format(self.current_ff_value))
        else:
            self.ui.bestFFLabel.setText("{:.0f}".format(self.best_ff_value))
            self.ui.currentFFLabel.setText("{:.0f}".format(self.current_ff_value))

    def update_ff_statistics(self):
        """ Обработчик изменения алгоритма эволюции """
        self.count_iterations = 0
        self.count_useless_iterations = 0

        if self.ui.gaRadioButton.isChecked() or self.ui.beesRadioButton.isChecked():
            self.current_ff_value = FitnessFunctions.get_ff_value(self.destination_heatmap, self.current_heatmap)
        if self.ui.chargesRadioButton.isChecked():
            self.current_ff_value = \
                FitnessFunctions.get_ff_value_charges(self.optimized_tree, self.ui.optimizedView.width(),
                                                      self.ui.optimizedView.height(), self.initial_energy)

        self.best_ff_value = self.current_ff_value
        self.show_statistics()


class Events(QObject):
    """
    Класс, содержащий сигналы, срабатывающие в процессе работы популяционных алгоритмов
    """
    generation_completed = pyqtSignal(str)


if __name__ == "__main__":
    # Создаём графический пользовательский интерфейс программы при помощи PyQt
    garnetBlocks = InterfaceOptimization()














