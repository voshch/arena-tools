from .ZonesEditor import ZonesEditor
from PyQt5 import QtWidgets


def main():
    app = QtWidgets.QApplication([])

    widget = ZonesEditor()
    widget.show()

    app.exec()


if __name__ == "__main__":
    main()
