class SyntaxError:
    def __init__(self, fragment, line, col, description):
        self.fragment = fragment
        self.line = line
        self.col = col
        self.description = description


class _ScientificLexemeParser:
    """Внутренний класс для проверки лексемы научной нотации"""
    def __init__(self, lexeme, base_line, base_col):
        self.lexeme = lexeme
        self.pos = 0
        self.line = base_line
        self.col = base_col
        self.errors = []
        self.sync_mantissa = {'.', 'e', 'E', ''}
        self.sync_exponent = {'', ' '}

    def current_char(self):
        return self.lexeme[self.pos] if self.pos < len(self.lexeme) else ''

    def advance(self):
        self.pos += 1
        self.col += 1

    def add_error(self, fragment, description):
        self.errors.append(SyntaxError(fragment, self.line, self.col, description))

    def synchronize(self, sync_set):
        while self.current_char() and self.current_char() not in sync_set:
            self.advance()

    def parse_integer_part(self):
        if not self.current_char().isdigit():
            self.add_error(self.current_char() or "конец строки", "Ожидается цифра")
            return False
        while self.current_char().isdigit():
            self.advance()
        return True

    def parse_fraction_part(self):
        if self.current_char() != '.':
            self.add_error(self.current_char() or "конец строки", "Ожидается точка")
            return False
        self.advance()
        if not self.parse_integer_part():
            self.add_error(self.current_char() or "конец строки",
                           "После точки должна быть хотя бы одна цифра")
            return False
        return True

    def parse_mantissa(self):
        saved_pos, saved_col = self.pos, self.col
        if self.parse_integer_part():
            if self.current_char() == '.':
                self.parse_fraction_part()
            return True
        self.pos, self.col = saved_pos, saved_col
        if self.current_char() == '.' and self.parse_fraction_part():
            return True
        self.add_error(self.current_char() or "конец строки",
                       "Ожидается целое число или дробная часть")
        self.synchronize(self.sync_mantissa)
        return False

    def parse_exponent(self):
        ch = self.current_char().lower()
        if ch != 'e':
            self.add_error(self.current_char() or "конец строки", "Ожидается 'e' или 'E'")
            self.synchronize(self.sync_exponent)
            return False
        self.advance()
        if self.current_char() in '+-':
            self.advance()
        if not self.parse_integer_part():
            self.add_error(self.current_char() or "конец строки",
                           "Ожидается целое число экспоненты")
            self.synchronize(self.sync_exponent)
            return False
        return True

    def parse(self):
        if not self.parse_mantissa():
            return False
        if not self.parse_exponent():
            return False
        if self.current_char():
            self.add_error(self.current_char(), "Лишние символы после числа")
            return False
        return True


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek_token(self, offset=1):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def consume(self):
        tok = self.current_token()
        self.pos += 1
        return tok

    def match(self, expected_type, expected_lexeme=None):
        tok = self.current_token()
        if not tok:
            self.add_error("конец файла", f"Ожидается {expected_type}")
            return False
        if tok.type != expected_type:
            self.add_error(tok.lexeme, f"Ожидается {expected_type}, найдено {tok.type}")
            return False
        if expected_lexeme is not None and tok.lexeme != expected_lexeme:
            self.add_error(tok.lexeme, f"Ожидается '{expected_lexeme}', найдено '{tok.lexeme}'")
            return False
        self.consume()
        return True

    def add_error(self, fragment, description):
        tok = self.current_token()
        if tok:
            self.errors.append(SyntaxError(fragment, tok.line, tok.start, description))
        else:
            if self.tokens:
                last = self.tokens[-1]
                self.errors.append(SyntaxError(fragment, last.line, last.end + 1, description))

    def synchronize_statement_set(self):
        sync_set = {';', '}', 'if', 'while', '{', 'IDENTIFIER'}
        while self.current_token() and self.current_token().lexeme not in sync_set:
            self.consume()
        if self.current_token() and self.current_token().lexeme in (';', '}'):
            self.consume()

    def validate_scientific_token(self, token):
        parser = _ScientificLexemeParser(token.lexeme, token.line, token.start)
        parser.parse()
        for err in parser.errors:
            self.errors.append(err)

    def parse_program(self):
        while self.current_token():
            if not self.parse_statement():
                self.synchronize_statement_set()
        return len(self.errors) == 0

    def parse_statement(self):
        tok = self.current_token()
        if not tok:
            return True
        if tok.type == 'KEYWORD':
            if tok.lexeme == 'if':
                return self.parse_if_stmt()
            elif tok.lexeme == 'while':
                return self.parse_while_stmt()
            elif tok.lexeme == 'else':
                self.add_error(tok.lexeme, "Неожиданное 'else' без соответствующего 'if'")
                self.consume()
                return False
        if tok.type == 'IDENTIFIER':
            return self.parse_assignment_stmt()
        if tok.lexeme == '{':
            return self.parse_block()
        if tok.lexeme == ';':
            self.consume()
            return True
        self.add_error(tok.lexeme, "Ожидается начало оператора")
        return False

    def parse_assignment_stmt(self):
        if not self.match('IDENTIFIER'):
            return False
        if not self.match('OPERATOR', '='):
            return False
        if not self.parse_expression():
            return False
        if not self.match('DELIMITER', ';'):
            return False
        return True

    def parse_if_stmt(self):
        if not self.match('KEYWORD', 'if'):
            return False
        if not self.match('DELIMITER', '('):
            return False
        if not self.parse_expression():
            return False
        if not self.match('DELIMITER', ')'):
            return False
        if not self.parse_statement():
            return False
        if self.current_token() and self.current_token().lexeme == 'else':
            self.consume()
            if not self.parse_statement():
                return False
        return True

    def parse_while_stmt(self):
        if not self.match('KEYWORD', 'while'):
            return False
        if not self.match('DELIMITER', '('):
            return False
        if not self.parse_expression():
            return False
        if not self.match('DELIMITER', ')'):
            return False
        if not self.parse_statement():
            return False
        return True

    def parse_block(self):
        if not self.match('DELIMITER', '{'):
            return False
        while self.current_token() and self.current_token().lexeme != '}':
            if not self.parse_statement():
                self.synchronize_statement_set()
        if not self.match('DELIMITER', '}'):
            return False
        return True

    def parse_expression(self):
        if not self.parse_term():
            return False
        while self.current_token() and self.current_token().type == 'OPERATOR' and self.current_token().lexeme in ('+', '-'):
            self.consume()
            if not self.parse_term():
                return False
        return True

    def parse_term(self):
        if not self.parse_factor():
            return False
        while self.current_token() and self.current_token().type == 'OPERATOR' and self.current_token().lexeme in ('*', '/'):
            self.consume()
            if not self.parse_factor():
                return False
        return True

    def parse_factor(self):
        tok = self.current_token()
        if not tok:
            self.add_error("конец файла", "Ожидается выражение")
            return False
        if tok.type in ('INTEGER', 'FLOAT'):
            self.consume()
            return True
        if tok.type == 'SCIENTIFIC':
            self.validate_scientific_token(tok)
            self.consume()
            return True
        if tok.type == 'IDENTIFIER':
            self.consume()
            return True
        if tok.type == 'DELIMITER' and tok.lexeme == '(':
            self.consume()
            if not self.parse_expression():
                return False
            if not self.match('DELIMITER', ')'):
                return False
            return True
        self.add_error(tok.lexeme, "Ожидается число, идентификатор или (")
        return False