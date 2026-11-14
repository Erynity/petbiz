"""Floating pixel pet that sits in the bottom-right corner of the Streamlit page.

How it works:
- Python decides the pet's mood and message (happy / worried / sad).
- This file turns that into a small piece of HTML + CSS.
- Streamlit shows it with st.markdown(..., unsafe_allow_html=True).
- "Click to pet" uses a hidden checkbox + CSS, so no JavaScript is needed.

Gotcha: in st.markdown, lines indented by 4+ spaces become code blocks,
so the HTML below is built WITHOUT indentation on purpose.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Pixel art: each rectangle is (x, y, width, height, colour) on a 16x16 grid
# ---------------------------------------------------------------------------
FUR = "#FFFFFF"
SHADE = "#C9B6E4"
INK = "#3A2350"
BLUSH = "#F7A8C6"
TEAR = "#7FB8F0"

BODY = [
    (3, 2, 2, 2, FUR), (11, 2, 2, 2, FUR),        # ears
    (4, 3, 1, 1, BLUSH), (11, 3, 1, 1, BLUSH),    # inner ears
    (3, 4, 10, 6, FUR),                           # head
    (4, 10, 8, 4, FUR), (6, 11, 4, 2, "#E4D6F5"), # body + belly
    (4, 14, 2, 1, SHADE), (10, 14, 2, 1, SHADE),  # paws
    (12, 11, 2, 1, FUR), (13, 10, 1, 1, FUR),     # tail
]

FACES = {
    "happy": [
        (5, 6, 1, 2, INK), (10, 6, 1, 2, INK),         # round eyes
        (4, 8, 1, 1, BLUSH), (11, 8, 1, 1, BLUSH),     # blush
        (6, 8, 1, 1, INK), (9, 8, 1, 1, INK), (7, 9, 2, 1, INK),  # smile
    ],
    "worried": [
        (5, 6, 2, 1, INK), (9, 6, 2, 1, INK),          # flat brows
        (5, 7, 1, 1, INK), (10, 7, 1, 1, INK),         # eyes
        (7, 9, 2, 1, INK),                              # small mouth
    ],
    "sad": [
        (5, 7, 2, 1, INK), (9, 7, 2, 1, INK),          # closed eyes
        (5, 8, 1, 1, TEAR),                             # tear
        (7, 9, 2, 1, INK), (6, 10, 1, 1, INK), (9, 10, 1, 1, INK),  # frown
    ],
}

BADGE_COLOURS = {"happy": "#7BC67E", "worried": "#F5C33B", "sad": "#F08BB4"}


def _pet_svg(mood: str, size: int) -> str:
    """Build the pixel cat as an inline SVG string."""
    rects = BODY + FACES.get(mood, FACES["happy"])
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>'
        for (x, y, w, h, c) in rects
    ]
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'shape-rendering="crispEdges" aria-hidden="true">{"".join(parts)}</svg>'
    )


PET_CSS = """
<style>
.pet-wrap{position:fixed;right:28px;bottom:28px;z-index:9999;display:flex;flex-direction:column;align-items:flex-end;gap:10px;font-family:'Nunito',sans-serif}
#pet-toggle{display:none}
.pet-bubble{max-width:300px;background:#FFFFFF;color:#3A2350;border-radius:24px 24px 6px 24px;padding:14px 18px;font-size:16px;font-weight:600;line-height:1.45;box-shadow:0 6px 20px rgba(58,35,80,.18)}
.pet-bubble .pet-name{display:block;font-size:13px;font-weight:800;color:#8E6FC2;margin-bottom:2px}
.pet-bubble .purr{display:none}
.pet-btn{position:relative;width:96px;height:96px;border-radius:50%;background:#F7C6D9;border:5px solid #FFFFFF;box-shadow:0 6px 20px rgba(58,35,80,.25);cursor:pointer;display:flex;align-items:center;justify-content:center}
.pet-btn svg{animation:pet-bob 1.6s ease-in-out infinite}
.pet-badge{position:absolute;top:-6px;right:-6px;width:28px;height:28px;border-radius:50%;color:#3A2350;border:3px solid #FFFFFF;font-weight:800;font-size:15px;display:flex;align-items:center;justify-content:center}
.pet-hint{font-size:12px;font-weight:700;color:#6B5A80}
#pet-toggle:checked ~ .pet-bubble .msg{display:none}
#pet-toggle:checked ~ .pet-bubble .purr{display:block}
#pet-toggle:checked ~ .pet-btn svg{animation:pet-wiggle .35s ease-in-out 4}
@keyframes pet-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes pet-wiggle{0%,100%{transform:rotate(0)}25%{transform:rotate(-12deg)}75%{transform:rotate(12deg)}}
</style>
"""


def show_pet(mood: str, message: str, name: str = "Mochi") -> None:
    """Draw the floating pet.

    mood:    "happy", "worried" or "sad"
    message: what the pet says in its speech bubble
    """
    badge = "!" if mood != "happy" else "♥"
    html = (
        PET_CSS
        + '<div class="pet-wrap">'
        + '<input type="checkbox" id="pet-toggle">'
        + '<div class="pet-bubble">'
        + f'<span class="pet-name">{name}</span>'
        + f'<span class="msg">{message}</span>'
        + '<span class="purr">Purr... thank you! ♥ Click me again to hear the update.</span>'
        + "</div>"
        + f'<label for="pet-toggle" class="pet-btn" title="Pet {name}">'
        + f'<span class="pet-badge" style="background:{BADGE_COLOURS.get(mood, "#F5C33B")}">{badge}</span>'
        + _pet_svg(mood, 60)
        + "</label>"
        + '<span class="pet-hint">Click to pet</span>'
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def pet_avatar(mood: str, size: int = 140) -> str:
    """Bigger version of the pet (as HTML) for the banner."""
    return _pet_svg(mood, size)
