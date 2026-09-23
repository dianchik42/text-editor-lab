"""Рекурсивный спуск для объявлений double с научным литералом.

Восстановление Айронса: пропуск входа до FIRST текущего или FOLLOW
завершаемого нетерминала; исходный текст не изменяется.
"""
from dataclasses import dataclass
from text_editor.compiler.ast_nodes import ProgramNode, VariableDeclNode, make_expression


@dataclass
class SyntaxError:
    fragment: str
    line: int
    col: int
    description: str


class Parser:
    def __init__(self, tokens, text=None, semantic=False):
        self.tokens = tokens
        self.text = text
        self.semantic = semantic
        self.ast = ProgramNode()
        self.pos = 0
        self.errors = []

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def add_error(self, description, token=None):
        token = token or self.current_token()
        if token:
            self.errors.append(SyntaxError(token.lexeme, token.line, token.start, description))
        else:
            if self.text is not None:
                lines = self.text.split('\n')
                line, col = len(lines), len(lines[-1]) + 1
            elif self.tokens:
                line, col = self.tokens[-1].line, self.tokens[-1].end + 1
            else:
                line, col = 1, 1
            self.errors.append(SyntaxError('конец файла', line, col, description))

    def expect(self, predicate, description, follow):
        """FIRST — predicate, FOLLOW — follow; EOF всегда завершает поиск.

        FOLLOW сохраняется для вызывающего правила. При пропуске подряд
        идущих ошибочных токенов выдаётся одна диагностика для фрагмента.
        UNKNOWN уже диагностирован сканером и повторно не учитывается.
        """
        token = self.current_token()
        if token and predicate(token):
            self.pos += 1
            return token
        if token is None or token.type != 'UNKNOWN':
            self.add_error(description)
        while self.current_token():
            token = self.current_token()
            if predicate(token):
                self.pos += 1
                return token
            if follow(token):
                return None
            self.pos += 1
        return None

    def parse_program(self):
        self.ast = ProgramNode()
        self.pos = 0
        self.errors = []
        if not self.tokens:
            self.add_error("Ожидалось объявление double")
        while self.current_token():
            before = self.pos
            self.parse_statement()
            if self.pos == before:
                self.pos += 1  # Гарантия завершения даже на повреждённом входе.
        return not self.errors and not any(t.type == 'UNKNOWN' for t in self.tokens)

    def parse_statement(self):
        start, error_count = self.pos, len(self.errors)
        boundary = lambda t: t.lexeme in (';', 'double')
        number = lambda t: (t.type in ('INTEGER', 'FLOAT', 'SCIENTIFIC', 'UNKNOWN')
                            or (self.semantic and t.type in ('IDENTIFIER', 'STRING')))
        type_token = self.expect(lambda t: t.lexeme == 'double', "Ожидалось ключевое слово double",
                    lambda t: t.type == 'IDENTIFIER' or t.lexeme in ('=', '+', '-', ';') or number(t))
        name = self.expect(lambda t: t.type == 'IDENTIFIER' and t.lexeme not in ('true', 'false', 'null'),
                    "Ожидался идентификатор",
                    lambda t: boundary(t) or t.lexeme in ('=', '+', '-') or number(t))
        self.expect(lambda t: t.lexeme == '=', "Ожидался знак =",
                    lambda t: boundary(t) or t.lexeme in ('+', '-') or number(t))
        sign = None
        if self.current_token() and self.current_token().lexeme in ('+', '-'):
            sign = self.current_token()
            self.pos += 1
        token = self.expect(number, "Ожидалось значение" if self.semantic else "Ожидалось число в научной нотации", boundary)
        if token and token.type in ('INTEGER', 'FLOAT'):
            self.add_error("Ожидалась экспонента e/E и целый показатель степени", token)
        if token and self.semantic and token.lexeme == 'null':
            self.add_error("В этой грамматике null не поддерживается", token)
        self.expect(lambda t: t.lexeme == ';', "Ожидалась точка с запятой ;",
                    lambda t: t.lexeme == 'double' or t.type == 'IDENTIFIER')
        valid = (len(self.errors) == error_count and type_token and name and token
                 and not any(t.type == 'UNKNOWN' for t in self.tokens[start:self.pos]))
        if valid:
            self.ast.children.append(VariableDeclNode(name, type_token, make_expression(token, sign)))
