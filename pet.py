"""Chrome & Oak, the two business mascots (animated SVG).

- Chrome (silver cat, glasses + magnifying glass) = the ANALYST: detects problems.
- Oak (oak-brown cat, tie + briefcase) = the ADVISOR: decides and acts.

Animations are pure CSS (MASCOT_CSS): blinking, tail wag, head tilt, ear
twitch, Chrome scanning with his magnifying glass, Oak swinging his briefcase,
plus a walk-in when they enter the corner. "Click to pet" uses a hidden
checkbox, so no JavaScript is needed.

Gotcha: in st.markdown, lines indented by 4+ spaces become code blocks, so the
HTML strings below are built WITHOUT indentation on purpose.
"""

import streamlit as st

INK = "#2A1F17"

MASCOTS = {
    "chrome": {"name": "Chrome", "role": "Analyst", "fur": "#CDD2D9", "shade": "#9AA2AD",
               "muzzle": "#F1F3F5", "inner_ear": "#E9C3CC", "tie": "#2F4A6D"},
    "oak": {"name": "Oak", "role": "Advisor", "fur": "#B07B4F", "shade": "#8B5E3C",
            "muzzle": "#EBD3B5", "inner_ear": "#E8B9A0", "tie": "#7A2E26"},
}

MASCOT_CSS = """
<style>
.mascot{overflow:visible}
.mascot .m-body{transform-box:fill-box;transform-origin:50% 100%;animation:m-breathe 3.2s ease-in-out infinite}
.mascot .m-head{transform-box:fill-box;transform-origin:50% 90%;animation:m-tilt 6s ease-in-out infinite}
.mascot .m-eyes{transform-box:fill-box;transform-origin:50% 50%;animation:m-blink 4.6s infinite}
.mascot .m-tail{transform-box:fill-box;transform-origin:100% 100%;animation:m-wag 1.6s ease-in-out infinite}
.mascot .m-ear{transform-box:fill-box;transform-origin:50% 100%;animation:m-twitch 5.5s ease-in-out infinite}
.mascot.chrome .m-prop{transform-box:fill-box;transform-origin:0% 100%;animation:m-scan 3.4s ease-in-out infinite}
.mascot.oak .m-prop{transform-box:fill-box;transform-origin:30% 0%;animation:m-swing 2.4s ease-in-out infinite}
.mascot.oak .m-head{animation-delay:-2.5s}
.mascot.oak .m-eyes{animation-delay:-1.7s}
.mascot.oak .m-tail{animation-delay:-.6s}
@keyframes m-breathe{0%,100%{transform:scaleY(1)}50%{transform:scaleY(1.03)}}
@keyframes m-tilt{0%,100%{transform:rotate(0)}30%{transform:rotate(-4deg)}60%{transform:rotate(3deg)}}
@keyframes m-blink{0%,93%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
@keyframes m-wag{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(10deg)}}
@keyframes m-twitch{0%,88%,100%{transform:rotate(0)}91%{transform:rotate(-8deg)}94%{transform:rotate(4deg)}}
@keyframes m-scan{0%,100%{transform:rotate(0) translate(0,0)}35%{transform:rotate(-14deg) translate(-2px,-3px)}70%{transform:rotate(6deg)}}
@keyframes m-swing{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}
@keyframes m-walkin{0%{transform:translateX(160%)}15%,35%,55%,75%{transform:translateX(var(--wx)) translateY(-6px)}25%,45%,65%,85%{transform:translateX(var(--wx2)) translateY(0)}100%{transform:translateX(0)}}
@keyframes m-hop{0%,100%{transform:translateY(0)}40%{transform:translateY(-16px)}}
.walk-in{animation:m-walkin 1.6s ease-out both}
.walk-in.d2{animation-delay:.25s}
@media (prefers-reduced-motion: reduce){.mascot *,.walk-in{animation:none !important}}
</style>
"""


def _face(mood):
    """Return (eyes, brows_and_mouth) SVG for a mood."""
    if mood == "happy":
        eyes = (
            f'<path d="M43 43 q4 -5 8 0" stroke="{INK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
            f'<path d="M59 43 q4 -5 8 0" stroke="{INK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
        )
        rest = f'<path d="M51 53 q2 3 4 0 q2 3 4 0" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>'
        return eyes, rest
    eyes = (
        f'<ellipse cx="47" cy="43" rx="3" ry="3.8" fill="{INK}"/><circle cx="48" cy="41.8" r="1" fill="#FFFFFF"/>'
        f'<ellipse cx="63" cy="43" rx="3" ry="3.8" fill="{INK}"/><circle cx="64" cy="41.8" r="1" fill="#FFFFFF"/>'
    )
    if mood == "worried":
        rest = (
            f'<path d="M42 35 q4 -1.5 8 0" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>'
            f'<path d="M60 35 q4 -1.5 8 0" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>'
            f'<path d="M52 54.5 h6" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
        )
    else:  # sad
        rest = (
            f'<path d="M42 36 l8 -2.5" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
            f'<path d="M68 36 l-8 -2.5" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
            f'<path d="M51 56 q4 -4 8 0" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>'
            '<path d="M45 48 q-1.5 3 0 4.5 q1.5 -1.5 0 -4.5 z" fill="#7FB8F0"/>'
        )
    return eyes, rest


def _prop(who, fur):
    if who == "chrome":  # magnifying glass
        return (
            '<g class="m-prop">'
            '<line x1="84" y1="74" x2="76" y2="84" stroke="#5E3B22" stroke-width="5" stroke-linecap="round"/>'
            '<circle cx="92" cy="66" r="10" fill="#DCEBF7" fill-opacity="0.55" stroke="#8A9099" stroke-width="4"/>'
            '<path d="M87 62 q3 -3 7 -2" stroke="#FFFFFF" stroke-width="2" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="76" cy="83" rx="5" ry="4" fill="{fur}"/>'
            "</g>"
        )
    return (  # briefcase
        '<g class="m-prop">'
        '<path d="M86 68 v-4 q0 -4 4 -4 h6 q4 0 4 4 v4" stroke="#3E2716" stroke-width="3" fill="none"/>'
        '<rect x="79" y="67" width="28" height="22" rx="4" fill="#5E3B22"/>'
        '<rect x="79" y="67" width="28" height="7" rx="3" fill="#4A2F1B"/>'
        '<rect x="90" y="72" width="6" height="5" rx="1" fill="#D4A84A"/>'
        f'<ellipse cx="80" cy="74" rx="5" ry="4" fill="{fur}"/>'
        "</g>"
    )


def mascot_svg(who, mood="happy", size=120):
    """One animated mascot as an inline SVG string. who = "chrome" or "oak"."""
    m = MASCOTS[who]
    fur, shade = m["fur"], m["shade"]
    eyes, rest = _face(mood)
    glasses = ""
    if who == "chrome":
        glasses = (
            '<circle cx="47" cy="43" r="7.5" fill="#DCEBF7" fill-opacity="0.25" stroke="#2E3440" stroke-width="2"/>'
            '<circle cx="63" cy="43" r="7.5" fill="#DCEBF7" fill-opacity="0.25" stroke="#2E3440" stroke-width="2"/>'
            '<path d="M54.5 43 h1" stroke="#2E3440" stroke-width="2"/>'
        )
    return "".join([
        f'<svg class="mascot {who}" width="{size}" height="{round(size * 110 / 120)}" viewBox="0 0 120 110" '
        f'role="img" aria-label="{m["name"]} the {m["role"].lower()}, {mood}">',
        '<ellipse cx="58" cy="104" rx="34" ry="4" fill="#2A1F17" fill-opacity="0.12"/>',
        f'<g class="m-tail"><path d="M36 90 C 16 90, 12 70, 24 62" stroke="{fur}" stroke-width="7" fill="none" stroke-linecap="round"/></g>',
        '<g class="m-body">',
        f'<rect x="34" y="60" width="42" height="40" rx="19" fill="{fur}"/>',
        f'<ellipse cx="45" cy="99" rx="7" ry="4" fill="{shade}"/><ellipse cx="65" cy="99" rx="7" ry="4" fill="{shade}"/>',
        '<path d="M45 62 L55 71 L49 76 Z" fill="#FFFFFF"/><path d="M65 62 L55 71 L61 76 Z" fill="#FFFFFF"/>',
        f'<path d="M53 71 h4 l2 15 l-4 5 l-4 -5 z" fill="{m["tie"]}"/><rect x="52.5" y="69" width="5" height="4" rx="1" fill="{m["tie"]}"/>',
        "</g>",
        _prop(who, fur),
        '<g class="m-head">',
        f'<g class="m-ear"><polygon points="27,36 31,8 50,26" fill="{fur}"/><polygon points="32,30 33,15 44,26" fill="{m["inner_ear"]}"/></g>',
        f'<polygon points="83,36 79,8 60,26" fill="{fur}"/><polygon points="78,30 77,15 66,26" fill="{m["inner_ear"]}"/>',
        f'<ellipse cx="55" cy="42" rx="30" ry="24" fill="{fur}"/>',
        f'<path d="M52 21 v6 M55 20 v7 M58 21 v6" stroke="{shade}" stroke-width="2" stroke-linecap="round"/>',
        f'<ellipse cx="55" cy="51" rx="13" ry="9" fill="{m["muzzle"]}"/>',
        '<ellipse cx="39" cy="50" rx="4.5" ry="2.6" fill="#F4A6A6" fill-opacity="0.6"/>',
        '<ellipse cx="71" cy="50" rx="4.5" ry="2.6" fill="#F4A6A6" fill-opacity="0.6"/>',
        '<path d="M53 48.5 h4 l-2 2.5 z" fill="#D9798C"/>',
        f'<g class="m-eyes">{eyes}</g>',
        rest,
        glasses,
        "</g>",
        "</svg>",
    ])


def mascots_pair(mood_chrome="happy", mood_oak="happy", size=120, walk_in=False):
    """Both mascots side by side (welcome page, banner)."""
    cls = ' class="walk-in"' if walk_in else ""
    cls2 = ' class="walk-in d2"' if walk_in else ""
    return (
        '<div style="display:flex;gap:2px;align-items:flex-end;--wx:90%;--wx2:60%">'
        f'<span{cls} style="display:inline-block;--wx:80%;--wx2:50%">{mascot_svg("chrome", mood_chrome, size)}</span>'
        f'<span{cls2} style="display:inline-block;--wx:60%;--wx2:30%">{mascot_svg("oak", mood_oak, size)}</span>'
        "</div>"
    )


DUO_CSS = """
<style>
.duo{position:fixed;right:24px;bottom:20px;z-index:9999;display:flex;flex-direction:column;align-items:flex-end;gap:8px;font-family:'Inter',sans-serif}
#duo-toggle{position:absolute;opacity:0;pointer-events:none}
.duo-chat{width:330px;background:#FFFFFF;border:1px solid #E9E1D6;border-radius:16px 16px 4px 16px;padding:14px 16px;box-shadow:0 12px 32px rgba(36,26,19,.16);display:flex;flex-direction:column;gap:10px;animation:duo-pop .4s .3s ease-out both}
.duo-head{display:flex;justify-content:space-between;align-items:center;font-size:12px;font-weight:700;color:#6B5B4E;border-bottom:1px solid #F0EAE1;padding-bottom:8px}
.duo-live{display:inline-flex;align-items:center;gap:6px}
.duo-live::before{content:"";width:8px;height:8px;border-radius:50%;background:#3F8F50;box-shadow:0 0 0 3px #E3F1E5}
.duo-line{display:flex;gap:10px;align-items:flex-start}
.duo-who{flex:none;font-size:11px;font-weight:800;letter-spacing:.8px;text-transform:uppercase;padding:3px 9px;border-radius:999px;margin-top:2px}
.duo-who.chrome{background:#E8EBEF;color:#2E3440}
.duo-who.oak{background:#F3EADF;color:#5E3B22}
.duo-text{font-size:14.5px;line-height:1.5;color:#241A13}
.duo-chat .thanks{display:none}
.duo-btn{display:flex;align-items:flex-end;cursor:pointer;background:linear-gradient(180deg,#FFFFFF,#F4F1EC);border:1px solid #E0D7CB;border-radius:20px;padding:4px 8px 0;box-shadow:0 10px 24px rgba(36,26,19,.16);transition:transform .2s}
.duo-btn:hover{transform:translateY(-3px)}
#duo-toggle:focus-visible + .duo-chat + .duo-btn{outline:3px solid #8B5E3C;outline-offset:3px}
.duo-hint{font-size:12px;font-weight:600;color:#6B5B4E}
#duo-toggle:checked ~ .duo-chat .msg{display:none}
#duo-toggle:checked ~ .duo-chat .thanks{display:flex}
#duo-toggle:checked ~ .duo-btn .mascot{animation:m-hop .5s ease-in-out 3}
@keyframes duo-pop{0%{opacity:0;transform:translateY(8px) scale(.97)}100%{opacity:1;transform:none}}
</style>
"""


def show_pets(mood, chrome_msg, oak_msg):
    """Floating Chrome & Oak in the bottom-right corner, talking to each other."""
    oak_mood = "happy" if mood == "happy" else "worried"  # Oak stays calm: he has a plan
    html = (
        DUO_CSS
        + '<div class="duo">'
        + '<input type="checkbox" id="duo-toggle" aria-label="Pet Chrome and Oak">'
        + '<div class="duo-chat" role="status">'
        + '<div class="duo-head"><span class="duo-live">Watching your data</span><span>Chrome &amp; Oak</span></div>'
        + f'<div class="duo-line msg"><span class="duo-who chrome">Chrome</span><span class="duo-text">{chrome_msg}</span></div>'
        + f'<div class="duo-line msg"><span class="duo-who oak">Oak</span><span class="duo-text">{oak_msg}</span></div>'
        + '<div class="duo-line thanks"><span class="duo-who chrome">Chrome</span><span class="duo-text">Purr... okay, back to the numbers!</span></div>'
        + '<div class="duo-line thanks"><span class="duo-who oak">Oak</span><span class="duo-text">Thanks, partner. Click us again for the update.</span></div>'
        + "</div>"
        + '<label for="duo-toggle" class="duo-btn" title="Pet Chrome &amp; Oak">'
        + f'<span style="display:inline-block">{mascot_svg("chrome", mood, 76)}</span>'
        + f'<span style="display:inline-block">{mascot_svg("oak", oak_mood, 76)}</span>'
        + "</label>"
        + '<span class="duo-hint">Click to pet</span>'
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)
