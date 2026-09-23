import sys
from PySide6.QtWidgets import (QMainWindow, QSplitter, QTextEdit,
                               QFileDialog, QMessageBox, QDialog, QVBoxLayout,
                               QLabel, QPushButton, QTextBrowser, QTableWidget,
                               QTableWidgetItem, QHeaderView, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QIcon, QTextCursor, QColor
from syntax_parser import Parser, SyntaxError

from regex_search import RULES, find_matches
from scanner import Scanner
from grammar import SYNTAX_GRAMMAR
from html import escape


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ========== НАСТРОЙКА ОКНА ==========
        self.setWindowTitle("Текстовый редактор")
        self.resize(1000, 700)
        
        self.current_file = None
        self.is_modified = False
        self.result_mode = None
        
        # Сканер
        self.scanner = Scanner()
        
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
        
        # Левая панель: редактор
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Введите текст здесь")
        self.editor.setUndoRedoEnabled(True)
        self.editor.setAcceptRichText(False)
        self.editor.textChanged.connect(self.on_text_changed)
        
        # Правая панель: таблица результатов
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Код", "Тип", "Лексема", "Позиция"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Подключаем обработчик клика по таблице для навигации к ошибкам
        self.result_table.itemClicked.connect(self.on_table_item_clicked)
        self.result_table.itemSelectionChanged.connect(self.on_result_selection_changed)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setSelectionMode(QTableWidget.SingleSelection)
        
        splitter.addWidget(self.editor)
        splitter.addWidget(self.result_table)
        
        splitter.setSizes([500, 500])
        
        self.setCentralWidget(splitter)
        self.analysis_status = QLabel("Анализ ещё не выполнен")
        self.statusBar().addWidget(self.analysis_status, 1)
    
    def load_icon(self, name):
        """Загрузка иконки из папки static"""
        icon_path = f"static/{name}.png"
        icon = QIcon(icon_path)
        return icon
    
    def create_menus(self):
        """Создание главного меню"""
        menubar = self.menuBar()
        
        # Меню Файл
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
        
        # Меню Правка
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
        
        # Меню Текст
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
        
        # Меню Пуск
        self.start_menu = menubar.addMenu(self.load_icon("Пуск"), "Пуск")
        self.start_action = QAction("Лексический анализ", self)
        self.start_action.triggered.connect(self.run_analyzer)
        self.start_menu.addAction(self.start_action)
        self.syntax_action = QAction("Синтаксический анализ", self)
        self.syntax_action.triggered.connect(self.run_syntax_analyzer)
        self.start_menu.addAction(self.syntax_action)
        self.search_action = QAction("Поиск подстрок", self)
        self.search_action.triggered.connect(self.run_regex_search)
        self.start_menu.addAction(self.search_action)
        
        # Меню Справка
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
        toolbar.addAction(self.syntax_action)
        toolbar.addAction(self.help_action)
        toolbar.addAction(self.about_action)
        self.addToolBarBreak()
        search_toolbar = self.addToolBar("Поиск по регулярным выражениям")
        search_toolbar.setMovable(False)
        search_toolbar.addWidget(QLabel("Тип поиска: "))
        self.search_type = QComboBox()
        self.search_type.setAccessibleName("Тип поиска подстрок")
        for rule in RULES:
            self.search_type.addItem(rule.title)
            self.search_type.setItemData(self.search_type.count() - 1, rule.description, Qt.ToolTipRole)
        self.search_type.currentIndexChanged.connect(self.on_search_type_changed)
        search_toolbar.addWidget(self.search_type)
        search_toolbar.addAction(self.search_action)
    
    # ========== РАБОТА С ФАЙЛАМИ ==========
    
    def new_file(self):
        """Создать новый файл"""
        if self.maybe_save():
            self.editor.clear()
            self.current_file = None
            self.is_modified = False
            self.setWindowTitle("Текстовый редактор")
            self.result_table.setRowCount(0)  # Очистить таблицу
    
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
                    self.result_table.setRowCount(0)  # Очистить таблицу
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
        if self.result_mode == "search":
            self.clear_search_results("Текст изменён. Запустите поиск повторно.")
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
    
    # ========== ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР ==========
    
    def run_analyzer(self):
        """Запуск лексического анализатора"""
        text = self.editor.toPlainText()
        
        self.prepare_results(["Код", "Тип", "Лексема", "Позиция"])
        # Запускаем сканер
        tokens, errors = self.scanner.scan(text)
        
        # Заполняем таблицу результатов
        self.result_table.setRowCount(len(tokens) + len(errors))
        
        tokens = [t for t in tokens if t.type != "UNKNOWN"]
        self.result_table.setRowCount(len(tokens) + len(errors))
        row = 0
        # Токены
        for token in tokens:
            self.result_table.setItem(row, 0, QTableWidgetItem(str(token.code)))
            self.result_table.setItem(row, 1, QTableWidgetItem(token.type))
            self.result_table.setItem(row, 2, QTableWidgetItem(token.lexeme))
            self.result_table.setItem(row, 3, QTableWidgetItem(f"строка {token.line}, [{token.start}:{token.end}]"))
            
            # Для ошибок сохраняем дополнительные данные
            self.result_table.item(row, 0).setData(Qt.UserRole, ('token', token.line, token.start))
            row += 1
        
        # Ошибки
        for error in errors:
            self.result_table.setItem(row, 0, QTableWidgetItem("!"))
            self.result_table.setItem(row, 1, QTableWidgetItem("ОШИБКА"))
            self.result_table.setItem(row, 2, QTableWidgetItem(error.character))
            self.result_table.setItem(row, 3, QTableWidgetItem(f"строка {error.line}, [{error.col}:{error.col}]"))
            
            # Сохраняем данные для навигации
            self.result_table.item(row, 0).setData(Qt.UserRole, ('error', error.line, error.col))
            row += 1
        
        self.analysis_status.setText(f"Лексем: {len(tokens)}. Общее количество ошибок: {len(errors)}")

    def prepare_results(self, headers):
        self.result_mode = None
        self.editor.setExtraSelections([])
        cursor = self.editor.textCursor()
        cursor.clearSelection()
        self.editor.setTextCursor(cursor)
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.analysis_status.setText("Анализ выполняется…")

    def run_syntax_analyzer(self):
        """Последовательный запуск ЛР2 и ЛР3, включая ошибочный вход."""
        self.prepare_results(["Неверный фрагмент", "Местоположение", "Описание ошибки"])
        text = self.editor.toPlainText()
        tokens, lex_errors = self.scanner.scan(text)
        parser = Parser(tokens, text)
        parser.parse_program()
        errors = [SyntaxError(e.character, e.line, e.col, "Лексическая ошибка: " + e.message)
                  for e in lex_errors] + parser.errors
        errors.sort(key=lambda e: (e.line, e.col))
        self.result_table.setRowCount(len(errors))
        for row, err in enumerate(errors):
            self.result_table.setItem(row, 0, QTableWidgetItem(err.fragment))
            self.result_table.setItem(row, 1, QTableWidgetItem(f"строка {err.line}, позиция {err.col}"))
            self.result_table.setItem(row, 2, QTableWidgetItem(err.description))
            self.result_table.item(row, 0).setData(Qt.UserRole, (err.line, err.col))
        message = f"Общее количество ошибок: {len(errors)}"
        if not errors:
            message += ". Синтаксис корректен, ошибок нет."
        self.analysis_status.setText(message)

    def clear_search_results(self, message):
        self.editor.setExtraSelections([])
        cursor = self.editor.textCursor()
        cursor.clearSelection()
        self.editor.setTextCursor(cursor)
        self.result_table.setRowCount(0)
        self.analysis_status.setText(message)

    def on_search_type_changed(self):
        if self.result_mode == "search":
            self.clear_search_results("Тип поиска изменён. Запустите поиск повторно.")

    def run_regex_search(self):
        self.prepare_results(["Найденная подстрока", "Начальная позиция", "Длина"])
        self.result_mode = "search"
        text = self.editor.toPlainText()
        if not text.strip():
            self.analysis_status.setText("Нет данных для поиска")
            return
        matches = find_matches(text, self.search_type.currentIndex())
        self.result_table.setRowCount(len(matches))
        for row, match in enumerate(matches):
            item = QTableWidgetItem(match.fragment)
            item.setData(Qt.UserRole, ("match", match.start, match.length))
            self.result_table.setItem(row, 0, item)
            self.result_table.setItem(row, 1, QTableWidgetItem(
                f"строка {match.line}, символ {match.column}"))
            length_item = QTableWidgetItem()
            length_item.setData(Qt.DisplayRole, match.length)
            self.result_table.setItem(row, 2, length_item)
        self.analysis_status.setText(f"Найдено совпадений: {len(matches)}")

    def on_result_selection_changed(self):
        if self.result_mode == "search":
            rows = self.result_table.selectionModel().selectedRows()
            if rows:
                self.on_table_item_clicked(self.result_table.item(rows[0].row(), 0))

    def highlight_match(self, start, length):
        text = self.editor.toPlainText()
        qt_start = len(text[:start].encode("utf-16-le")) // 2
        qt_end = qt_start + len(text[start:start + length].encode("utf-16-le")) // 2
        cursor = self.editor.textCursor()
        cursor.setPosition(qt_start)
        cursor.setPosition(qt_end, QTextCursor.KeepAnchor)
        self.editor.setTextCursor(cursor)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        selection.format.setBackground(QColor("#ffe082"))
        selection.format.setForeground(QColor("#202020"))
        self.editor.setExtraSelections([selection])
        self.editor.ensureCursorVisible()

    def on_table_item_clicked(self, item):
        """Обработка клика по элементу таблицы для навигации"""
        row = item.row()
        first_item = self.result_table.item(row, 0)
        if not first_item:
            return
        data = first_item.data(Qt.UserRole)
        if not data:
            return

        if isinstance(data, (tuple, list)) and len(data) == 3 and data[0] == "match":
            self.highlight_match(data[1], data[2])
            return

        # Синтаксический режим: данные = (line, col)
        if isinstance(data, (tuple, list)) and len(data) == 2:
            line_num, col_num = data
            self.jump_to_position(line_num, col_num)
        # Лексический режим: данные = ('token', line, col) или ('error', line, col)
        elif isinstance(data, (tuple, list)) and len(data) == 3 and data[0] in ('token', 'error'):
            line_num, col_num = data[1], data[2]
            self.jump_to_position(line_num, col_num)
    
    def jump_to_position(self, line_num, col_num):
        """Перемещает курсор на указанную строку и позицию"""
        block = self.editor.document().findBlockByNumber(max(0, line_num - 1))
        if not block.isValid():
            return
        # Qt хранит позиции в UTF-16, сканер считает символы Python.
        prefix = block.text()[:max(0, col_num - 1)]
        offset = len(prefix.encode("utf-16-le")) // 2
        cursor = QTextCursor(block)
        cursor.setPosition(block.position() + offset)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self.editor.ensureCursorVisible()

    # ========== ФУНКЦИИ ДЛЯ СПРАВКИ И МЕНЮ ==========
    
    def show_help(self):
        """Показать справку"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Справка")
        help_dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml("""
        <h1>Текстовый редактор с лексическим анализатором</h1>
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
        
        <h3>Анализаторы</h3><p>Пуск → Синтаксический анализ: проверка объявлений double x = 1.23e+4; с нейтрализацией ошибок. Общее количество ошибок показано в строке состояния.</p>
        <ul>
            <li><b>Пуск → Запуск анализатора</b> - выполнить лексический анализ текста</li>
            <li><b>Таблица результатов</b> - показывает все найденные лексемы и ошибки</li>
            <li><b>Клик по ошибке</b> - перемещает курсор к месту ошибки</li>
        </ul>
        
        <h3>Поиск подстрок — ЛР4</h3>
        <p>Выберите HEX-цвет, юзернейм или пароль на панели «Тип поиска», затем нажмите
        «Поиск подстрок» на панели или в меню «Пуск». Таблица показывает фрагмент,
        строку, символ и длину. Выберите строку мышью или клавиатурой для подсветки.
        После изменения текста или типа поиска выполните поиск повторно.</p>
        <p>HEX: шесть цифр, # необязателен. Юзернейм: 8–16 символов a–z, 0–9, _, -.
        Пароли разделяются пробелами и переводами строк; длина от 14 символов,
        русские буквы обоих регистров, цифра и специальный символ.</p>
        <h3>Распознаваемые лексемы</h3>
        <ul>
            <li><b>Ключевые слова</b>: if, else, while, for, int, float, return и др.</li>
            <li><b>Идентификаторы</b>: буква + буквы/цифры/_</li>
            <li><b>Числа</b>: десятичные целые, дробные и научная нотация</li>
            <li><b>Строки</b>: в двойных кавычках</li>
            <li><b>Символы</b>: в одинарных кавычках</li>
            <li><b>Операторы</b>: +, -, *, /, =, ==, !=, &&, || и др.</li>
            <li><b>Разделители</b>: (, ), {, }, [, ], ;, ,</li>
        </ul>
        
        <p>Версия: 2.0.0 (с лексическим анализатором)</p>
        <p>Дата: 09.04.2026</p>
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
            "<h1>Текстовый редактор с лексическим анализатором</h1>"
            "<p>Версия: 2.0.0</p>"
            "<p>Лабораторные работы №1–4</p>"
            "<p>Текстовый редактор с графическим интерфейсом и лексическим анализатором</p>"
            "<p>Разработчик: Базыкина Диана</p>"
            "<p>2026</p>"
        )
    
    def show_task(self):
        """Постановка задачи"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Постановка задачи")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        text = QTextBrowser()
        text.setHtml('<h1>Лабораторная работа №3</h1><p>Синтаксический анализ объявлений double с числами в научной нотации Java. Пример: double x = 1.23e+4;</p><p>Пуск → Синтаксический анализ: лексический анализ, разбор и нейтрализация ошибок методом Айронса. Таблица показывает фрагменты, позиции и описания; щелчок перемещает курсор.</p>')

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
        text.setHtml("<h1>Грамматика ЛР3</h1><pre>" + escape(SYNTAX_GRAMMAR) + "</pre>")

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
        text.setHtml('<h1>Классификация грамматики</h1><p>Представленная грамматика — контекстно-свободная (тип 2): слева стоит один нетерминал. Она LL(1), разбор выполняется за O(n). Язык этого ограниченного варианта также регулярен и допускает эквивалентную грамматику типа 3; вложенных выражений нет.</p>')

        layout.addWidget(text)
        
        btn = QPushButton("Закрыть")
        btn.clicked.connect(dialog.close)
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec()