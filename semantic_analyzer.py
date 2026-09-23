"""ЛР5: таблица символов одной области видимости и проверка AST."""
from dataclasses import dataclass
import math
import re
from ast_nodes import ProgramNode
from scanner import Scanner
from syntax_parser import Parser, SyntaxError


@dataclass(frozen=True)
class Symbol:
    name: str
    type: str
    value: float
    line: int
    col: int


class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def lookup(self, name):
        return self.symbols.get(name)

    def check_duplicate(self, name):
        return name in self.symbols

    def declare(self, name, type_name, value, line, col):
        if self.check_duplicate(name):
            return False
        self.symbols[name] = Symbol(name, type_name, value, line, col)
        return True


@dataclass
class AnalysisResult:
    ast: ProgramNode
    lexical_errors: list
    syntax_errors: list
    semantic_errors: list
    symbols: SymbolTable

    @property
    def errors(self):
        return sorted(self.lexical_errors + self.syntax_errors + self.semantic_errors,
                      key=lambda error: (error.line, error.col))


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.errors = []

    def report(self, node, message):
        fragment = node.attributes.get('lexeme', node.attributes.get('name',
                   node.attributes.get('operator', str(node.attributes.get('value', '')))))
        self.errors.append(SyntaxError(fragment, node.line, node.col, message))

    def evaluate(self, node):
        if node.kind == 'ScientificLiteralNode':
            lexeme = node.attributes['lexeme']
            try:
                value = float(lexeme)
            except (ValueError, OverflowError):
                self.report(node, 'Значение не представимо в типе double')
                return None
            if not math.isfinite(value):
                self.report(node, 'Выход за диапазон double: переполнение до бесконечности')
                return None
            mantissa = re.split('[eE]', lexeme, maxsplit=1)[0]
            if value == 0.0 and any(ch in '123456789' for ch in mantissa):
                self.report(node, 'Выход за диапазон double: ненулевой литерал округляется до нуля')
                return None
            node.attributes['value'] = value
            return 'double', value
        if node.kind == 'IdentifierNode':
            symbol = self.symbols.lookup(node.attributes['name'])
            if symbol is None:
                self.report(node, f"Идентификатор {node.attributes['name']!r} не объявлен ранее")
                return None
            node.attributes.update(type=symbol.type, value=symbol.value)
            return symbol.type, symbol.value
        if node.kind == 'StringLiteralNode':
            return 'String', node.attributes['lexeme']
        if node.kind == 'BooleanLiteralNode':
            return 'boolean', node.attributes['value']
        if node.kind == 'UnaryOpNode':
            operand = self.evaluate(node.children[0])
            if operand is None:
                return None
            type_name, value = operand
            if type_name != 'double':
                self.report(node, f"Унарный оператор {node.attributes['operator']} неприменим к типу {type_name}")
                return None
            value = -value if node.attributes['operator'] == '-' else value
            node.attributes.update(type='double', value=value)
            return 'double', value
        raise ValueError(f'Неизвестный тип узла: {node.kind}')

    def analyze(self, parsed_ast):
        self.symbols = SymbolTable()
        self.errors = []
        result = ProgramNode()
        for declaration in parsed_ast.children:
            name = declaration.attributes['name']
            previous = self.symbols.lookup(name)
            if previous:
                self.report(declaration, f"Идентификатор {name!r} уже объявлен ранее (строка {previous.line}, символ {previous.col})")
                continue
            initializer = declaration.children[1]
            evaluated = self.evaluate(initializer)
            if evaluated is None:
                continue
            type_name, value = evaluated
            expected = declaration.attributes['type']
            if type_name != expected:
                self.report(initializer, f'Несовместимые типы: ожидался {expected}, получен {type_name}')
                continue
            self.symbols.declare(name, expected, value, declaration.line, declaration.col)
            declaration.attributes['value'] = value
            result.children.append(declaration)
        return result


def analyze_text(text):
    tokens, lexical = Scanner().scan(text)
    parser = Parser(tokens, text, semantic=True)
    parser.parse_program()
    analyzer = SemanticAnalyzer()
    ast = analyzer.analyze(parser.ast)
    lexical_errors = [SyntaxError(e.character, e.line, e.col, 'Лексическая ошибка: ' + e.message)
                      for e in lexical]
    syntax_errors = [SyntaxError(e.fragment, e.line, e.col, 'Синтаксическая ошибка: ' + e.description)
                     for e in parser.errors]
    semantic_errors = [SyntaxError(e.fragment, e.line, e.col, 'Семантическая ошибка: ' + e.description)
                       for e in analyzer.errors]
    return AnalysisResult(ast, lexical_errors, syntax_errors, semantic_errors, analyzer.symbols)
