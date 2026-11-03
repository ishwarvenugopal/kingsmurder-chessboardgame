"""Streamlit interaction checks for the updated rules."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from constants import QUEENS, RULES_VERSION, SUSPECTS


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        self.assertFalse(self.app.exception)

    def button(self, label):
        return next(button for button in self.app.button if button.label == label)

    def test_initial_display_and_skip_limit(self):
        self.assertTrue(all(metric.value == '10 / 10' for metric in self.app.metric[-2:]))
        for _ in QUEENS:
            self.app.radio[0].set_value('Skip turn').run()
            self.button('Skip interrogation').click().run()
        self.assertTrue(self.button('Skip interrogation').disabled)
        self.assertEqual(self.app.session_state.game['turn_number'], 3)
        self.assertTrue(self.app.warning)
        self.assertFalse(self.app.exception)

    def test_same_square_interrogation_and_rewind(self):
        game = self.app.session_state.game
        suspect = SUSPECTS[0]
        target = game['histories'][suspect][3]
        game['queens'] = dict.fromkeys(QUEENS, target)
        self.app.run()
        self.app.selectbox[0].select_index(0).run()
        self.assertIn(f'{target} · 0 points', self.app.selectbox[1].options)
        self.app.selectbox[1].set_value(f'{target} · 0 points').run()
        self.button('Move and reveal one historical move').click().run()
        self.assertEqual(game['revealed'][suspect], 1)
        self.assertEqual(game['points'][QUEENS[0]], 10)
        self.assertEqual(game['turn'], 1)
        self.assertEqual(len(self.app.get('iframe')), 2)
        self.assertFalse(self.app.exception)

    def test_round_refresh_and_new_mystery(self):
        for _ in QUEENS:
            self.app.radio[0].set_value('End my movement round').run()
            self.button('Finish my round').click().run()
        game = self.app.session_state.game
        self.assertEqual(game['round'], 2)
        self.assertEqual(game['points'], dict.fromkeys(QUEENS, 10))
        self.button('🎲 Generate new mystery').click().run()
        self.assertEqual(self.app.session_state.game['round'], 1)
        self.assertEqual(self.app.session_state.game['skipped'], dict.fromkeys(QUEENS, False))
        self.assertFalse(self.app.exception)

    def test_old_session_is_replaced_with_current_rules(self):
        del self.app.session_state.game['rules_version']
        self.app.run()
        self.assertEqual(self.app.session_state.game['rules_version'], RULES_VERSION)
        self.assertFalse(self.app.exception)


if __name__ == '__main__':
    unittest.main()
