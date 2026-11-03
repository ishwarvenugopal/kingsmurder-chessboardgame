"""Streamlit interface and session-state interactions."""

import streamlit as st
import streamlit.components.v1 as components

from board import board_html
from constants import GLYPHS, MOVEMENT_POINTS, QUEENS, RULES_VERSION, SUSPECTS
from game import (
    advance_turn,
    generate_case,
    interrogation_choices,
    position_of,
    record,
    skip_turn,
)


def reset():
    st.session_state.game = generate_case()


def render_app():
    """Render the game and handle the current player interaction."""
    st.set_page_config(page_title="Murder at the Black Castle", page_icon="♛", layout="wide")

    if "game" not in st.session_state or st.session_state.game.get("rules_version") != RULES_VERSION:
        reset()
    g = st.session_state.game

    st.title("♛ Murder at the Black Castle")
    st.caption("A two-player chessboard detective game · Reconstruct three hidden moves to discover the killer")
    with st.sidebar:
        st.header("Case controls")
        if st.button("🎲 Generate new mystery", use_container_width=True):
            reset()
            st.rerun()
        st.write("**Rules**")
        st.markdown("""- White Queen takes the first turn.
- One interrogation, accusation, or skip per turn.
- Both queens start on the same unoccupied square.
- Queens take the shortest clear route, changing direction as needed; each traversed square costs 1 point.
- Interrogate from the same square as a suspect or any of its 8 neighboring squares.
- Each player may skip voluntarily only once per game.
- Each suspect rewinds one historical move per interrogation.
- Both queens share all revealed clues.
- A queen may end her movement round early; once both finish, both get 10 fresh points.
- After two clues per suspect, only the murderer has a legal move to the murder square.
- A wrong accusation loses the game.""")
        st.info("The case solution is held privately in the app's session state. Do not inspect source/session state while playing.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Murder square", g["murder"])
    c2.metric("Movement round", g["round"])
    c3.metric("Turn", g["turn_number"])

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        current_positions = {n: position_of(g, n) for n in SUSPECTS}
        current_positions.update(g["queens"])
        components.html(board_html(current_positions, g["murder"], caption="Current investigation board"), height=585)
        st.caption("Red ✕ = murder square. ♕/♛ = detectives. Other chess pieces = suspects. Revealed suspects remain at their rewound squares. Pieces sharing a square appear side by side.")

    with right:
        st.subheader("Detective dashboard")
        p1, p2 = st.columns(2)
        for col, queen in zip((p1, p2), QUEENS):
            with col:
                st.metric(queen, f"{g['points'][queen]} / {MOVEMENT_POINTS}", delta="Waiting" if g["waiting"][queen] else f"At {g['queens'][queen]}", delta_color="off")
        if g["winner"]:
            st.success(g["winner"])
            st.write(f"**The murderer was: {g['culprit']}**")
            if st.button("Play another case", type="primary"):
                reset()
                st.rerun()
        else:
            queen = QUEENS[g["turn"]]
            if g["waiting"][queen]:
                st.warning(f"{queen} has finished this movement round and must wait.")
                if st.button("Pass waiting turn", use_container_width=True):
                    advance_turn(g)
                    st.rerun()
            else:
                st.info(f"**{queen}'s turn** · {g['points'][queen]} movement points remaining")
                action = st.radio("Choose your action", ["Interrogate", "Skip turn", "End my movement round", "Accuse"], horizontal=True)
                if action == "Interrogate":
                    suspect = st.selectbox("Suspect to question", SUSPECTS, format_func=lambda n: f"{GLYPHS[n]} {n} · {position_of(g,n)} · {g['revealed'][n]}/3 clues")
                    target = position_of(g, suspect)
                    choices = interrogation_choices(g, queen, suspect)
                    if g["revealed"][suspect] == 3:
                        st.warning("All three movements of this suspect have already been revealed.")
                    elif not choices:
                        st.warning("No interrogation square is reachable with the remaining points. Choose another suspect or end your movement round.")
                    else:
                        labels = {f"{s} · {cost} point{'s' if cost != 1 else ''}": (s, cost) for s, cost in choices}
                        selection = st.selectbox("Move queen to an interrogation square", list(labels))
                        dest, cost = labels[selection]
                        st.caption(f"Queen: {g['queens'][queen]} → {dest} | Cost: {cost} | Suspect currently at {target}")
                        if st.button("Move and reveal one historical move", type="primary", use_container_width=True):
                            g["queens"][queen] = dest
                            g["points"][queen] -= cost
                            g["revealed"][suspect] += 1
                            old = target
                            new = position_of(g, suspect)
                            g["last_reveal"] = {"suspect": suspect, "from": old, "to": new, "by": queen}
                            record(g, f"{queen} spent {cost} points ({dest}) and questioned {suspect}: {old} → {new}.")
                            if g["points"][queen] == 0:
                                g["waiting"][queen] = True
                            advance_turn(g)
                            st.rerun()
                elif action == "Skip turn":
                    used_skip = g["skipped"][queen]
                    if used_skip:
                        st.warning("You have already used your one skip for this game. Choose another action.")
                    else:
                        st.caption("Use your one skip for this game and save your movement points.")
                    if st.button("Skip interrogation", use_container_width=True, disabled=used_skip):
                        if skip_turn(g, queen):
                            st.rerun()
                elif action == "End my movement round":
                    st.caption("Forfeit your unused points and wait until the other queen also finishes their round.")
                    if st.button("Finish my round", use_container_width=True):
                        record(g, f"{queen} ended their movement round early.")
                        g["waiting"][queen] = True
                        g["points"][queen] = 0
                        advance_turn(g)
                        st.rerun()
                else:
                    accused = st.selectbox("Who killed the Black King?", SUSPECTS)
                    if st.button("Submit final accusation", type="primary", use_container_width=True):
                        if accused == g["culprit"]:
                            g["winner"] = f"🏆 {queen} wins! Correct accusation."
                        else:
                            other = QUEENS[1-g["turn"]]
                            g["winner"] = f"🏆 {other} wins! {queen} wrongly accused {accused}."
                        record(g, f"{queen} accused {accused}. {g['winner']}")
                        st.rerun()

    st.divider()
    st.subheader("🔎 Suspect movement evidence — 6 × 3")
    st.caption("Columns are interrogation order: first reveal = most recent position, third reveal = location at the time of the murder.")
    rows = []
    for n in SUSPECTS:
        hist = g["histories"][n]
        count = g["revealed"][n]
        rows.append({"Suspect": f"{GLYPHS[n]} {n}", "Current position": position_of(g,n),
                     "1st reveal (one move back)": hist[2] if count >= 1 else "🔒 Hidden",
                     "2nd reveal (two moves back)": hist[1] if count >= 2 else "🔒 Hidden",
                     "3rd reveal (murder time)": hist[0] if count >= 3 else "🔒 Hidden"})
    st.dataframe(rows, hide_index=True, use_container_width=True)

    if g["last_reveal"]:
        clue = g["last_reveal"]
        st.subheader("🎬 Latest reconstructed movement")
        st.write(f"**{clue['suspect']}** moved backward from **{clue['from']}** to **{clue['to']}**, revealed by **{clue['by']}**.")
        # This mini-board is intentionally isolated so the historical movement is easy to see.
        components.html(board_html({clue["suspect"]: clue["to"]}, g["murder"], start=clue["from"], end=clue["to"], caption=f"{clue['suspect']}: {clue['from']} → {clue['to']} (rewind)", compact=True), height=445)
        st.caption("Yellow outline = position before interrogation. Turquoise outline = revealed earlier position. Arrow shows the rewind direction.")

    with st.expander("📜 Investigation log", expanded=False):
        if g["log"]:
            for event in reversed(g["log"]):
                st.write("•", event)
        else:
            st.write("No moves recorded yet.")

    if g["winner"]:
        with st.expander("🔓 Complete case solution", expanded=True):
            st.write(f"**Murder square:** {g['murder']} · **Murderer:** {g['culprit']}")
            for n in SUSPECTS:
                st.write(f"{GLYPHS[n]} **{n}:** {' → '.join(g['histories'][n])}")

    st.caption("Game state is stored in the current Streamlit session. Refreshing normally preserves it; server restarts or a new browser session start a new case.")
