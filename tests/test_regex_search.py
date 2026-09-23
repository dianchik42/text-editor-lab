import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from text_editor.regex_search import find_matches


class RegexSearchTests(unittest.TestCase):
    def assert_cases(self, rule, valid, invalid):
        for value in valid:
            with self.subTest(rule=rule, valid=value):
                self.assertEqual([m.fragment for m in find_matches(value, rule)], [value])
        for value in invalid:
            with self.subTest(rule=rule, invalid=value):
                self.assertEqual(find_matches(value, rule), [])

    def test_hex(self):
        self.assert_cases(0, ['#A1b2C3', 'abcdef', '000000', '#FFFFFF'],
                          ['', '#12345', '#1234567', '#12345678', '1234567',
                           '#GG0000', 'wordABCDEF', 'ABCDEFword', 'яABCDEF', '##ABCDEF'])
        self.assertEqual([m.fragment for m in find_matches('(#ABCDEF), 123abc;', 0)],
                         ['#ABCDEF', '123abc'])

    def test_username(self):
        self.assert_cases(1, ['abcd1234', 'user_name-01', 'a' * 16, '12345678', 'a' * 8],
                          ['', 'a' * 7, 'a' * 17, 'Abcd1234', 'Яabcdefgh', 'abcdefghЯ',
                           'abcdefghZ', 'Zabcdefgh', 'abcdefgh-' + 'z' * 8])
        self.assertEqual([m.fragment for m in find_matches('(abcd1234), user_name-01', 1)],
                         ['abcd1234', 'user_name-01'])

    def test_password(self):
        self.assert_cases(2, ['Ая1!' + 'x' * 10, 'Ёё1_' + 'x' * 10,
                             'Ая1!' + 'x' * 100, 'ПарольНадежный1!'],
                          ['', 'Ая1!' + 'x' * 9, 'АА1!' + 'x' * 10,
                           'яя1!' + 'x' * 10, 'Аяa!' + 'x' * 10,
                           'Ая1a' + 'x' * 10, 'Aa1!' + 'x' * 10,
                           'Ая١!' + 'x' * 10, 'Ая1! xxx xxxxxxx'])

    def test_every_password_special(self):
        for special in '()#?!|/@$%\\^&*-_':
            with self.subTest(special=special):
                self.assertEqual(len(find_matches('Ая1' + special + 'x' * 10, 2)), 1)

    def test_password_no_cross_token_lookahead(self):
        self.assertEqual(find_matches('a' * 14 + ' Ая1!', 2), [])
        self.assertEqual(find_matches('А' * 14 + '\nя1!', 2), [])

    def test_positions_lengths_and_all_matches(self):
        text = '😀 #abcdef\n  #123456 #ffffff'
        matches = find_matches(text, 0)
        self.assertEqual([(m.line, m.column, m.length, m.start) for m in matches],
                         [(1, 3, 7, 2), (2, 3, 7, 12), (2, 11, 7, 20)])
        for m in matches:
            self.assertEqual(text[m.start:m.start + m.length], m.fragment)

    def test_empty_no_matches_and_repeated_runs(self):
        for rule in range(3):
            self.assertEqual(find_matches('', rule), [])
            self.assertEqual(find_matches(' \n\t', rule), [])
            self.assertEqual(find_matches('abc', rule), [])
        self.assertEqual(find_matches('#abcdef', 0), find_matches('#abcdef', 0))


class SearchInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from text_editor.ui.editor import TextEditor
        self.window = TextEditor()

    def tearDown(self):
        self.window.is_modified = False
        self.window.close()

    def test_selection_unicode_and_keyboard(self):
        w = self.window
        w.editor.setPlainText('😀 #abcdef\n#123456')
        w.search_action.trigger()
        self.assertEqual(w.result_table.rowCount(), 2)
        self.assertEqual(w.result_table.columnCount(), 3)
        w.result_table.selectRow(0)
        self.assertEqual(w.editor.textCursor().selectedText(), '#abcdef')
        self.assertEqual(len(w.editor.extraSelections()), 1)
        w.result_table.setCurrentCell(1, 2)
        self.assertEqual(w.editor.textCursor().selectedText(), '#123456')
        self.assertIn('2', w.analysis_status.text())

    def test_clear_edit_change_type_and_modes(self):
        w = self.window
        w.editor.setPlainText('#abcdef')
        w.run_regex_search()
        w.result_table.selectRow(0)
        w.search_type.setCurrentIndex(1)
        self.assertEqual(w.result_table.rowCount(), 0)
        self.assertEqual(w.editor.extraSelections(), [])
        w.editor.setPlainText('abcd1234')
        w.run_regex_search()
        self.assertEqual(w.result_table.rowCount(), 1)
        w.result_table.selectRow(0)
        w.editor.insertPlainText('x')
        self.assertEqual(w.result_table.rowCount(), 0)
        self.assertEqual(w.editor.extraSelections(), [])
        w.editor.clear()
        w.run_regex_search()
        self.assertEqual(w.analysis_status.text(), 'Нет данных для поиска')
        w.editor.setPlainText('double x=1e2;')
        w.run_syntax_analyzer()
        self.assertEqual(w.result_table.rowCount(), 0)
        w.run_analyzer()
        self.assertEqual(w.result_table.columnCount(), 4)
        w.run_regex_search()
        self.assertEqual(w.result_table.columnCount(), 3)
        self.assertEqual(w.result_table.rowCount(), 0)


if __name__ == '__main__':
    unittest.main()
