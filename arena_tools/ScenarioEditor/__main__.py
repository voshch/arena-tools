from PyQt5 import QtWidgets

from .ArenaScenarioEditor import ArenaScenarioEditor


def main():

    app = QtWidgets.QApplication([])

    widget = ArenaScenarioEditor()
    widget.show()

    app.exec()


if __name__ == "__main__":
    main()
