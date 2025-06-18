from PyQt5 import QtGui, QtCore, QtWidgets
import os
import copy
from arena_tools.ScenarioEditor.ArenaScenario import *
from arena_tools.utils.QtExtensions import *
from arena_tools.utils.HelperFunctions import *
from .Pedestrian import PedestrianAgentType, PedestrianWaypointMode, PedestrianStartupMode

import arena_simulation_setup.entities.obstacles.dynamic


class PedestrianAgentEditor(QtWidgets.QWidget):
    editorSaved = QtCore.pyqtSignal()

    def __init__(self, pedestrianAgentWidget=None, **kwargs):
        super().__init__(**kwargs)
        self.pedestrianAgentWidget = pedestrianAgentWidget
        if pedestrianAgentWidget is None:
            self.pedestrianAgent = Pedestrian('Pedestrian 1')
        else:
            self.pedestrianAgent = pedestrianAgentWidget.pedestrianAgent
        self.setup_ui()
        self.updateValuesFromPedestrianAgent()
        self.updateWidgetsFromSelectedType()
        self.updateWidgetsFromSelectedStartupMode()

    def setup_ui(self):
        self.setWindowTitle("Pedestrian Agent Editor")
        self.setLayout(QtWidgets.QGridLayout())
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.resize(600, 600)
        self.move(220, 150)

        # scrollarea
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumWidth(400)
        self.layout().addWidget(self.scrollArea, 0, 0, 1, -1)
        # frame
        self.scrollAreaFrame = QtWidgets.QFrame()
        self.scrollAreaFrame.setLayout(QtWidgets.QGridLayout())
        self.scrollAreaFrame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        self.scrollAreaFrame.setMinimumWidth(400)
        self.scrollArea.setWidget(self.scrollAreaFrame)

        vertical_idx = 0

        # heading "general"
        general_label = QtWidgets.QLabel("#### General")
        general_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(general_label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        line = Line()
        self.scrollAreaFrame.layout().addWidget(line, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # name
        # label
        self.nameLabel = QtWidgets.QLabel("Name")
        self.nameLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.nameLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # editbox
        name = self.pedestrianAgentWidget.name_label.text() if self.pedestrianAgentWidget is not None else "global agent"
        self.name_edit = QtWidgets.QLineEdit(name)
        self.name_edit.setFixedSize(200, 30)
        self.scrollAreaFrame.layout().addWidget(self.name_edit, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # type
        # label
        type_label = QtWidgets.QLabel("Type")
        type_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(type_label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # dropdown
        self.typeComboBox = QtWidgets.QComboBox()
        for agent_type in PedestrianAgentType:
            self.typeComboBox.insertItem(agent_type.value, agent_type.name.lower())
        self.typeComboBox.setFixedSize(200, 30)
        self.typeComboBox.currentIndexChanged.connect(self.updateWidgetsFromSelectedType)
        self.scrollAreaFrame.layout().addWidget(self.typeComboBox, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # model
        # label
        model_label = QtWidgets.QLabel("Model")
        model_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(model_label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # dropdown
        self.modelComboBox = QtWidgets.QComboBox()
        for index, agent_model in enumerate(arena_simulation_setup.entities.obstacles.dynamic.DynamicObstacle.list()):
            self.modelComboBox.insertItem(index, agent_model)
        self.modelComboBox.setFixedSize(200, 30)
        self.modelComboBox.currentIndexChanged.connect(self.updateWidgetsFromSelectedModel)
        self.scrollAreaFrame.layout().addWidget(self.modelComboBox, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # amount
        # label
        amount_label = QtWidgets.QLabel("Amount")
        amount_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(amount_label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # spin box
        self.amountSpinBox = QtWidgets.QSpinBox()
        self.amountSpinBox.setValue(1)
        self.amountSpinBox.setMinimum(1)
        self.amountSpinBox.setFixedSize(200, 30)
        self.scrollAreaFrame.layout().addWidget(self.amountSpinBox, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # waypoint mode
        # label
        label = QtWidgets.QLabel("Waypoint Mode")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # dropdown
        self.waypointModeComboBox = QtWidgets.QComboBox()
        for mode in PedestrianWaypointMode:
            self.waypointModeComboBox.insertItem(mode.value, mode.name.lower())
        self.waypointModeComboBox.setFixedSize(200, 30)
        self.scrollAreaFrame.layout().addWidget(self.waypointModeComboBox, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # startup mode
        # label
        label = QtWidgets.QLabel("Startup Mode")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # dropdown
        self.startupModeComboBox = QtWidgets.QComboBox()
        for mode in PedestrianStartupMode:
            self.startupModeComboBox.insertItem(mode.value, mode.name.lower())
        self.startupModeComboBox.setFixedSize(200, 30)
        self.startupModeComboBox.currentIndexChanged.connect(self.updateWidgetsFromSelectedStartupMode)
        self.scrollAreaFrame.layout().addWidget(self.startupModeComboBox, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # wait time
        # label
        self.waitTimeLabel = QtWidgets.QLabel("Wait Time (seconds)")
        self.waitTimeLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.waitTimeLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # spin box
        self.waitTimeSpinBox = ArenaQDoubleSpinBox()
        self.waitTimeSpinBox.setFixedSize(200, 30)
        self.scrollAreaFrame.layout().addWidget(self.waitTimeSpinBox, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # trigger zone radius
        # label
        self.triggerZoneLabel = QtWidgets.QLabel("Trigger Zone Radius")
        self.triggerZoneLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.triggerZoneLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # spin box
        self.triggerZoneSpinBox = ArenaQDoubleSpinBox()
        self.triggerZoneSpinBox.setFixedSize(200, 30)
        self.scrollAreaFrame.layout().addWidget(self.triggerZoneSpinBox, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # vmax
        # label
        self.vmax_label = QtWidgets.QLabel("Velocity<sub>max</sub>")
        self.vmax_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.vmax_label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.vmax_slider = ArenaSliderWidget(0, 20, 0.1, "m/s")
        self.scrollAreaFrame.layout().addWidget(self.vmax_slider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # max talking distance
        # label
        self.maxTalkingDistanceLabel = QtWidgets.QLabel("Max Talking Distance")
        self.maxTalkingDistanceLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.maxTalkingDistanceLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.maxTalkingDistanceSlider = ArenaSliderWidget(0, 10, 1, "m")
        self.scrollAreaFrame.layout().addWidget(self.maxTalkingDistanceSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # forces
        # heading
        label = QtWidgets.QLabel("#### Force Factors")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        line = Line()
        self.scrollAreaFrame.layout().addWidget(line, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # Desired
        # label
        label = QtWidgets.QLabel("Desired")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.desiredForceSlider = ArenaSliderWidget(0, 20, 1, "")
        self.desiredForceSlider.slider.setValue(1)
        self.scrollAreaFrame.layout().addWidget(self.desiredForceSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # Obstacle
        # label
        label = QtWidgets.QLabel("Obstacle")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.obstacleForceSlider = ArenaSliderWidget(0, 20, 1, "")
        self.obstacleForceSlider.slider.setValue(1)
        self.scrollAreaFrame.layout().addWidget(self.obstacleForceSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # Social
        # label
        label = QtWidgets.QLabel("Social")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.socialForceSlider = ArenaSliderWidget(0, 20, 1, "")
        self.socialForceSlider.slider.setValue(1)
        self.scrollAreaFrame.layout().addWidget(self.socialForceSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # Robot
        # label
        label = QtWidgets.QLabel("Robot")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(label, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.robotForceSlider = ArenaSliderWidget(0, 20, 1, "")
        self.robotForceSlider.slider.setValue(1)
        self.scrollAreaFrame.layout().addWidget(self.robotForceSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # individual talking
        # heading
        self.individualTalkingLabel = QtWidgets.QLabel("#### Individual Talking")
        self.individualTalkingLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.individualTalkingLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.individualTalkingLine = Line()
        self.scrollAreaFrame.layout().addWidget(self.individualTalkingLine, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # probability
        # label
        self.individualTalkingProbabilityLabel = QtWidgets.QLabel("Probability")
        self.individualTalkingProbabilityLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.individualTalkingProbabilityLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.individualTalkingProbabilitySlider = ArenaProbabilitySliderWidget()
        self.scrollAreaFrame.layout().addWidget(self.individualTalkingProbabilitySlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # base time
        # label
        self.individualTalkingBaseTimeLabel = QtWidgets.QLabel("Base Time")
        self.individualTalkingBaseTimeLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.individualTalkingBaseTimeLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.individualTalkingBaseTimeSlider = ArenaSliderWidget(0, 100, 1, "s")
        self.scrollAreaFrame.layout().addWidget(self.individualTalkingBaseTimeSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # group talk
        # heading
        self.groupTalkLabel = QtWidgets.QLabel("#### Group Talk")
        self.groupTalkLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.groupTalkLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.groupTalkLine = Line()
        self.scrollAreaFrame.layout().addWidget(self.groupTalkLine, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # probability
        # label
        self.groupTalkProbabilityLabel = QtWidgets.QLabel("Probability")
        self.groupTalkProbabilityLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.groupTalkProbabilityLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.groupTalkProbabilitySlider = ArenaProbabilitySliderWidget()
        self.scrollAreaFrame.layout().addWidget(self.groupTalkProbabilitySlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # base time
        # label
        self.groupTalkBaseTimeLabel = QtWidgets.QLabel("Base Time")
        self.groupTalkBaseTimeLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.groupTalkBaseTimeLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.groupTalkBaseTimeSlider = ArenaSliderWidget(0, 100, 1, "s")
        self.scrollAreaFrame.layout().addWidget(self.groupTalkBaseTimeSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # talk and walk
        # heading
        self.talkWalkLabel = QtWidgets.QLabel("#### Talk & Walk")
        self.talkWalkLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.talkWalkLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.talkWalkLine = Line()
        self.scrollAreaFrame.layout().addWidget(self.talkWalkLine, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # probability
        # label
        self.talkWalkProbabilityLabel = QtWidgets.QLabel("Probability")
        self.talkWalkProbabilityLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.talkWalkProbabilityLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.talkWalkProbabilitySlider = ArenaProbabilitySliderWidget()
        self.scrollAreaFrame.layout().addWidget(self.talkWalkProbabilitySlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # base time
        # label
        self.talkWalkBaseTimeLabel = QtWidgets.QLabel("Base Time")
        self.talkWalkBaseTimeLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.talkWalkBaseTimeLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.talkWalkBaseTimeSlider = ArenaSliderWidget(0, 100, 1, "s")
        self.scrollAreaFrame.layout().addWidget(self.talkWalkBaseTimeSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # requesting service
        # heading
        self.requestingServiceLabel = QtWidgets.QLabel("#### Requesting Service")
        self.requestingServiceLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.requestingServiceLine = Line()
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceLine, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # probability
        # label
        self.requestingServiceProbabilityLabel = QtWidgets.QLabel("Probability")
        self.requestingServiceProbabilityLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceProbabilityLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.requestingServiceProbabilitySlider = ArenaProbabilitySliderWidget()
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceProbabilitySlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # max service distance
        # label
        self.maxServiceDistanceLabel = QtWidgets.QLabel("Max Service Distance")
        self.maxServiceDistanceLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.maxServiceDistanceLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.maxServiceDistanceSlider = ArenaSliderWidget(0, 10, 1, "m")
        self.scrollAreaFrame.layout().addWidget(self.maxServiceDistanceSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # base time requesting
        # label
        self.requestingServiceRequestingBaseTimeLabel = QtWidgets.QLabel("Base Time (req.)")
        self.requestingServiceRequestingBaseTimeLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceRequestingBaseTimeLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.requestingServiceRequestingBaseTimeSlider = ArenaSliderWidget(0, 100, 1, "s")
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceRequestingBaseTimeSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # base time receiving
        # label
        self.requestingServiceReceivingBaseTimeLabel = QtWidgets.QLabel("Base Time (recv.)")
        self.requestingServiceReceivingBaseTimeLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceReceivingBaseTimeLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.requestingServiceReceivingBaseTimeSlider = ArenaSliderWidget(0, 100, 1, "s")
        self.scrollAreaFrame.layout().addWidget(self.requestingServiceReceivingBaseTimeSlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # requesting guide
        # heading
        self.requestingGuideLabel = QtWidgets.QLabel("#### Requesting Guide")
        self.requestingGuideLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingGuideLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.requestingGuideLine = Line()
        self.scrollAreaFrame.layout().addWidget(self.requestingGuideLine, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # probability
        # label
        self.requestingGuideProbabilityLabel = QtWidgets.QLabel("Probability")
        self.requestingGuideProbabilityLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingGuideProbabilityLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.requestingGuideProbabilitySlider = ArenaProbabilitySliderWidget()
        self.scrollAreaFrame.layout().addWidget(self.requestingGuideProbabilitySlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # requesting follower
        # heading
        self.requestingFollowerLabel = QtWidgets.QLabel("#### Requesting Follower")
        self.requestingFollowerLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingFollowerLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.requestingFollowerLine = Line()
        self.scrollAreaFrame.layout().addWidget(self.requestingFollowerLine, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1
        # probability
        # label
        self.requestingFollowerProbabilityLabel = QtWidgets.QLabel("Probability")
        self.requestingFollowerProbabilityLabel.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.scrollAreaFrame.layout().addWidget(self.requestingFollowerProbabilityLabel, vertical_idx, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        # slider
        self.requestingFollowerProbabilitySlider = ArenaProbabilitySliderWidget()
        self.scrollAreaFrame.layout().addWidget(self.requestingFollowerProbabilitySlider, vertical_idx, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        vertical_idx += 1

        # save button
        self.save_button = QtWidgets.QPushButton("Save and Close")
        self.save_button.clicked.connect(self.onSaveClicked)
        self.layout().addWidget(self.save_button, 1, 0, -1, -1)

    def updateWidgetsFromSelectedStartupMode(self):
        mode = PedestrianStartupMode(self.startupModeComboBox.currentIndex())
        if mode == PedestrianStartupMode.DEFAULT:
            self.waitTimeLabel.hide()
            self.waitTimeSpinBox.hide()
            self.triggerZoneLabel.hide()
            self.triggerZoneSpinBox.hide()
        elif mode == PedestrianStartupMode.WAIT_TIMER:
            self.waitTimeLabel.show()
            self.waitTimeSpinBox.show()
            self.triggerZoneLabel.hide()
            self.triggerZoneSpinBox.hide()
        elif mode == PedestrianStartupMode.TRIGGER_ZONE:
            self.waitTimeLabel.hide()
            self.waitTimeSpinBox.hide()
            self.triggerZoneLabel.show()
            self.triggerZoneSpinBox.show()

    def updateWidgetsFromSelectedType(self):
        agent_type = PedestrianAgentType(self.typeComboBox.currentIndex())
        if agent_type in [PedestrianAgentType.ADULT, PedestrianAgentType.CHILD, PedestrianAgentType.ELDER]:
            # max talking distance
            self.maxTalkingDistanceLabel.show()
            self.maxTalkingDistanceSlider.show()
            # individual talking
            self.individualTalkingLabel.show()
            self.individualTalkingLine.show()
            self.individualTalkingProbabilityLabel.show()
            self.individualTalkingProbabilitySlider.show()
            self.individualTalkingBaseTimeLabel.show()
            self.individualTalkingBaseTimeSlider.show()
            # group talk
            self.groupTalkLabel.show()
            self.groupTalkLine.show()
            self.groupTalkProbabilityLabel.show()
            self.groupTalkProbabilitySlider.show()
            self.groupTalkBaseTimeLabel.show()
            self.groupTalkBaseTimeSlider.show()
            # talk and walk
            self.talkWalkLabel.show()
            self.talkWalkLine.show()
            self.talkWalkProbabilityLabel.show()
            self.talkWalkProbabilitySlider.show()
            self.talkWalkBaseTimeLabel.show()
            self.talkWalkBaseTimeSlider.show()
            # requesting service
            self.requestingServiceLabel.show()
            self.requestingServiceLine.show()
            self.requestingServiceProbabilityLabel.show()
            self.requestingServiceProbabilitySlider.show()
            self.maxServiceDistanceLabel.hide()
            self.maxServiceDistanceSlider.hide()
            self.requestingServiceRequestingBaseTimeLabel.show()
            self.requestingServiceRequestingBaseTimeSlider.show()
            self.requestingServiceReceivingBaseTimeLabel.show()
            self.requestingServiceReceivingBaseTimeSlider.show()
            # requesting guide
            self.requestingGuideLabel.show()
            self.requestingGuideLine.show()
            self.requestingGuideProbabilityLabel.show()
            self.requestingGuideProbabilitySlider.show()
            # requesting follower
            self.requestingFollowerLabel.show()
            self.requestingFollowerLine.show()
            self.requestingFollowerProbabilityLabel.show()
            self.requestingFollowerProbabilitySlider.show()

        elif agent_type == PedestrianAgentType.FORKLIFT:
            # max talking distance
            self.maxTalkingDistanceLabel.hide()
            self.maxTalkingDistanceSlider.hide()
            # individual talking
            self.individualTalkingLabel.hide()
            self.individualTalkingLine.hide()
            self.individualTalkingProbabilityLabel.hide()
            self.individualTalkingProbabilitySlider.hide()
            self.individualTalkingBaseTimeLabel.hide()
            self.individualTalkingBaseTimeSlider.hide()
            # group talk
            self.groupTalkLabel.hide()
            self.groupTalkLine.hide()
            self.groupTalkProbabilityLabel.hide()
            self.groupTalkProbabilitySlider.hide()
            self.groupTalkBaseTimeLabel.hide()
            self.groupTalkBaseTimeSlider.hide()
            # talk and walk
            self.talkWalkLabel.hide()
            self.talkWalkLine.hide()
            self.talkWalkProbabilityLabel.hide()
            self.talkWalkProbabilitySlider.hide()
            self.talkWalkBaseTimeLabel.hide()
            self.talkWalkBaseTimeSlider.hide()
            # requesting service
            self.requestingServiceLabel.hide()
            self.requestingServiceLine.hide()
            self.requestingServiceProbabilityLabel.hide()
            self.requestingServiceProbabilitySlider.hide()
            self.maxServiceDistanceLabel.hide()
            self.maxServiceDistanceSlider.hide()
            self.requestingServiceRequestingBaseTimeLabel.hide()
            self.requestingServiceRequestingBaseTimeSlider.hide()
            self.requestingServiceReceivingBaseTimeLabel.hide()
            self.requestingServiceReceivingBaseTimeSlider.hide()
            # requesting guide
            self.requestingGuideLabel.hide()
            self.requestingGuideLine.hide()
            self.requestingGuideProbabilityLabel.hide()
            self.requestingGuideProbabilitySlider.hide()
            # requesting follower
            self.requestingFollowerLabel.hide()
            self.requestingFollowerLine.hide()
            self.requestingFollowerProbabilityLabel.hide()
            self.requestingFollowerProbabilitySlider.hide()

        elif agent_type == PedestrianAgentType.SERVICEROBOT:
            # max talking distance
            self.maxTalkingDistanceLabel.hide()
            self.maxTalkingDistanceSlider.hide()
            # individual talking
            self.individualTalkingLabel.hide()
            self.individualTalkingLine.hide()
            self.individualTalkingProbabilityLabel.hide()
            self.individualTalkingProbabilitySlider.hide()
            self.individualTalkingBaseTimeLabel.hide()
            self.individualTalkingBaseTimeSlider.hide()
            # group talk
            self.groupTalkLabel.hide()
            self.groupTalkLine.hide()
            self.groupTalkProbabilityLabel.hide()
            self.groupTalkProbabilitySlider.hide()
            self.groupTalkBaseTimeLabel.hide()
            self.groupTalkBaseTimeSlider.hide()
            # talk and walk
            self.talkWalkLabel.hide()
            self.talkWalkLine.hide()
            self.talkWalkProbabilityLabel.hide()
            self.talkWalkProbabilitySlider.hide()
            self.talkWalkBaseTimeLabel.hide()
            self.talkWalkBaseTimeSlider.hide()
            # requesting service
            self.requestingServiceLabel.show()
            self.requestingServiceLine.show()
            self.requestingServiceProbabilityLabel.hide()
            self.requestingServiceProbabilitySlider.hide()
            self.maxServiceDistanceLabel.show()
            self.maxServiceDistanceSlider.show()
            self.requestingServiceRequestingBaseTimeLabel.hide()
            self.requestingServiceRequestingBaseTimeSlider.hide()
            self.requestingServiceReceivingBaseTimeLabel.hide()
            self.requestingServiceReceivingBaseTimeSlider.hide()
            # requesting guide
            self.requestingGuideLabel.hide()
            self.requestingGuideLine.hide()
            self.requestingGuideProbabilityLabel.hide()
            self.requestingGuideProbabilitySlider.hide()
            # requesting follower
            self.requestingFollowerLabel.hide()
            self.requestingFollowerLine.hide()
            self.requestingFollowerProbabilityLabel.hide()
            self.requestingFollowerProbabilitySlider.hide()

    def updateValuesFromPedestrianAgent(self):
        self.typeComboBox.setCurrentIndex(PedestrianAgentType[self.pedestrianAgent.type.upper()].value)
        self.modelComboBox.setCurrentText(self.pedestrianAgent.model)
        self.modelComboBox.setCurrentText(self.pedestrianAgent.model)
        self.amountSpinBox.setValue(self.pedestrianAgent.number_of_peds)
        self.vmax_slider.setValue(self.pedestrianAgent.vmax)

        self.startupModeComboBox.setCurrentIndex(PedestrianStartupMode[self.pedestrianAgent.start_up_mode.upper()].value)
        self.waitTimeSpinBox.setValue(self.pedestrianAgent.wait_time)
        self.triggerZoneSpinBox.setValue(self.pedestrianAgent.trigger_zone_radius)

        self.individualTalkingProbabilitySlider.setValue(self.pedestrianAgent.chatting_probability)
        self.groupTalkProbabilitySlider.setValue(self.pedestrianAgent.group_talking_probability)
        self.talkWalkProbabilitySlider.setValue(self.pedestrianAgent.talking_and_walking_probability)
        self.requestingServiceProbabilitySlider.setValue(self.pedestrianAgent.requesting_service_probability)
        self.requestingGuideProbabilitySlider.setValue(self.pedestrianAgent.requesting_guide_probability)
        self.requestingFollowerProbabilitySlider.setValue(self.pedestrianAgent.requesting_follower_probability)

        self.maxTalkingDistanceSlider.setValue(self.pedestrianAgent.max_talking_distance)
        self.maxServiceDistanceSlider.setValue(self.pedestrianAgent.max_servicing_radius)

        self.individualTalkingBaseTimeSlider.setValue(self.pedestrianAgent.talking_base_time)
        self.groupTalkBaseTimeSlider.setValue(self.pedestrianAgent.group_talking_base_time)
        self.talkWalkBaseTimeSlider.setValue(self.pedestrianAgent.talking_and_walking_base_time)
        self.requestingServiceReceivingBaseTimeSlider.setValue(self.pedestrianAgent.receiving_service_base_time)
        self.requestingServiceRequestingBaseTimeSlider.setValue(self.pedestrianAgent.requesting_service_base_time)

        # forces
        self.desiredForceSlider.setValue(self.pedestrianAgent.force_factor_desired)
        self.obstacleForceSlider.setValue(self.pedestrianAgent.force_factor_obstacle)
        self.socialForceSlider.setValue(self.pedestrianAgent.force_factor_social)
        self.robotForceSlider.setValue(self.pedestrianAgent.force_factor_robot)

        self.waypointModeComboBox.setCurrentIndex(PedestrianWaypointMode(self.pedestrianAgent.waypoint_mode).value)

        self.name_edit.setText(self.pedestrianAgent.name)

    def updateWidgetsFromSelectedModel(self):
        ...

    def show(self):
        self.updateValuesFromPedestrianAgent()
        return super().show()

    def updatePedestrianAgentFromWidgets(self, agent: Pedestrian):
        agent.type = PedestrianAgentType(self.typeComboBox.currentIndex()).name.lower()
        agent.model = self.modelComboBox.currentText()
        agent.number_of_peds = self.amountSpinBox.value()
        agent.vmax = self.vmax_slider.getValue()

        agent.start_up_mode = PedestrianStartupMode(self.startupModeComboBox.currentIndex()).name.lower()
        agent.wait_time = self.waitTimeSpinBox.value()
        agent.trigger_zone_radius = self.triggerZoneSpinBox.value()

        agent.chatting_probability = self.individualTalkingProbabilitySlider.getValue()
        agent.group_talking_probability = self.groupTalkProbabilitySlider.getValue()
        agent.talking_and_walking_probability = self.talkWalkProbabilitySlider.getValue()
        agent.requesting_service_probability = self.requestingServiceProbabilitySlider.getValue()
        agent.requesting_guide_probability = self.requestingGuideProbabilitySlider.getValue()
        agent.requesting_follower_probability = self.requestingFollowerProbabilitySlider.getValue()

        agent.max_talking_distance = self.maxTalkingDistanceSlider.getValue()
        agent.max_servicing_radius = self.maxServiceDistanceSlider.getValue()

        agent.talking_base_time = self.individualTalkingBaseTimeSlider.getValue()
        agent.group_talking_base_time = self.groupTalkBaseTimeSlider.getValue()
        agent.talking_and_walking_base_time = self.talkWalkBaseTimeSlider.getValue()
        agent.receiving_service_base_time = self.requestingServiceReceivingBaseTimeSlider.getValue()
        agent.requesting_service_base_time = self.requestingServiceRequestingBaseTimeSlider.getValue()

        # forces
        agent.force_factor_desired = self.desiredForceSlider.getValue()
        agent.force_factor_obstacle = self.obstacleForceSlider.getValue()
        agent.force_factor_social = self.socialForceSlider.getValue()
        agent.force_factor_robot = self.robotForceSlider.getValue()

        agent.waypoint_mode = PedestrianWaypointMode(self.waypointModeComboBox.currentIndex()).value

        agent.name = self.name_edit.text()

    def onSaveClicked(self):
        self.updatePedestrianAgentFromWidgets(self.pedestrianAgent)
        self.hide()
        self.editorSaved.emit()

    def closeEvent(self, event):
        # check if any changes have been made
        current_agent = copy.deepcopy(self.pedestrianAgent)
        self.updatePedestrianAgentFromWidgets(current_agent)
        if self.pedestrianAgent != current_agent:
            # ask user if changes should be saved
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText("Do you want to save changes to this agent?")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.Save)
            ret = msg_box.exec()
            if ret == QtWidgets.QMessageBox.Save:
                self.onSaveClicked()
            elif ret == QtWidgets.QMessageBox.Discard:
                # reset to values already saved
                self.updateValuesFromPedestrianAgent()
            elif ret == QtWidgets.QMessageBox.Cancel:
                event.ignore()


class PedestrianAgentEditorGlobalConfig(PedestrianAgentEditor):
    """
    A Pedestrian Agent Editor excluding widgets that shouldn't be globally configured
    and without a parent PedestrianAgentWidget.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_ui(self):
        super().setup_ui()
        self.nameLabel.hide()
        self.name_edit.hide()
