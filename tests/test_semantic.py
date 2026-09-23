import json
import math
import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from text_editor.compiler.scanner import Scanner
from text_editor.compiler.syntax_parser import Parser
from text_editor.compiler.semantic_analyzer import SemanticAnalyzer, SymbolTable, analyze_text


class SemanticTests(unittest.TestCase):
    def test_ast_structure_and_values(self):
        result = analyze_text('double x = 1.23e+4; double y = -x;')
        self.assertEqual(result.errors, [])
        tree = json.loads(result.ast.to_json())
        self.assertEqual(tree['node'], 'ProgramNode')
        x, y = result.ast.children
        self.assertEqual([n.kind for n in x.children], ['TypeNode', 'ScientificLiteralNode'])
        self.assertEqual((x.line, x.col), (1, 8))
        self.assertEqual(x.attributes['value'], 12300.0)
        self.assertEqual(y.children[1].kind, 'UnaryOpNode')
        self.assertEqual(y.children[1].children[0].attributes['name'], 'x')
        self.assertEqual(result.symbols.lookup('y').value, -12300.0)

    def test_duplicate_preserves_first(self):
        result = analyze_text('double x=1e2;\ndouble x=2e2;\ndouble y=x;')
        self.assertEqual(len(result.semantic_errors), 1)
        self.assertEqual((result.errors[0].line, result.errors[0].col), (2, 8))
        self.assertIn('строка 1', result.errors[0].description)
        self.assertEqual([n.attributes['name'] for n in result.ast.children], ['x', 'y'])
        self.assertEqual(result.symbols.lookup('y').value, 100)

    def test_type_mismatch(self):
        for literal, type_name in (('"1e2"', 'String'), ('true', 'boolean'), ('false', 'boolean')):
            with self.subTest(literal=literal):
                result = analyze_text('double x = ' + literal + ';')
                self.assertEqual(result.syntax_errors, [])
                self.assertEqual(len(result.semantic_errors), 1)
                self.assertIn(type_name, result.errors[0].description)
                self.assertEqual(result.errors[0].col, 12)
                self.assertEqual(result.errors[0].fragment, literal)
                self.assertEqual(result.ast.children, [])

    def test_unary_type_mismatch(self):
        result = analyze_text('double x=-true;')
        self.assertEqual(len(result.semantic_errors), 1)
        self.assertIn('неприменим', result.errors[0].description)

    def test_out_of_range(self):
        for literal in ('1e309', '-1e309', '1e-324', '-1e-9999', '1e9999999999999999999999999'):
            with self.subTest(literal=literal):
                result = analyze_text('double x=' + literal + '; double y=2e2;')
                self.assertEqual(len(result.semantic_errors), 1)
                self.assertIn('диапазон', result.errors[0].description)
                self.assertEqual([n.attributes['name'] for n in result.ast.children], ['y'])

    def test_double_boundary_rounding_and_zero(self):
        for literal in ('1.7976931348623157e308', '1.7976931348623158e308',
                        '4.9e-324', '3e-324', '0e-99999999', '0e99999999', '-0e0'):
            with self.subTest(literal=literal):
                result = analyze_text('double x=' + literal + ';')
                self.assertEqual(result.errors, [])
                self.assertTrue(math.isfinite(result.symbols.lookup('x').value))
        value = analyze_text('double x=-0e0;').symbols.lookup('x').value
        self.assertEqual(math.copysign(1, value), -1)

    def test_undeclared_forward_and_self_reference(self):
        for text in ('double x=missing;', 'double x=y; double y=1e2;', 'double x=x;'):
            with self.subTest(text=text):
                result = analyze_text(text)
                self.assertEqual(len(result.semantic_errors), 1)
                self.assertIn('не объявлен ранее', result.errors[0].description)

    def test_invalid_declaration_not_registered(self):
        result = analyze_text('double x=true; double y=x; double x=1e2;')
        self.assertEqual(len(result.semantic_errors), 2)
        self.assertEqual([n.attributes['name'] for n in result.ast.children], ['x'])

    def test_mixed_errors_and_recovery(self):
        result = analyze_text('double a=1e+; double b 1e2; double c=q; double d=1e2;')
        self.assertEqual(len(result.lexical_errors), 1)
        self.assertEqual(len(result.syntax_errors), 1)
        self.assertEqual(len(result.semantic_errors), 1)
        self.assertEqual([n.attributes['name'] for n in result.ast.children], ['d'])
        self.assertEqual([e.col for e in result.errors], sorted(e.col for e in result.errors))

    def test_empty_and_repeat(self):
        result = analyze_text('')
        self.assertEqual(len(result.syntax_errors), 1)
        self.assertEqual(result.ast.children, [])
        tokens, _ = Scanner().scan('double x=1e2;')
        parser = Parser(tokens, semantic=True)
        analyzer = SemanticAnalyzer()
        for _ in range(2):
            self.assertTrue(parser.parse_program())
            self.assertEqual(len(analyzer.analyze(parser.ast).children), 1)
            self.assertEqual(analyzer.errors, [])

    def test_strict_lab3_and_extended_lab5(self):
        tokens, _ = Scanner().scan('double x=1e2; double y=x;')
        self.assertFalse(Parser(tokens).parse_program())
        self.assertTrue(Parser(tokens, semantic=True).parse_program())

    def test_symbol_table(self):
        table = SymbolTable()
        self.assertTrue(table.declare('x', 'double', 1.0, 1, 8))
        self.assertFalse(table.declare('x', 'double', 2.0, 2, 8))
        self.assertTrue(table.check_duplicate('x'))
        self.assertEqual(table.lookup('x').value, 1.0)
        self.assertIsNone(table.lookup('missing'))


class SemanticInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_ast_errors_navigation_clear_and_modes(self):
        from text_editor.ui.editor import TextEditor
        w = TextEditor()
        try:
            w.editor.setPlainText('double x=1e2;\ndouble x=2e2;')
            w.semantic_action.trigger()
            self.assertEqual(w.result_table.rowCount(), 1)
            self.assertFalse(w.ast_panel.isHidden())
            self.assertEqual(len(json.loads(w.ast_view.toPlainText())['children']), 1)
            w.on_table_item_clicked(w.result_table.item(0, 2))
            cursor = w.editor.textCursor()
            self.assertEqual((cursor.blockNumber(), cursor.positionInBlock()), (1, 7))
            w.editor.setPlainText('double z=2e3;')
            self.assertEqual(w.ast_view.toPlainText(), '')
            self.assertEqual(w.result_table.rowCount(), 0)
            w.run_semantic_analyzer()
            self.assertIn('Ошибок нет', w.analysis_status.text())
            w.run_regex_search()
            self.assertTrue(w.ast_panel.isHidden())
            self.assertEqual(w.ast_view.toPlainText(), '')
            w.run_syntax_analyzer()
            self.assertEqual(w.result_table.rowCount(), 0)
            w.editor.clear()
            w.run_semantic_analyzer()
            self.assertEqual(w.result_table.rowCount(), 1)
            self.assertEqual(json.loads(w.ast_view.toPlainText())['children'], [])
        finally:
            w.is_modified = False
            w.close()


if __name__ == '__main__':
    unittest.main()
