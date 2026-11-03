"""Regression checks for case generation, movement, and turn rules."""

import random
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from board import board_html
from constants import GLYPHS, MOVEMENT_POINTS, QUEENS, SUSPECTS
from game import (
    ALL_SQUARES,
    adjacent,
    advance_turn,
    generate_case,
    interrogation_choices,
    legal_move,
    path,
    shortest_distances,
    skip_turn,
)


class GameTests(unittest.TestCase):
    def test_interrogation_range(self):
        for destination in ("D4", "C3", "D3", "E3", "C4", "E4", "C5", "D5", "E5"):
            self.assertTrue(adjacent("D4", destination))
        self.assertFalse(adjacent("D4", "D6"))

    def test_generation_invariants(self):
        with patch('game.random', random.Random(42)):
            for _ in range(250):
                game = generate_case()
                start = game['queens'][QUEENS[0]]
                self.assertEqual(start, game['queens'][QUEENS[1]])
                self.assertNotIn(start, [h[3] for h in game['histories'].values()])
                self.assertNotEqual(start, game['murder'])
                candidates = [n for n in SUSPECTS if legal_move(n, game['histories'][n][1], game['murder'])]
                self.assertEqual(candidates, [game['culprit']])
                self.assertEqual(game['points'], dict.fromkeys(QUEENS, 10))
                self.assertEqual(game['skipped'], dict.fromkeys(QUEENS, False))
                for stage in range(4):
                    self.assertEqual(len({h[stage] for h in game['histories'].values()}), 6)
                for name, history in game['histories'].items():
                    self.assertEqual(history[0] == game['murder'], name == game['culprit'])
                    for start, end in zip(history, history[1:]):
                        self.assertTrue(legal_move(name, start, end))

    def test_unblocked_routes_cost_one_per_square(self):
        costs = shortest_distances('A1', set())
        self.assertEqual(costs['A1'], 0)
        self.assertEqual(costs['H8'], 7)
        self.assertEqual(costs['D2'], 3)

    def test_detour_around_blocked_direct_path(self):
        wall = {f'C{rank}' for rank in range(1, 8)}
        costs = shortest_distances('A1', wall)
        self.assertEqual(costs['E1'], 14)
        self.assertNotIn('C1', costs)
        self.assertIsNone(path('A1', 'D2', QUEENS[0]))
        self.assertEqual(shortest_distances('A1', set())['D2'], 3)

    def test_occupied_destination_cannot_be_used_as_a_shortcut(self):
        wall = {f'B{rank}' for rank in range(1, 9)}
        costs = shortest_distances('A1', wall, {'B1'})
        self.assertEqual(costs['B1'], 1)
        self.assertNotIn('C1', costs)
        self.assertNotIn('B2', costs)

    def test_same_square_interrogation_and_shared_start(self):
        game = generate_case()
        queen = QUEENS[0]
        suspect = SUSPECTS[0]
        target = game['histories'][suspect][3]
        game['queens'] = dict.fromkeys(QUEENS, target)
        game['points'][queen] = 0
        self.assertEqual(interrogation_choices(game, queen, suspect), [(target, 0)])
        game['queens'][queen] = 'A1'
        game['histories'][suspect][3] = 'A2'
        game['queens'][QUEENS[1]] = 'A1'
        game['points'][queen] = 1
        self.assertIn(('A2', 1), interrogation_choices(game, queen, suspect))
        game['revealed'][suspect] = 3
        self.assertEqual(interrogation_choices(game, queen, suspect), [])

    def test_interrogation_choices_respect_shortest_cost_and_budget(self):
        game = generate_case()
        game['queens'] = dict.fromkeys(QUEENS, 'A1')
        for name in SUSPECTS:
            game['histories'][name][3] = 'H8'
        game['histories'][SUSPECTS[0]][3] = 'E1'
        game['histories'][SUSPECTS[1]][3] = 'B1'
        game['histories'][SUSPECTS[2]][3] = 'B2'
        game['points'][QUEENS[0]] = 4
        self.assertNotIn(('E1', 4), interrogation_choices(game, QUEENS[0], SUSPECTS[0]))
        game['points'][QUEENS[0]] = 5
        self.assertIn(('E1', 5), interrogation_choices(game, QUEENS[0], SUSPECTS[0]))

    def test_skip_limit_survives_round_reset(self):
        game = generate_case()
        self.assertFalse(skip_turn(game, QUEENS[1]))
        self.assertTrue(skip_turn(game, QUEENS[0]))
        self.assertTrue(skip_turn(game, QUEENS[1]))
        previous_turn = game['turn_number']
        self.assertFalse(skip_turn(game, QUEENS[0]))
        self.assertEqual(game['turn_number'], previous_turn)
        game['waiting'] = dict.fromkeys(QUEENS, True)
        game['points'] = dict.fromkeys(QUEENS, 0)
        advance_turn(game)
        self.assertEqual(game['points'], dict.fromkeys(QUEENS, MOVEMENT_POINTS))
        self.assertEqual(game['skipped'], dict.fromkeys(QUEENS, True))
        self.assertEqual(game['round'], 2)
        self.assertIn('10 new movement points', game['log'][-1])

    def test_shared_square_renders_every_piece_at_a_distinct_position(self):
        for names in (QUEENS, [*QUEENS, SUSPECTS[0]], list(GLYPHS)):
            html = board_html(dict.fromkeys(names, 'D4'), 'A1')
            svg = ElementTree.fromstring(html[html.index('<svg'):html.index('</svg>') + 6])
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            pieces = [node for node in svg.findall('svg:text', ns) if node.find('svg:title', ns) is not None]
            self.assertEqual(len(pieces), len(names))
            self.assertEqual(len({(p.get('x'), p.get('y')) for p in pieces}), len(names))
            self.assertEqual({p.find('svg:title', ns).text for p in pieces}, set(names))
            for piece in pieces:
                x, y = float(piece.get('x')), float(piece.get('y'))
                self.assertTrue(28 + 3*62 < x < 28 + 4*62)
                self.assertTrue(12 + 4*62 < y < 12 + 5*62)


if __name__ == '__main__':
    unittest.main()
