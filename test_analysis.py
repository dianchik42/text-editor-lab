import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from scanner import Scanner
from syntax_parser import Parser


def analyze(text):
    tokens, lexical = Scanner().scan(text)
    parser = Parser(tokens, text)
    success = parser.parse_program()
    return success, lexical, parser.errors


class AnalysisTests(unittest.TestCase):
    def test_valid(self):
        for text in ("double x = 1.23e+4;", "double y = -6E-8;", "double z = +.5e2;",
                     "double x=1.e0;\ndouble y=0E0;", "double x=1e2; double y=2e3;"):
            with self.subTest(text=text):
                self.assertEqual(analyze(text), (True, [], []))

    def test_single_error(self):
        success, lex, errors = analyze("double x = 1.23;")
        self.assertFalse(success)
        self.assertEqual(len(errors), 1)
        self.assertEqual((errors[0].fragment, errors[0].col), ("1.23", 12))

    def test_missing_keyword(self):
        _, _, errors = analyze("x = 1e2;")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].col, 1)

    def test_empty(self):
        for text, position in (("", (1, 1)), (" \n  ", (2, 3))):
            _, _, errors = analyze(text)
            self.assertEqual(len(errors), 1)
            self.assertEqual((errors[0].line, errors[0].col), position)

    def test_eof_position(self):
        _, _, errors = analyze("double x=1e2\n  ")
        self.assertEqual((errors[0].line, errors[0].col), (2, 3))

    def test_recovery_multiple(self):
        _, _, errors = analyze("double = 1e2;\ndouble y 2e3;\ndouble z=3e4;")
        self.assertEqual([(e.line, e.col) for e in errors], [(1, 8), (2, 10)])

    def test_recovery_next_declaration(self):
        _, _, errors = analyze("double x=1e2 double y=2; double z=3e4;")
        self.assertEqual(len(errors), 2)

    def test_lexical_recovery(self):
        _, lex, errors = analyze("double x=1e+; double y=2; double z=3e4;")
        self.assertEqual(len(lex), 1)
        self.assertEqual(len(errors), 1)

    def test_scanner_positions_and_reuse(self):
        scanner = Scanner()
        tokens, errors = scanner.scan('a; "x" + .5e2;')
        self.assertFalse(errors)
        self.assertEqual([(t.lexeme, t.start) for t in tokens],
                         [('a', 1), (';', 2), ('"x"', 4), ('+', 8), ('.5e2', 10), (';', 14)])
        for text in ('1e', '1e+', '"abc', "'a"):
            self.assertEqual(len(scanner.scan(text)[1]), 1)
        self.assertEqual(scanner.scan('double x=1e2;')[1], [])

    def test_unexpected_tokens_terminate(self):
        for text in (';;;', '{}', 'double', '= = =', 'double x=1e2+3;', 'double x=1e2; if'):
            self.assertFalse(analyze(text)[0])


class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_analysis_switch_navigation_and_clear(self):
        from editor import TextEditor
        window = TextEditor()
        window.editor.setPlainText('double x=1e2;\n' + ' ' * 180 + 'double y=2;')
        window.run_syntax_analyzer()
        self.assertEqual(window.result_table.rowCount(), 1)
        window.on_table_item_clicked(window.result_table.item(0, 2))
        cursor = window.editor.textCursor()
        self.assertEqual((cursor.blockNumber(), cursor.positionInBlock()), (1, 189))
        window.run_analyzer()
        self.assertEqual(window.result_table.columnCount(), 4)
        window.editor.clear()
        window.run_syntax_analyzer()
        self.assertEqual(window.result_table.columnCount(), 3)
        self.assertEqual(window.result_table.rowCount(), 1)
        window.editor.setPlainText('double x=1e2;')
        window.run_syntax_analyzer()
        self.assertEqual(window.result_table.rowCount(), 0)
        self.assertIn('ошибок нет', window.analysis_status.text())
        window.is_modified = False
        window.close()


if __name__ == '__main__':
    unittest.main()
