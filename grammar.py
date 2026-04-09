# ========== КЛЮЧЕВЫЕ СЛОВА JAVA ==========
KEYWORDS = {
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
    'char', 'class', 'const', 'continue', 'default', 'do', 'double',
    'else', 'enum', 'extends', 'final', 'finally', 'float', 'for',
    'goto', 'if', 'implements', 'import', 'instanceof', 'int',
    'interface', 'long', 'native', 'new', 'package', 'private',
    'protected', 'public', 'return', 'short', 'static', 'strictfp',
    'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
    'transient', 'try', 'void', 'volatile', 'while'
}

# ========== ОПЕРАТОРЫ ==========
OPERATORS = {
    '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
    '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '>>>', '+=',
    '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '>>>=',
    '++', '--'
}

# ========== РАЗДЕЛИТЕЛИ ==========
DELIMITERS = {
    '(', ')', '{', '}', '[', ']', ';', ',', '.', '@', '::'
}

# ========== ТИПЫ ЛЕКСЕМ ==========
TOKEN_TYPES = {
    'KEYWORD':      1,
    'IDENTIFIER':   2,
    'INTEGER':      3,
    'FLOAT':        4,
    'SCIENTIFIC':   5,      # Числа в научной нотации (с e/E)
    'STRING':       6,
    'CHAR':         7,
    'OPERATOR':     8,
    'DELIMITER':    9,
    'COMMENT':      10,
    'WHITESPACE':   11,
    'UNKNOWN':      99
}

# Обратное отображение
TOKEN_NAMES = {v: k for k, v in TOKEN_TYPES.items()}

# ========== РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ ДЛЯ ЧИСЕЛ (НАУЧНАЯ НОТАЦИЯ) ==========
SCIENTIFIC_PATTERN = r'\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)\b|\b\.\d+(?:[eE][+-]?\d+)\b'

# Вещественные числа
FLOAT_PATTERN = r'\b\d+\.\d*\b|\b\.\d+\b'

# Целые числа (десятичные)
INTEGER_PATTERN = r'\b\d+\b'

# Шестнадцатеричные числа (Java-style)
HEX_PATTERN = r'\b0[xX][0-9a-fA-F]+\b'

# Двоичные числа (Java-style)
BINARY_PATTERN = r'\b0[bB][01]+\b'

# Восьмеричные числа (Java-style)
OCTAL_PATTERN = r'\b0[0-7]+\b'

# Строковые литералы
STRING_PATTERN = r'"(?:\\.|[^"\\])*"'

# Символьные литералы
CHAR_PATTERN = r"'(?:\\.|[^'\\])'"

# Идентификаторы
IDENTIFIER_PATTERN = r'[a-zA-Z_][a-zA-Z0-9_]*'

# Комментарии
COMMENT_PATTERN = r'//[^\n]*|/\*.*?\*/'