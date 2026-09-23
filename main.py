import sys
from PySide6.QtWidgets import QApplication
from text_editor.ui.editor import TextEditor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())