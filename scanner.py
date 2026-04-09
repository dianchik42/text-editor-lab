# scanner.py
import re
from grammar import (
    KEYWORDS, OPERATORS, DELIMITERS, TOKEN_TYPES,
    STRING_PATTERN, CHAR_PATTERN, IDENTIFIER_PATTERN
)


class Token:
    """Класс для хранения информации о лексеме"""
    def __init__(self, code, type_name, lexeme, line, start_col, end_col):
        self.code = code          # числовой код типа
        self.type = type_name     # строковое описание
        self.lexeme = lexeme      # сама лексема
        self.line = line          # номер строки (1-based)
        self.start = start_col    # начальная позиция в строке (1-based)
        self.end = end_col        # конечная позиция в строке (1-based)
    
    def __repr__(self):
        return f"Token({self.type}, '{self.lexeme}', line={self.line}, pos={self.start}-{self.end})"


class LexicalError:
    """Класс для хранения информации об ошибке"""
    def __init__(self, message, line, col, character):
        self.message = message
        self.line = line
        self.col = col
        self.character = character
    
    def __repr__(self):
        return f"Ошибка на строке {self.line}, позиция {self.col}: {self.message} ('{self.character}')"


class FiniteAutomaton:
    """
    Конечный автомат для распознавания чисел в научной нотации (Java-style)
    Диаграмма состояний:
    START → INTEGER → FLOAT → SCIENTIFIC → EXP_SIGN → SCIENTIFIC (цикл)
    """
    
    def __init__(self):
        # Состояния автомата
        self.START = 0
        self.IDENT = 1
        self.INTEGER = 2          # Целое число
        self.FLOAT = 3            # Вещественное число (с точкой)
        self.SCIENTIFIC = 4       # Научная нотация (после e/E)
        self.EXP_SIGN = 5         # Знак экспоненты (+/-)
        self.STRING = 6
        self.CHAR = 7
        self.OPERATOR = 8
        self.DELIMITER = 9
        self.UNKNOWN = 99
        
        self.state = self.START
        self.current_lexeme = []
        self.start_pos = 0
        self.has_dot = False      # Флаг: есть ли точка в числе
        self.has_exp = False      # Флаг: есть ли e/E в числе
        
    def reset(self):
        """Сброс автомата для новой лексемы"""
        self.state = self.START
        self.current_lexeme = []
        self.start_pos = 0
        self.has_dot = False
        self.has_exp = False
    
    def add_char(self, ch):
        """Добавить символ к текущей лексеме"""
        self.current_lexeme.append(ch)
    
    def get_lexeme(self):
        """Получить текущую лексему"""
        return ''.join(self.current_lexeme)
    
    def get_number_type(self):
        """Определить тип числа на основе флагов"""
        lexeme = self.get_lexeme()
        
        # Научная нотация (приоритет 1)
        if self.has_exp:
            return 'SCIENTIFIC'
        
        # Вещественное число (есть точка, приоритет 2)
        if self.has_dot:
            return 'FLOAT'
        
        # Целое число (приоритет 3)
        return 'INTEGER'
    
    def process_char(self, ch, line, col):
        """
        Обработать символ и вернуть (признак завершения лексемы, тип лексемы, лексема)
        """
        if self.state == self.START:
            self.start_pos = col
            self.add_char(ch)
            
            # Распознавание начала лексемы
            if ch.isalpha() or ch == '_':
                self.state = self.IDENT
                return (False, None, None)
            elif ch.isdigit():
                self.state = self.INTEGER
                return (False, None, None)
            elif ch == '.':
                self.state = self.FLOAT
                self.has_dot = True
                return (False, None, None)
            elif ch == '"':
                self.state = self.STRING
                return (False, None, None)
            elif ch == "'":
                self.state = self.CHAR
                return (False, None, None)
            elif ch in OPERATORS:
                self.state = self.OPERATOR
                return (False, None, None)
            elif ch in DELIMITERS:
                self.state = self.DELIMITER
                # Разделители — односимвольные лексемы
                return (True, 'DELIMITER', self.get_lexeme())
            elif ch.isspace():
                # Пропускаем пробельные символы
                self.reset()
                return (False, None, None)
            else:
                self.state = self.UNKNOWN
                return (False, None, None)
        
        # ========== ОБРАБОТКА IDENTIFIER ==========
        elif self.state == self.IDENT:
            if ch.isalnum() or ch == '_':
                self.add_char(ch)
                return (False, None, None)
            else:
                lexeme = self.get_lexeme()
                token_type = 'KEYWORD' if lexeme in KEYWORDS else 'IDENTIFIER'
                self.reset()
                return (True, token_type, lexeme)
        
        # ========== ОБРАБОТКА INTEGER (целое число) ==========
        elif self.state == self.INTEGER:
            if ch.isdigit():
                self.add_char(ch)
                return (False, None, None)
            elif ch == '.':
                self.add_char(ch)
                self.state = self.FLOAT
                self.has_dot = True
                return (False, None, None)
            elif ch.lower() == 'e':
                self.add_char(ch)
                self.state = self.SCIENTIFIC
                self.has_exp = True
                return (False, None, None)
            else:
                # Конец целого числа
                lexeme = self.get_lexeme()
                token_type = self.get_number_type()
                self.reset()
                # Возвращаемся на один символ назад (не потребляем текущий)
                return (True, token_type, lexeme)
        
        # ========== ОБРАБОТКА FLOAT (вещественное число) ==========
        elif self.state == self.FLOAT:
            if ch.isdigit():
                self.add_char(ch)
                return (False, None, None)
            elif ch.lower() == 'e':
                self.add_char(ch)
                self.state = self.SCIENTIFIC
                self.has_exp = True
                return (False, None, None)
            else:
                # Конец вещественного числа
                lexeme = self.get_lexeme()
                token_type = self.get_number_type()
                self.reset()
                return (True, token_type, lexeme)
        
        # ========== ОБРАБОТКА SCIENTIFIC (научная нотация после e/E) ==========
        elif self.state == self.SCIENTIFIC:
            if ch == '+' or ch == '-':
                self.add_char(ch)
                self.state = self.EXP_SIGN
                return (False, None, None)
            elif ch.isdigit():
                self.add_char(ch)
                # Остаемся в состоянии SCIENTIFIC
                return (False, None, None)
            else:
                # Конец научной нотации
                lexeme = self.get_lexeme()
                # Проверяем, что после e/E есть хотя бы одна цифра
                # Находим позицию e/E
                exp_pos = -1
                for i, c in enumerate(lexeme):
                    if c.lower() == 'e':
                        exp_pos = i
                        break
                
                # Проверяем, есть ли цифры после e/E
                has_exp_digits = False
                if exp_pos != -1 and exp_pos + 1 < len(lexeme):
                    # Пропускаем возможный знак
                    start = exp_pos + 1
                    if lexeme[start] in '+-':
                        start += 1
                    if start < len(lexeme) and any(c.isdigit() for c in lexeme[start:]):
                        has_exp_digits = True
                
                if has_exp_digits:
                    token_type = self.get_number_type()
                else:
                    token_type = 'UNKNOWN'
                
                self.reset()
                return (True, token_type, lexeme)
        
        # ========== ОБРАБОТКА EXP_SIGN (знак экспоненты) ==========
        elif self.state == self.EXP_SIGN:
            if ch.isdigit():
                self.add_char(ch)
                self.state = self.SCIENTIFIC
                return (False, None, None)
            else:
                # Незавершенная научная нотация (ошибка)
                lexeme = self.get_lexeme()
                self.reset()
                return (True, 'UNKNOWN', lexeme)
        
        # ========== ОБРАБОТКА STRING (строка) ==========
        elif self.state == self.STRING:
            self.add_char(ch)
            if ch == '"' and len(self.current_lexeme) > 1:
                lexeme = self.get_lexeme()
                self.reset()
                return (True, 'STRING', lexeme)
            return (False, None, None)
        
        # ========== ОБРАБОТКА CHAR (символ) ==========
        elif self.state == self.CHAR:
            self.add_char(ch)
            if ch == "'" and len(self.current_lexeme) > 1:
                lexeme = self.get_lexeme()
                self.reset()
                return (True, 'CHAR', lexeme)
            return (False, None, None)
        
        # ========== ОБРАБОТКА OPERATOR (оператор) ==========
        elif self.state == self.OPERATOR:
            current = self.get_lexeme()
            if ch != '' and (current + ch) in OPERATORS:
                self.add_char(ch)
                return (False, None, None)
            else:
                lexeme = self.get_lexeme()
                self.reset()
                return (True, 'OPERATOR', lexeme)
        
        # ========== ОБРАБОТКА UNKNOWN (неизвестный символ) ==========
        elif self.state == self.UNKNOWN:
            lexeme = self.get_lexeme()
            self.reset()
            return (True, 'UNKNOWN', lexeme)
        
        return (False, None, None)
    
    def finalize(self):
        """Завершить анализ (вызвать в конце строки)"""
        if self.state != self.START:
            lexeme = self.get_lexeme()
            token_type = 'UNKNOWN'
            
            if self.state == self.IDENT:
                token_type = 'KEYWORD' if lexeme in KEYWORDS else 'IDENTIFIER'
            elif self.state in [self.INTEGER, self.FLOAT, self.SCIENTIFIC, self.EXP_SIGN]:
                token_type = self.get_number_type()
                # Дополнительная проверка для научной нотации
                if token_type == 'SCIENTIFIC':
                    # Проверяем, что после e/E есть цифры
                    exp_pos = -1
                    for i, c in enumerate(lexeme):
                        if c.lower() == 'e':
                            exp_pos = i
                            break
                    if exp_pos != -1 and exp_pos + 1 < len(lexeme):
                        start = exp_pos + 1
                        if lexeme[start] in '+-':
                            start += 1
                        if start >= len(lexeme) or not any(c.isdigit() for c in lexeme[start:]):
                            token_type = 'UNKNOWN'
            elif self.state == self.STRING:
                token_type = 'STRING'
            elif self.state == self.CHAR:
                token_type = 'CHAR'
            elif self.state == self.OPERATOR:
                token_type = 'OPERATOR'
            elif self.state == self.DELIMITER:
                token_type = 'DELIMITER'
            
            self.reset()
            return (True, token_type, lexeme)
        
        return (False, None, None)


class Scanner:
    """Лексический анализатор"""
    
    def __init__(self):
        self.automaton = FiniteAutomaton()
        self.tokens = []
        self.errors = []
    
    def scan(self, text):
        """
        Анализирует текст и возвращает список токенов и ошибок
        """
        self.tokens = []
        self.errors = []
        
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            self._scan_line(line, line_num)
        
        return self.tokens, self.errors
    
    def _scan_line(self, line, line_num):
        """Анализирует одну строку"""
        i = 0
        length = len(line)
        
        while i < length:
            ch = line[i]
            col = i + 1
            
            # Пропускаем пробелы в начале
            if ch.isspace() and self.automaton.state == 0:
                i += 1
                continue
            
            # Обрабатываем символ автоматом
            is_complete, token_type, lexeme = self.automaton.process_char(ch, line_num, col)
            
            if is_complete:
                if token_type == 'UNKNOWN':
                    # Неизвестный символ — ошибка
                    start_col = col - len(lexeme)
                    error = LexicalError(
                        f"Недопустимый символ '{lexeme}'",
                        line_num, start_col, lexeme
                    )
                    self.errors.append(error)
                else:
                    # Создаем токен
                    start_col = col - len(lexeme)
                    token = Token(
                        code=TOKEN_TYPES.get(token_type, 99),
                        type_name=token_type,
                        lexeme=lexeme,
                        line=line_num,
                        start_col=start_col,
                        end_col=col - 1
                    )
                    self.tokens.append(token)
                
                # Не увеличиваем i, так как автомат мог не потребить символ
                # (например, при завершении лексемы текущий символ принадлежит следующей)
                if not is_complete:
                    i += 1
            else:
                i += 1
        
        # Завершаем обработку строки (если осталась незавершенная лексема)
        is_complete, token_type, lexeme = self.automaton.finalize()
        if is_complete:
            if token_type == 'UNKNOWN':
                error = LexicalError(
                    f"Недопустимый символ '{lexeme}'",
                    line_num, length - len(lexeme) + 1, lexeme
                )
                self.errors.append(error)
            else:
                start_col = length - len(lexeme) + 1
                token = Token(
                    code=TOKEN_TYPES.get(token_type, 99),
                    type_name=token_type,
                    lexeme=lexeme,
                    line=line_num,
                    start_col=start_col,
                    end_col=length
                )
                self.tokens.append(token)
    
    def get_tokens_table_data(self):
        """Возвращает данные для отображения в таблице"""
        data = []
        for token in self.tokens:
            data.append([
                token.code,
                token.type,
                token.lexeme,
                f"строка {token.line}, [{token.start}:{token.end}]"
            ])
        for error in self.errors:
            data.append([
                -1,
                "ОШИБКА",
                error.character,
                f"строка {error.line}, [{error.col}:{error.col}]"
            ])
        return data