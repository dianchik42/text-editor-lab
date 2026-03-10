import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter, QTextEdit,
                               QFileDialog, QMessageBox, QDialog, QVBoxLayout,
                               QLabel, QPushButton, QTextBrowser)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QIcon


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ========== НАСТРОЙКА ОКНА ==========
        self.setWindowTitle("Текстовый редактор")
        self.resize(1000, 700)
        
        self.current_file = None
        self.is_modified = False
        
        # Установка иконки приложения
        app_icon = QIcon("static/Приложение.png")
        self.setWindowIcon(app_icon)

        # ========== СОЗДАЕМ ИНТЕРФЕЙС ==========
        self.setup_ui()
        self.create_menus()
        self.create_toolbar()
        
    def setup_ui(self):
        """Создание областей редактирования"""
        splitter = QSplitter(Qt.Horizontal)
        
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Введите текст здесь")
        self.editor.setUndoRedoEnabled(True)
        
        self.editor.textChanged.connect(self.on_text_changed)
        
        self.output = QTextEdit()
        self.output.setPlaceholderText("Результаты работы анализатора")
        self.output.setReadOnly(True)
        
        splitter.addWidget(self.editor)
        splitter.addWidget(self.output)
        
        splitter.setSizes([500, 500])
        
        self.setCentralWidget(splitter)
    
    def load_icon(self, name):
        """Загрузка иконки из папки static"""
        icon_path = f"static/{name}.png"
        icon = QIcon(icon_path)
        return icon
    
    def create_menus(self):
        """Создание главного меню"""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        file_menu.setIcon(self.load_icon("Файл"))
        
        self.new_action = QAction("Создать", self) 
        self.new_action.setShortcut(QKeySequence.New)
        self.new_action.triggered.connect(self.new_file)
        file_menu.addAction(self.new_action)
        
        self.open_action = QAction("Открыть", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self.open_file)
        file_menu.addAction(self.open_action)
        
        self.save_action = QAction("Сохранить", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self.save_file)
        file_menu.addAction(self.save_action)
        
        self.save_as_action = QAction("Сохранить как", self)
        self.save_as_action.setShortcut(QKeySequence.SaveAs)
        self.save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(self.save_as_action)
        
        file_menu.addSeparator()
        
        self.exit_action = QAction("Выход", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)
        
        edit_menu = menubar.addMenu("Правка")
        edit_menu.setIcon(self.load_icon("Правка"))
        
        self.undo_action = QAction("Отменить", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("Повторить", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        
        self.cut_action = QAction("Вырезать", self)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(self.cut_action)
        
        self.copy_action = QAction("Копировать", self)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(self.copy_action)
        
        self.paste_action = QAction("Вставить", self)
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(self.paste_action)
        
        self.delete_action = QAction("Удалить", self)
        self.delete_action.setShortcut(QKeySequence.Delete)
        self.delete_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(self.delete_action)
        
        edit_menu.addSeparator()
        
        self.select_all_action = QAction("Выделить все", self)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)
        self.select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(self.select_all_action)
        
        text_menu = menubar.addMenu(self.load_icon("Текст"), "Текст")
        
        self.task_action = QAction("Постановка задачи", self) 
        self.task_action.triggered.connect(self.show_task)
        text_menu.addAction(self.task_action)
        
        self.grammar_action = QAction("Грамматика", self)
        self.grammar_action.triggered.connect(self.show_grammar)
        text_menu.addAction(self.grammar_action)
        
        self.classification_action = QAction("Классификация грамматики", self) 
        self.classification_action.triggered.connect(self.show_classification)
        text_menu.addAction(self.classification_action)
        
        self.start_menu = menubar.addMenu(self.load_icon("Пуск"), "Пуск")

        self.start_action = QAction("Запуск анализатора", self)
        self.start_action.triggered.connect(self.run_analyzer)
        self.start_menu.addAction(self.start_action)
        
        help_menu = menubar.addMenu(self.load_icon("Справка"), "Справка")
        
        self.help_action = QAction("Вызов справки", self)
        self.help_action.setShortcut("F1")
        self.help_action.triggered.connect(self.show_help)
        help_menu.addAction(self.help_action)
        
        help_menu.addSeparator()
        
        self.about_action = QAction("О программе", self)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar("Инструменты")
        toolbar.setMovable(False)
        
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(self.cut_action)
        toolbar.addAction(self.copy_action)
        toolbar.addAction(self.paste_action)
        toolbar.addSeparator()
        toolbar.addAction(self.start_action)
        toolbar.addAction(self.help_action)
        toolbar.addAction(self.about_action)

    def new_file(self):
        """Создать новый файл"""
        if self.maybe_save():
            self.editor.clear()
            self.current_file = None
            self.is_modified = False
            self.setWindowTitle("Текстовый редактор")
            self.output.append("Создан новый файл")
    
    def open_file(self):
        """Открыть файл"""
        if self.maybe_save():
            file_name, _ = QFileDialog.getOpenFileName(
                self, 
                "Открыть файл",
                "",
                "Текстовые файлы (*.txt);;Все файлы (*.*)"
            )
            if file_name:
                try:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        text = f.read()
                    self.editor.setText(text)
                    self.current_file = file_name
                    self.is_modified = False
                    self.setWindowTitle(f"Текстовый редактор - {file_name}")
                    self.output.append(f"Открыт файл: {file_name}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{str(e)}")
    
    def save_file(self):
        """Сохранить файл"""
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.is_modified = False
                self.setWindowTitle(f"Текстовый редактор - {self.current_file}")
                self.output.append(f"Файл сохранен: {self.current_file}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
                return False
        else:
            return self.save_as_file()
    
    def save_as_file(self):
        """Сохранить файл как"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        if file_name:
            self.current_file = file_name
            return self.save_file()
        return False
    
    def maybe_save(self):
        """Спросить, нужно ли сохранить изменения"""
        if not self.is_modified:
            return True
        
        reply = QMessageBox.question(
            self,
            "Сохранение",
            "Файл был изменен. Сохранить изменения?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            return self.save_file()
        elif reply == QMessageBox.No:
            return True
        else:
            return False
    
    def on_text_changed(self):
        """Обработчик изменения текста"""
        if not self.is_modified:
            self.is_modified = True
            if self.current_file:
                self.setWindowTitle(f"Текстовый редактор - {self.current_file} *")
            else:
                self.setWindowTitle("Текстовый редактор - [Новый файл] *")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()
    
    # ========== ФУНКЦИИ ДЛЯ СПРАВКИ ==========
    
    def run_analyzer(self):
        """Запуск анализатора"""
        self.output.append("Не сейчас")
        QMessageBox.information(self, "Пуск", "Не сейчас")
    
    def show_help(self):
        """Показать справку"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Справка")
        help_dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml("""
        <h1>Текстовый редактор</h1>
        <h2>Руководство пользователя</h2>
        
        <h3>Меню Файл</h3>
        <ul>
            <li><b>Создать</b> - создать новый документ (Ctrl+N)</li>
            <li><b>Открыть</b> - открыть существующий файл (Ctrl+O)</li>
            <li><b>Сохранить</b> - сохранить текущий документ (Ctrl+S)</li>
            <li><b>Сохранить как</b> - сохранить документ под новым именем (Ctrl+Shift+S)</li>
            <li><b>Выход</b> - выйти из программы (Ctrl+Q)</li>
        </ul>
        
        <h3>Меню Правка</h3>
        <ul>
            <li><b>Отменить</b> - отменить последнее действие (Ctrl+Z)</li>
            <li><b>Повторить</b> - повторить отмененное действие (Ctrl+Y)</li>
            <li><b>Вырезать</b> - вырезать выделенный текст (Ctrl+X)</li>
            <li><b>Копировать</b> - копировать выделенный текст (Ctrl+C)</li>
            <li><b>Вставить</b> - вставить текст из буфера (Ctrl+V)</li>
            <li><b>Удалить</b> - удалить выделенный текст (Del)</li>
            <li><b>Выделить все</b> - выделить весь текст (Ctrl+A)</li>
        </ul>
        
        <h3>Меню Справка</h3>
        <ul>
            <li><b>Вызов справки</b> - показать это окно (F1)</li>
            <li><b>О программе</b> - информация о программе</li>
        </ul>
        
        <p>Версия: 1.0.0</p>
        <p>Дата: 07.03.2026</p>
        """)
        
        layout.addWidget(text_browser)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(help_dialog.close)
        layout.addWidget(close_btn)
        
        help_dialog.setLayout(layout)
        help_dialog.exec()
    
    def show_about(self):
        """Показать окно 'О программе'"""
        QMessageBox.about(
            self,
            "О программе",
            "<h1>Текстовый редактор</h1>"
            "<p>Версия: 1.0.0</p>"
            "<p>Лабораторная работа №1</p>"
            "<p>Текстовый редактор с графическим интерфейсом</p>"
            "<p>Разработчик: Базыкина Диана</p>"
            "<p>2026</p>"
        )

    # ========== МЕТОДЫ ДЛЯ МЕНЮ "ТЕКСТ" ==========
    
    def show_task(self):
        """Постановка задачи"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Постановка задачи")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        text = QTextBrowser()
        text.setHtml("""
        <h1>Постановка задачи</h1>
        <p>Разработать текстовый редактор с графическим интерфейсом.</p>
        <p>В дальнейшем редактор будет дополнен функциями языкового процессора.</p>
        """)
        
        layout.addWidget(text)
        
        btn = QPushButton("Закрыть")
        btn.clicked.connect(dialog.close)
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec()
        
    def show_grammar(self):
        """Грамматика"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Грамматика")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        text = QTextBrowser()
        text.setHtml("""
        <h1>Грамматика</h1>
        <p>G = (V<sub>T</sub>, V<sub>N</sub>, P, S)</p>
        """)
        
        layout.addWidget(text)
        
        btn = QPushButton("Закрыть")
        btn.clicked.connect(dialog.close)
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_classification(self):
        """Классификация грамматики"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Классификация грамматики")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        text = QTextBrowser()
        text.setHtml("""
        <h1>Классификация грамматики</h1>
        <p>Тип 2 - Контекстно-свободная грамматика</p>
        """)
        
        layout.addWidget(text)
        
        btn = QPushButton("Закрыть")
        btn.clicked.connect(dialog.close)
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())