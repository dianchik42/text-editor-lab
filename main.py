import sys
from PySide6.QtWidgets import QApplication
from editor import TextEditor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())