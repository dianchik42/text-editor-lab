"""ЛР4: поиск подстрок стандартным модулем re, позиции от единицы."""
from bisect import bisect_right
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SearchRule:
    title: str
    pattern: str
    description: str


RULES = (
    SearchRule("I — HEX-цвет (6 цифр)",
               r"(?<![\w#])#?[0-9A-Fa-f]{6}(?!\w)",
               "Шесть HEX-цифр, необязательный #; без вхождения внутрь слова."),
    SearchRule("II — Юзернейм (8–16 знаков)",
               r"(?<![\w-])[a-z0-9_-]{8,16}(?![\w-])",
               "От 8 до 16 строчных латинских букв, цифр, дефисов или подчёркиваний."),
    SearchRule("III — Надёжный пароль (от 14 знаков)",
               r"(?<!\S)(?=\S*[А-ЯЁ])(?=\S*[а-яё])(?=\S*[0-9])"
               r"(?=\S*[()#?!|/@$%\\^&*_-])\S{14,}(?!\S)",
               "Пароли разделяются пробельными символами; нужны русские буквы обоих регистров, цифра и спецсимвол."),
)
COMPILED_RULES = tuple(re.compile(rule.pattern) for rule in RULES)


@dataclass(frozen=True)
class SearchMatch:
    fragment: str
    start: int
    line: int
    column: int
    length: int


def find_matches(text, rule_index):
    """Неперекрывающиеся совпадения; start — индекс Python, не позиция Qt."""
    pattern = COMPILED_RULES[rule_index]
    line_starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == '\n']
    results = []
    for match in pattern.finditer(text):
        line = bisect_right(line_starts, match.start())
        results.append(SearchMatch(match.group(), match.start(), line,
                                   match.start() - line_starts[line - 1] + 1,
                                   match.end() - match.start()))
    return results
