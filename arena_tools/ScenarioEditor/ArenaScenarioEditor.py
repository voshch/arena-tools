import pathlib
from PyQt5 import QtGui, QtCore, QtWidgets
import os
import time
import copy
from typing import Tuple, List
from .Pedestrian.Pedestrian import Pedestrian
from .Pedestrian.PedestrianEditor import PedestrianAgentEditor, PedestrianAgentEditorGlobalConfig
from .ArenaScenario import *
from arena_tools.utils.QtExtensions import *
from arena_tools.utils.HelperFunctions import *
import arena_simulation_setup.world
import arena_simulation_setup.entities.obstacles.static


class RosMapData():
    def __init__(self, path: str = ""):
        self.image_path = ""
        self.resolution = 1.0
        self.origin = [0.0, 0.0, 0.0]
        self.path = path
        if path != "":
            self.load(path)

    def load(self, path: str):
        if os.path.exists(path):
            self.path = path
            with open(path, "r") as file:
                data = yaml.safe_load(file)
                folder_path = os.path.dirname(path)
                self.image_path = os.path.join(folder_path, data["image"])
                self.resolution = float(data["resolution"])
                self.origin = [float(value) for value in data["origin"]]


class WaypointWidget(QtWidgets.QWidget):
    def __init__(self, pedestrianAgentWidget, graphicsScene: QtWidgets.QGraphicsScene, posIn: QtCore.QPointF = None, **kwargs):
        super().__init__(**kwargs)
        self.id = 0
        self.pedestrianAgentWidget = pedestrianAgentWidget  # needed so the ellipse item can trigger a waypoint path redraw
        # create circle and add to scene
        self.ellipseItem = WaypointGraphicsEllipseItem(self, None, None, -0.25, -0.25, 0.5, 0.5)
        self.graphicsScene = graphicsScene
        graphicsScene.addItem(self.ellipseItem)
        # setup widgets
        self.setupUI()
        self.setId(self.id)
        # set initial position
        if posIn is not None:
            self.setPos(posIn)

    def setupUI(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)

        # x value
        # label
        label = QtWidgets.QLabel("x")
        self.layout().addWidget(label)
        # spinbox
        self.posXSpinBox = ArenaQDoubleSpinBox()
        self.posXSpinBox.valueChanged.connect(self.updateEllipseItemFromSpinBoxes)
        self.layout().addWidget(self.posXSpinBox)

        # y value
        # label
        label = QtWidgets.QLabel("y")
        self.layout().addWidget(label)
        # spinbox
        self.posYSpinBox = ArenaQDoubleSpinBox()
        self.posYSpinBox.valueChanged.connect(self.updateEllipseItemFromSpinBoxes)
        self.layout().addWidget(self.posYSpinBox)

        # delete button
        delete_button = QtWidgets.QPushButton("X")
        delete_button.setFixedWidth(30)
        delete_button.setStyleSheet("background-color: red")
        delete_button.clicked.connect(self.remove)
        self.layout().addWidget(delete_button)

    def setId(self, id: int):
        self.id = id

    def setPos(self, posIn: QtCore.QPointF):
        # set values of spin boxes (and ellipse item)
        # since spin boxes are connected to the ellipse item, the change will be propagated
        self.posXSpinBox.setValue(posIn.x())
        self.posYSpinBox.setValue(posIn.y())

    def getPos(self) -> Tuple[float, float]:
        return self.posXSpinBox.value(), self.posYSpinBox.value()

    def updateEllipseItemFromSpinBoxes(self):
        if not self.ellipseItem.isDragged:  # do this to prevent recursion between spin boxes and graphics item
            x = self.posXSpinBox.value()
            y = self.posYSpinBox.value()
            self.ellipseItem.setPosNoEvent(x, y)  # set without event to prevent recursion between spin boxes and graphics item

    def updateSpinBoxesFromGraphicsItem(self):
        new_pos = self.ellipseItem.mapToScene(self.ellipseItem.transformOriginPoint())
        self.posXSpinBox.setValue(new_pos.x())
        self.posYSpinBox.setValue(new_pos.y())

    def remove(self):
        self.ellipseItem.scene().removeItem(self.ellipseItem)
        del self.ellipseItem.keyPressEater  # delete to remove event filter

        self.parent().layout().removeWidget(self)
        self.pedestrianAgentWidget.updateWaypointIdLabels()
        self.pedestrianAgentWidget.drawWaypointPath()
        self.deleteLater()


class PedestrianAgentWidget(QtWidgets.QFrame):
    '''
    This is a row in the obstacles frame.
    '''

    def __init__(self, id: int, pedestrianAgentIn: Pedestrian, graphicsScene: QtWidgets.QGraphicsScene, graphicsView: ArenaQGraphicsView, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.graphicsScene = graphicsScene
        self.graphicsView = graphicsView
        self.pedestrianAgent = pedestrianAgentIn

        # create path item
        self.graphicsPathItem = ArenaGraphicsPathItem(self)
        # add to scene
        self.graphicsScene.addItem(self.graphicsPathItem)
        # setup widgets
        self.setup_ui()
        # setup pedestrian agent editor
        self.pedestrian_editor = PedestrianAgentEditor(self, parent=self.parent(), flags=QtCore.Qt.WindowType.Window)
        self.pedestrian_editor.editorSaved.connect(self.handleEditorSaved)

        # setup waypoints
        self.addWaypointModeActive = False
        self.activeModeWindow = ActiveModeWindow(self)
        graphicsView.clickedPos.connect(self.handleGraphicsViewClick)
        # GraphicsItem for drawing a path connecting the waypoints
        self.waypointPathItem = QtWidgets.QGraphicsPathItem()
        # create brush
        brush = QtGui.QBrush(QtGui.QColor(), QtCore.Qt.BrushStyle.NoBrush)
        self.waypointPathItem.setBrush(brush)
        # create pen
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor("lightseagreen"))
        pen.setWidthF(0.1)
        pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        self.waypointPathItem.setPen(pen)
        # add to scene
        graphicsScene.addItem(self.waypointPathItem)

        self.updateEverythingFromPedestrianAgent()

    def setup_ui(self):
        self.setLayout(QtWidgets.QGridLayout())
        self.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)

        # name label
        self.name_label = QtWidgets.QLabel(self.pedestrianAgent.name)
        self.layout().addWidget(self.name_label, 0, 0)

        # edit button
        self.edit_button = QtWidgets.QPushButton("Edit")
        self.edit_button.clicked.connect(self.onEditClicked)
        self.layout().addWidget(self.edit_button, 0, 1)

        # delete button
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.clicked.connect(self.onDeleteClicked)
        self.layout().addWidget(self.delete_button, 0, 2)

        # position
        label = QtWidgets.QLabel("Position:")
        self.layout().addWidget(label, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.posXSpinBox = ArenaQDoubleSpinBox()
        self.posXSpinBox.valueChanged.connect(self.updateGraphicsPathItemFromSpinBoxes)
        self.layout().addWidget(self.posXSpinBox, 1, 1)
        self.posYSpinBox = ArenaQDoubleSpinBox()
        self.posYSpinBox.valueChanged.connect(self.updateGraphicsPathItemFromSpinBoxes)
        self.layout().addWidget(self.posYSpinBox, 1, 2)

        # waypoints
        label = QtWidgets.QLabel("Waypoints:")
        self.layout().addWidget(label, 2, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        button = QtWidgets.QPushButton("Add Waypoints...")
        button.clicked.connect(self.onAddWaypointClicked)
        self.layout().addWidget(button, 2, 1, 1, -1)
        self.waypointListWidget = QtWidgets.QWidget()
        self.waypointListWidget.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.waypointListWidget, 3, 0, 1, -1)

    def handleMouseDoubleClick(self):
        # function will be called by the graphics item
        self.onEditClicked()

    def handleItemChange(self):
        # function will be called by the graphics item
        self.updateSpinBoxesFromGraphicsItem()
        self.drawWaypointPath()

    def drawWaypointPath(self):
        path = QtGui.QPainterPath()
        path.moveTo(self.getCurrentAgentPosition())
        for w in self.getWaypointWidgets():
            w_pos = w.ellipseItem.mapToScene(w.ellipseItem.transformOriginPoint())
            path.lineTo(w_pos)

        self.waypointPathItem.setPath(path)

    def getCurrentAgentPosition(self):
        x = self.posXSpinBox.value()
        y = self.posYSpinBox.value()
        return QtCore.QPointF(x, y)

    def getWaypointWidgets(self):
        widgets = []
        for i in range(self.waypointListWidget.layout().count()):
            w = self.waypointListWidget.layout().itemAt(i).widget()
            if w is not None:
                widgets.append(w)
        return widgets

    def updateSpinBoxesFromGraphicsItem(self):
        new_pos = self.graphicsPathItem.mapToScene(self.graphicsPathItem.transformOriginPoint())
        self.posXSpinBox.setValue(new_pos.x())
        self.posYSpinBox.setValue(new_pos.y())

    def updateGraphicsPathItemFromSpinBoxes(self):
        if not self.graphicsPathItem.isDragged:  # prevents recursive loop (spin box <-> moving item)
            x = self.posXSpinBox.value()
            y = self.posYSpinBox.value()
            self.graphicsPathItem.setPosNoEvent(x, y)
            self.drawWaypointPath()
            self.graphicsPathItem.updateTextItemPos()

    def updateGraphicsPathItemFromPedestrianAgent(self):
        # update path
        painter_path = QtGui.QPainterPath()
        painter_path.setFillRule(QtCore.Qt.WindingFill)
        # visualize
        brush = QtGui.QBrush(QtGui.QColor('#ffff90'), QtCore.Qt.BrushStyle.SolidPattern)
        self.graphicsPathItem.setBrush(brush)
        center = QtCore.QPointF(0, 0)
        radius = 1
        painter_path.addEllipse(center, radius, radius)
        self.graphicsPathItem.setPath(painter_path)
        # update text
        self.graphicsPathItem.textItem.setPlainText(self.name_label.text())
        self.graphicsPathItem.updateTextItemPos()

    def setPedestrianAgent(self, agent: Pedestrian):
        self.pedestrianAgent = agent
        self.updateEverythingFromPedestrianAgent()

    def updateEverythingFromPedestrianAgent(self):
        # position
        self.posXSpinBox.setValue(self.pedestrianAgent.pos[0])
        self.posYSpinBox.setValue(self.pedestrianAgent.pos[1])
        # waypoints
        # remove all waypoint widgets
        for w in self.getWaypointWidgets():
            w.remove()
        # add new waypoints
        for wp in self.pedestrianAgent.waypoints:
            pos = QtCore.QPointF(wp[0], wp[1])
            self.addWaypoint(pos)
        # update name label
        self.updateNameLabelFromPedestrianAgent()
        # update item scene
        self.updateGraphicsPathItemFromPedestrianAgent()

    def updateNameLabelFromPedestrianAgent(self):
        self.name_label.setText(self.pedestrianAgent.name)

    def handleEditorSaved(self):
        # editor was saved, update possibly changed values
        self.updateNameLabelFromPedestrianAgent()
        self.updateGraphicsPathItemFromPedestrianAgent()

    def updateWaypointIdLabels(self):
        widgets = self.getWaypointWidgets()
        for i, w in enumerate(widgets):
            w.setId(i)

    # @pyqtSlot(QtCore.QPointF)
    def handleGraphicsViewClick(self, pos: QtCore.QPointF):
        if self.addWaypointModeActive:
            self.addWaypoint(pos)

    def addWaypoint(self, pos: QtCore.QPointF = None):
        w = WaypointWidget(self, self.graphicsScene, pos, parent=self)
        self.waypointListWidget.layout().addWidget(w)
        self.updateWaypointIdLabels()
        self.drawWaypointPath()

    def removeWaypoint(self, waypointWidget: WaypointWidget):
        self.waypointListWidget.layout().removeWidget(waypointWidget)
        self.updateWaypointIdLabels()
        self.drawWaypointPath()

    def setAddWaypointMode(self, enable: bool):
        self.addWaypointModeActive = enable
        if enable:
            self.activeModeWindow.show()
        else:
            self.activeModeWindow.hide()

    def save(self):
        # saves position and waypoints to the pedestrian agent
        # all other attributes should have already been saved by the PedestrianAgentEditor
        # position
        pos_x = self.posXSpinBox.value()
        pos_y = self.posYSpinBox.value()
        self.pedestrianAgent.pos = np.array([pos_x, pos_y])
        # waypoints
        self.pedestrianAgent.waypoints = []
        for w in self.getWaypointWidgets():
            x, y = w.getPos()
            self.pedestrianAgent.waypoints.append(np.array([x, y]))

    def remove(self):
        # remove waypoints
        for w in self.getWaypointWidgets():
            w.remove()
        # remove items from scene
        self.graphicsScene.removeItem(self.graphicsPathItem)
        self.graphicsScene.removeItem(self.graphicsPathItem.textItem)
        self.graphicsScene.removeItem(self.waypointPathItem)
        del self.graphicsPathItem.keyPressEater  # delete to remove event filter
        # remove widget
        self.parent().layout().removeWidget(self)
        self.deleteLater()

    def onAddWaypointClicked(self):
        if self.addWaypointModeActive:
            self.setAddWaypointMode(False)
        else:
            self.setAddWaypointMode(True)

    def onEditClicked(self):
        self.pedestrian_editor.show()

    def onDeleteClicked(self):
        self.remove()


class RobotAgentWidget(QtWidgets.QFrame):
    '''
    This is a row in the obstacles frame.
    '''

    def __init__(self, graphicsScene: QtWidgets.QGraphicsScene, graphicsView: ArenaQGraphicsView, **kwargs):
        super().__init__(**kwargs)
        self.graphicsScene = graphicsScene
        self.graphicsView = graphicsView

        self.setup_ui()

        # create graphics items displayed in the scene
        # start pos
        self.startGraphicsEllipseItem = ArenaGraphicsEllipseItem(self.startXSpinBox, self.startYSpinBox, -0.25, -0.25, 0.5, 0.5)
        # set color
        brush = QtGui.QBrush(QtGui.QColor("green"), QtCore.Qt.BrushStyle.SolidPattern)
        self.startGraphicsEllipseItem.setBrush(brush)
        # enable text next to item in scene
        self.startGraphicsEllipseItem.enableTextItem(self.graphicsScene, "Robot")
        # add to scene
        self.graphicsScene.addItem(self.startGraphicsEllipseItem)

        # goal pos
        self.goalGraphicsEllipseItem = ArenaGraphicsEllipseItem(self.goalXSpinBox, self.goalYSpinBox, -0.25, -0.25, 0.5, 0.5)
        # set color
        brush = QtGui.QBrush(QtGui.QColor("red"), QtCore.Qt.BrushStyle.SolidPattern)
        self.goalGraphicsEllipseItem.setBrush(brush)
        # enable text next to item in scene
        self.goalGraphicsEllipseItem.enableTextItem(self.graphicsScene, "Goal")
        # add to scene
        self.graphicsScene.addItem(self.goalGraphicsEllipseItem)

        # move start and goal positions a bit to make them not overlap
        self.startXSpinBox.setValue(-3)
        self.startYSpinBox.setValue(3)
        self.goalXSpinBox.setValue(3)
        self.goalYSpinBox.setValue(-3)

    def setup_ui(self):
        self.setLayout(QtWidgets.QGridLayout())
        self.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)
        self.setStyleSheet("background-color: rgb(255, 255, 255);")

        # name label
        self.name_label = QtWidgets.QLabel("Robot")
        self.layout().addWidget(self.name_label, 0, 0)

        # start position
        label = QtWidgets.QLabel("Start:")
        self.layout().addWidget(label, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.startXSpinBox = ArenaQDoubleSpinBox()
        self.startXSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.startXSpinBox, 1, 1)
        self.startYSpinBox = ArenaQDoubleSpinBox()
        self.startYSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.startYSpinBox, 1, 2)

        # goal position
        label = QtWidgets.QLabel("Goal")
        self.layout().addWidget(label, 2, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.goalXSpinBox = ArenaQDoubleSpinBox()
        self.goalXSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.goalXSpinBox, 2, 1)
        self.goalYSpinBox = ArenaQDoubleSpinBox()
        self.goalYSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.goalYSpinBox, 2, 2)

        self.resetsSpinBox = QtWidgets.QSpinBox()
        self.resetsSpinBox.setMinimum(0)
        rst_label = QtWidgets.QLabel("Episode resets:")
        self.layout().addWidget(rst_label, 3, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.resetsSpinBox, 3, 1)

    def updateSpinBoxesFromGraphicsItems(self):
        # start
        new_pos = self.startGraphicsEllipseItem.mapToScene(self.startGraphicsEllipseItem.transformOriginPoint())
        self.startXSpinBox.setValue(new_pos.x())
        self.startYSpinBox.setValue(new_pos.y())
        # goal
        new_pos = self.goalGraphicsEllipseItem.mapToScene(self.goalGraphicsEllipseItem.transformOriginPoint())
        self.goalXSpinBox.setValue(new_pos.x())
        self.goalYSpinBox.setValue(new_pos.y())

    def updateGraphicsItemsFromSpinBoxes(self):
        # start
        if not self.startGraphicsEllipseItem.isDragged:  # prevents recursive loop (spin box <-> moving item)
            x = self.startXSpinBox.value()
            y = self.startYSpinBox.value()
            self.startGraphicsEllipseItem.setPosNoEvent(x, y)
        # goal
        if not self.goalGraphicsEllipseItem.isDragged:
            x = self.goalXSpinBox.value()
            y = self.goalYSpinBox.value()
            self.goalGraphicsEllipseItem.setPosNoEvent(x, y)


class ArenaScenarioEditor(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_ui()
        self.arenaScenario = ArenaScenario()
        self.numObstacles = 0
        self.pixmap_item = None
        self.mapData = None
        self.currentSavePath = ""
        self.copied = []
        self.lastNameId = 0

        self.selected_world = "map_empty"
        path = pathlib.Path(arena_simulation_setup.world.World(self.selected_world).map.path) / "map.yaml"
        if path.is_file():
            self.setMap(str(path))
        self.selected_scenario = ""

        # create global pedestrian settings widget
        self.pedestrianAgentsGlobalConfigWidget = PedestrianAgentEditorGlobalConfig()
        self.pedestrianAgentsGlobalConfigWidget.editorSaved.connect(self.onPedestrianAgentsGlobalConfigChanged)

        QtCore.QTimer.singleShot(0, self.show_select_world_dialog)

    def show_select_world_dialog(self):
        dialog = ComboBoxDialog(
            self, 
            combo_box_items=arena_simulation_setup.world.World.list(),
            window_title="Choose world",
            label="Please select a world:"
        )
        result = dialog.exec_()  # Modal dialog, execution pauses here

        if result == QtWidgets.QDialog.Accepted:
            selected_world = dialog.get_selected_option()
            print(f"User selected: {selected_world}")
            self.statusBar().showMessage(f"Selected: {selected_world}")

            self.selected_world = selected_world
            path = pathlib.Path(arena_simulation_setup.world.World(self.selected_world).map.path) / "map.yaml"
            if path.is_file():
                self.setMap(str(path))
            
            self.show_select_scenario_dialog()
        else:
            print("Dialog was rejected or closed unexpectedly.")

    def setup_ui(self):
        self.setWindowTitle("Scenario Editor")
        self.resize(1300, 700)
        self.move(100, 100)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap('icon.png'), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.setWindowIcon(icon)

        # set central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(QtWidgets.QGridLayout())
        self.setCentralWidget(central_widget)

        # menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open...", self.onOpenClicked, "Ctrl+O")
        file_menu.addAction("Save", self.onSaveClicked, "Ctrl+S")
        file_menu.addAction("Save As...", self.onSaveAsClicked, "Ctrl+Shift+S")
        add_menu = menubar.addMenu("Elements")
        add_menu.addAction("Set Map...", self.onSetMapClicked)
        add_menu.addAction("Add Pedestrian Agent", self.onAddPedestrianAgentClicked, "Ctrl+1")
        global_pedestrian_settings_menu = menubar.addMenu("Global Configs")
        global_pedestrian_settings_menu.addAction("Pedestrian Agents...", self.onPedestrianAgentsGlobalConfigClicked)

        # status bar
        self.statusBar()  # create status bar

        # drawing frame
        # frame
        drawing_frame = QtWidgets.QFrame()
        drawing_frame.setLayout(QtWidgets.QVBoxLayout())
        drawing_frame.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)
        self.centralWidget().layout().addWidget(drawing_frame, 0, 1, -1, -1)
        # graphicsscene
        self.gscene = ArenaQGraphicsScene()
        # graphicsview
        self.gview = ArenaQGraphicsView(self.gscene)
        self.gview.scale(0.25, 0.25)  # zoom out a bit
        drawing_frame.layout().addWidget(self.gview)

        # obstacles
        # scrollarea
        self.obstacles_scrollarea = QtWidgets.QScrollArea(self)
        self.obstacles_scrollarea.setWidgetResizable(True)
        self.obstacles_scrollarea.setMinimumWidth(300)
        self.centralWidget().layout().addWidget(self.obstacles_scrollarea, 0, 0, -1, 1)
        # frame
        self.obstacles_frame = QtWidgets.QFrame()
        self.obstacles_frame.setLayout(QtWidgets.QVBoxLayout())
        self.obstacles_frame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        self.obstacles_scrollarea.setWidget(self.obstacles_frame)

        # always add robot agent
        self.robotAgentWidget = RobotAgentWidget(self.gscene, self.gview)
        self.obstacles_frame.layout().addWidget(self.robotAgentWidget)

    def onPedestrianAgentsGlobalConfigClicked(self):
        self.pedestrianAgentsGlobalConfigWidget.show()

    def onPedestrianAgentsGlobalConfigChanged(self):
        for w in self.getPedestrianAgentWidgets():
            w.save()
            global_agent = copy.deepcopy(self.pedestrianAgentsGlobalConfigWidget.pedestrianAgent)
            # preserve individual values
            global_agent.name = w.pedestrianAgent.name
            global_agent.pos = w.pedestrianAgent.pos
            global_agent.waypoints = w.pedestrianAgent.waypoints
            # set new agent
            w.pedestrianAgent = global_agent
            w.pedestrianAgentEditor.pedestrianAgent = global_agent
            w.pedestrianAgentEditor.updateValuesFromPedestrianAgent()
            w.handleEditorSaved()

    def onSetMapClicked(self):
        self.show_select_world_dialog()

    def setMap(self, path: str):
        self.mapData = RosMapData(path)
        pixmap = QtGui.QPixmap(self.mapData.image_path)
        transform = QtGui.QTransform.fromScale(1.0, -1.0)  # flip y axis
        pixmap = pixmap.transformed(transform)
        if self.pixmap_item is not None:
            # remove old map
            self.gscene.removeItem(self.pixmap_item)
        self.pixmap_item = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_item.setZValue(-1.0)  # make sure map is always in the background
        self.pixmap_item.setScale(self.mapData.resolution)
        self.pixmap_item.setOffset(self.mapData.origin[0] / self.mapData.resolution, self.mapData.origin[1] / self.mapData.resolution)
        self.gscene.addItem(self.pixmap_item)

    def getMapData(self, path: str) -> dict:
        # read yaml file containing map meta data
        with open(path, "r") as file:
            data = yaml.safe_load(file)
            return data

    def disableAddWaypointMode(self):
        widgets = self.getPedestrianAgentWidgets()
        for w in widgets:
            w.setAddWaypointMode(False)

    def onAddPedestrianAgentClicked(self):
        new_agent = Pedestrian(self.generateName())
        self.arenaScenario.pedestrianAgents.append(new_agent)
        self.addPedestrianAgentWidget(new_agent)

    def addPedestrianAgentWidget(self, agent: Pedestrian) -> PedestrianAgentWidget:
        '''
        Adds a new pedestrian agent widget with the given agent.
        Warning: self.arenaScenario is not updated. Management of self.arenaScenario happens outside of this function.
        '''
        w = PedestrianAgentWidget(self.numObstacles, agent, self.gscene, self.gview, parent=self)
        self.obstacles_frame.layout().addWidget(w)
        self.numObstacles += 1
        return w

    def getPedestrianAgentWidgets(self):
        widgets = []
        for i in range(self.obstacles_frame.layout().count()):
            w = self.obstacles_frame.layout().itemAt(i).widget()
            if w is not None and isinstance(w, PedestrianAgentWidget):
                widgets.append(w)
        return widgets

    def getElementsCount(self):
        count = 0
        for i in range(self.obstacles_frame.layout().count()):
            w = self.obstacles_frame.layout().itemAt(i).widget()
            if w is not None and isinstance(w, PedestrianAgentWidget):
                count += 1
        return count

    def generateName(self):
        self.lastNameId += 1
        return "Pedestrian " + str(self.lastNameId)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Escape or event.key() == QtCore.Qt.Key.Key_Return:
            self.disableAddWaypointMode()

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_C:
            self.copied = self.gscene.selectedItems()

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_V:
            self.pasteElements()

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_D:
            self.toggleWaypointMode()

        return super().keyPressEvent(event)

    def toggleWaypointMode(self):
        # active waypoint mode for selected pedestrian agents
        for item in self.gscene.selectedItems():
            if hasattr(item, "parentWidget"):
                widget = item.parentWidget
                if isinstance(widget, PedestrianAgentWidget):
                    widget.onAddWaypointClicked()

    def pasteElements(self):
        # duplicate copied items
        for item in self.copied:
            widget = item.parentWidget
            if isinstance(widget, PedestrianAgentWidget):
                widget.save()
                agent = copy.deepcopy(widget.pedestrianAgent)
                agent.name = self.generateName()
                # move agent and waypoints a bit
                agent.pos[0] += 1.0
                agent.pos[1] += 1.0
                for wp in agent.waypoints:
                    wp[0] += 1.0
                    wp[1] += 1.0
                new_widget = self.addPedestrianAgentWidget(agent)
                # select new item and waypoints
                new_widget.graphicsPathItem.setSelected(True)
                for w in new_widget.getWaypointWidgets():
                    w.ellipseItem.setSelected(True)
                # unselect old item and waypoints
                widget.graphicsPathItem.setSelected(False)
                for w in widget.getWaypointWidgets():
                    w.ellipseItem.setSelected(False)

    def onNewScenarioClicked(self):
        pass

    def onOpenClicked(self):
        self.show_select_scenario_dialog()

    def show_select_scenario_dialog(self):
        dialog = ComboBoxDialog(
            self, 
            combo_box_items=arena_simulation_setup.world.World(self.selected_world).scenario.list(),
            window_title="Choose scenario",
            label="Please select a scenario:"
        )
        result = dialog.exec_()  # Modal dialog, execution pauses here

        if result == QtWidgets.QDialog.Accepted:
            selected_scenario = dialog.get_selected_option()
            print(f"User selected: {selected_scenario}")
            self.statusBar().showMessage(f"Selected: {selected_scenario}")

            self.selected_scenario = selected_scenario

            path = pathlib.Path(arena_simulation_setup.world.World(self.selected_world).base_dir()) / os.path.join("scenarios", self.selected_scenario)
            if path.is_file():
                self.loadArenaScenario(str(path))
        else:
            print("Dialog was rejected or closed unexpectedly.")

    def onSaveClicked(self):
        if not self.save():
            # no path has been set yet. fall back to "save as"
            self.onSaveAsClicked()

    def onSaveAsClicked(self) -> bool:
        # initial_folder = os.path.join(arena_simulation_setup.world.World(self.selected_world).base_dir(), "scenarios")

        # res = QtWidgets.QFileDialog.getSaveFileName(parent=self, directory=initial_folder)
        # path = res[0]
        dialog = LineEditDialog(
            self, 
            window_title="Save scenario",
            label="Please type a name for your new scenario:",
            placeholder_text="new_scenario.json"
        )
        result = dialog.exec_()  # Modal dialog, execution pauses here

        if result == QtWidgets.QDialog.Accepted:
            scenario_name = dialog.get_typed_text()

            if scenario_name != "":
                path = pathlib.Path(arena_simulation_setup.world.World(self.selected_world).scenario.base_dir()) / \
                        os.path.join(
                            scenario_name
                        )
                self.statusBar().showMessage(f"Saved at: {str(path)}")
                return self.save(str(path))
        else:
            print("Dialog was rejected or closed unexpectedly.")

        return False

    def loadArenaScenario(self, path: str):
        self.currentSavePath = path
        self.arenaScenario.loadFromFile(path)
        self.updateWidgetsFromArenaScenario()

    def save(self, path: str = "") -> bool:
        if path != "":
            self.currentSavePath = path

        self.updateArenaScenarioFromWidgets()
        if self.arenaScenario.saveToFile():
            msg = f"[{time.strftime('%H:%M:%S')}] Saved scenario to {self.arenaScenario.path}"
            self.statusBar().showMessage(msg, 10 * 1000)
            return True

        return False

    def updateWidgetsFromArenaScenario(self):
        # pedestrian agents
        # remove all pedestrian widgets
        for w in self.getPedestrianAgentWidgets():
            w.remove()
        # create new pedestrian widgets
        for agent in self.arenaScenario.pedestrianAgents:
            self.addPedestrianAgentWidget(agent)

        # static obstacles

        # interactive obstacles
        # TODO

        # robot position
        self.robotAgentWidget.startXSpinBox.setValue(self.arenaScenario.robotPosition[0])
        self.robotAgentWidget.startYSpinBox.setValue(self.arenaScenario.robotPosition[1])
        # robot goal
        self.robotAgentWidget.goalXSpinBox.setValue(self.arenaScenario.robotGoal[0])
        self.robotAgentWidget.goalYSpinBox.setValue(self.arenaScenario.robotGoal[1])

        # map
        self.setMap(self.arenaScenario.mapPath)

        # resets
        self.robotAgentWidget.resetsSpinBox.setValue(self.arenaScenario.resets)

    def updateArenaScenarioFromWidgets(self):
        '''
        Save data from widgets into self.arenaScenario.
        '''
        # reset scenario
        self.arenaScenario.__init__()

        # save path
        self.arenaScenario.path = self.currentSavePath

        # save pedestrian agents
        for w in self.getPedestrianAgentWidgets():
            w.save()  # save all data from widget(s) into pedestrian agent
            self.arenaScenario.pedestrianAgents.append(w.pedestrianAgent)  # add pedestrian agent

        # save static obstacles

        # save map path
        if self.mapData is not None:
            self.arenaScenario.mapPath = self.mapData.path

        # robot position
        self.arenaScenario.robotPosition[0] = self.robotAgentWidget.startXSpinBox.value()
        self.arenaScenario.robotPosition[1] = self.robotAgentWidget.startYSpinBox.value()
        # robot goal
        self.arenaScenario.robotGoal[0] = self.robotAgentWidget.goalXSpinBox.value()
        self.arenaScenario.robotGoal[1] = self.robotAgentWidget.goalYSpinBox.value()

        # interactive obstacles
        # TODO
        self.arenaScenario.resets = self.robotAgentWidget.resetsSpinBox.value()
