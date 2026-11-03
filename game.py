"""Chess movement rules, case generation, and game state updates."""

import random
from collections import deque

from constants import FILES, MOVEMENT_POINTS, QUEENS, RULES_VERSION, SUSPECTS


def square(x, y):
    return f"{FILES[x]}{y + 1}"


def coords(s):
    return FILES.index(s[0]), int(s[1]) - 1


def legal_move(piece, a, b):
    x1, y1 = coords(a)
    x2, y2 = coords(b)
    dx, dy = abs(x2-x1), abs(y2-y1)
    if dx == dy == 0:
        return False
    if "Knight" in piece:
        return (dx, dy) in [(1, 2), (2, 1)]
    if "Bishop" in piece:
        return dx == dy
    if "Rook" in piece:
        return dx == 0 or dy == 0
    return dx == 0 or dy == 0 or dx == dy


def path(a, b, piece):
    if not legal_move(piece, a, b):
        return None
    x1, y1 = coords(a)
    x2, y2 = coords(b)
    if "Knight" in piece:
        return [b]
    sx = (x2 > x1) - (x2 < x1)
    sy = (y2 > y1) - (y2 < y1)
    out = []
    x, y = x1 + sx, y1 + sy
    while (x, y) != (x2, y2):
        out.append(square(x, y))
        x, y = x + sx, y + sy
    out.append(b)
    return out


def destinations(piece, start, occupied):
    return [end for end in ALL_SQUARES if end != start and (p := path(start, end, piece)) is not None and not any(s in occupied for s in p)]


def adjacent(a, b):
    """Interrogation range includes the same square and all eight neighbors."""
    x1, y1 = coords(a)
    x2, y2 = coords(b)
    return max(abs(x1-x2), abs(y1-y2)) <= 1


def distance(a, b):
    x1, y1 = coords(a)
    x2, y2 = coords(b)
    return max(abs(x1-x2), abs(y1-y2))


ALL_SQUARES = [square(x, y) for y in range(8) for x in range(8)]


def shortest_distances(start, occupied, allowed_destinations=()):
    """Find queen travel costs, allowing turns and charging one per square.

    A queen's route is a sequence of horizontal, vertical, or diagonal steps.
    Occupied squares block travel. Explicitly allowed occupied destinations can
    be reached, but cannot be traversed to reach another destination.
    """
    occupied = set(occupied)
    allowed_destinations = set(allowed_destinations)
    costs = {start: 0}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        x, y = coords(current)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (dx == dy == 0) or not (0 <= x + dx < 8 and 0 <= y + dy < 8):
                    continue
                destination = square(x + dx, y + dy)
                if destination in costs:
                    continue
                if destination in occupied and destination not in allowed_destinations:
                    continue
                costs[destination] = costs[current] + 1
                if destination not in occupied:
                    pending.append(destination)
    return costs


def interrogation_choices(game, queen, suspect):
    """Return reachable interrogation squares and their minimum point costs."""
    if game["revealed"][suspect] >= 3:
        return []
    target = position_of(game, suspect)
    occupied = {position_of(game, name) for name in SUSPECTS}
    occupied.update(pos for name, pos in game["queens"].items() if name != queen)
    costs = shortest_distances(game["queens"][queen], occupied, {target})
    return sorted(
        ((s, cost) for s, cost in costs.items()
         if adjacent(s, target) and cost <= game["points"][queen]),
        key=lambda choice: (choice[1], choice[0]),
    )


def skip_turn(game, queen):
    """Consume a player's single voluntary skip; reject repeated attempts."""
    if game["winner"] or queen != QUEENS[game["turn"]] or game["waiting"][queen]:
        return False
    if game["skipped"][queen]:
        return False
    game["skipped"][queen] = True
    record(game, f"{queen} skipped.")
    advance_turn(game)
    return True


def generate_case():
    # Generate all six trajectories together, ensuring that pieces never share a
    # square at any synchronized historical stage. The king's marker is evidence,
    # not a blocking chess piece during the suspects' historical movements.
    for _ in range(300):
        murder = random.choice(ALL_SQUARES)
        culprit = random.choice(SUSPECTS)
        initial = {culprit: murder}
        for name in random.sample([n for n in SUSPECTS if n != culprit], 5):
            choices = [s for s in ALL_SQUARES if s != murder and s not in initial.values()]
            initial[name] = random.choice(choices)
        stages = [initial]
        valid = True
        for stage in range(3):
            prev = stages[-1]
            new = dict(prev)
            # Sequential moves, but positions checked against all other pieces.
            for name in random.sample(SUSPECTS, len(SUSPECTS)):
                occupied = {new[n] for n in SUSPECTS if n != name}
                # Prevent any innocent from visiting the murder square in history.
                if name != culprit:
                    occupied.add(murder)
                opts = destinations(name, new[name], occupied)
                if stage == 0 and name != culprit:
                    # After two rewinds, only the culprit may have a legal
                    # single-move connection to the murder square, even when
                    # ignoring blockers. Later histories remain unrestricted.
                    opts = [s for s in opts if not legal_move(name, s, murder)]
                if not opts:
                    valid = False
                    break
                new[name] = random.choice(opts)
            if not valid:
                break
            stages.append(new)
        if not valid:
            continue
        current = stages[-1]
        free = [s for s in ALL_SQUARES if s not in current.values() and s != murder]
        if not free:
            continue
        start = random.choice(free)
        histories = {name: [stage[name] for stage in stages] for name in SUSPECTS}
        assert sum(histories[n][0] == murder for n in SUSPECTS) == 1
        assert [n for n in SUSPECTS if legal_move(n, histories[n][1], murder)] == [culprit]
        return {
            "rules_version": RULES_VERSION,
            "murder": murder, "culprit": culprit, "histories": histories,
            "revealed": {n: 0 for n in SUSPECTS},
            "queens": {q: start for q in QUEENS},
            "points": {q: MOVEMENT_POINTS for q in QUEENS},
            "skipped": {q: False for q in QUEENS},
            "round": 1, "turn": 0, "turn_number": 1,
            "waiting": {q: False for q in QUEENS},
            "log": [], "last_reveal": None, "winner": None,
        }
    raise RuntimeError("Could not generate a valid case; please retry.")


def position_of(game, name):
    return game["histories"][name][3 - game["revealed"][name]]


def advance_turn(game):
    game["turn"] = 1 - game["turn"]
    game["turn_number"] += 1
    if all(game["waiting"].values()):
        game["round"] += 1
        game["points"] = {q: MOVEMENT_POINTS for q in QUEENS}
        game["waiting"] = {q: False for q in QUEENS}
        game["log"].append(f"Round {game['round']} unlocked: both queens receive {MOVEMENT_POINTS} new movement points.")


def record(game, message):
    game["log"].append(f"Turn {game['turn_number']} · {message}")
