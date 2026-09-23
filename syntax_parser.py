"""Рекурсивный спуск для объявлений double с научным литералом.

Восстановление Айронса: пропуск входа до FIRST текущего или FOLLOW
завершаемого нетерминала; исходный текст не изменяется.
"""
from dataclasses import dataclass


@dataclass
class SyntaxError:
    fragment: str
    line: int
    col: int
    description: str


class Parser:
    def __init__(self, tokens, text=None):
        self.tokens = tokens
        self.text = text
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
        boundary = lambda t: t.lexeme in (';', 'double')
        number = lambda t: t.type in ('INTEGER', 'FLOAT', 'SCIENTIFIC', 'UNKNOWN')
        self.expect(lambda t: t.lexeme == 'double', "Ожидалось ключевое слово double",
                    lambda t: t.type == 'IDENTIFIER' or t.lexeme in ('=', '+', '-', ';') or number(t))
        self.expect(lambda t: t.type == 'IDENTIFIER', "Ожидался идентификатор",
                    lambda t: boundary(t) or t.lexeme in ('=', '+', '-') or number(t))
        self.expect(lambda t: t.lexeme == '=', "Ожидался знак =",
                    lambda t: boundary(t) or t.lexeme in ('+', '-') or number(t))
        if self.current_token() and self.current_token().lexeme in ('+', '-'):
            self.pos += 1
        token = self.expect(number, "Ожидалось число в научной нотации", boundary)
        if token and token.type != 'UNKNOWN' and token.type != 'SCIENTIFIC':
            self.add_error("Ожидалась экспонента e/E и целый показатель степени", token)
        self.expect(lambda t: t.lexeme == ';', "Ожидалась точка с запятой ;",
                    lambda t: t.lexeme == 'double' or t.type == 'IDENTIFIER')
