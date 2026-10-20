"""
app.py - Readings 5 interactive presentation (Streamlit).

Run:  streamlit run app.py
Keys: Right arrow / PageDown = next slide, Left arrow / PageUp = previous slide
      (when a slider is focused, arrows move the slider instead).
"""
import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import config
import content
from demos import actuator_net, domain_rand, kine2go, pipeline, sdk_demo

st.set_page_config(page_title="Readings 5 - Crime-Scene Go2", page_icon="🐕",
                   layout="wide", initial_sidebar_state="collapsed")

N_SLIDES = len(content.SLIDES)

# ----------------------------------------------------------------------------
# Theme: navy title bar, accent colours, projector-sized fonts
# ----------------------------------------------------------------------------
st.markdown(f"""
<style>
html, body, [class*="css"], .stMarkdown, .stMarkdown p, .stMarkdown li {{ font-size: 1.22rem; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 100%; }}
.title-bar {{ background: {config.NAVY}; color: white; padding: 18px 28px; border-radius: 10px;
             border-bottom: 6px solid {config.ACCENT}; display: flex; justify-content: space-between;
             align-items: center; margin-bottom: 0.8rem; }}
.title-bar h1 {{ color: white; font-size: 2.3rem; margin: 0; padding: 0; line-height: 1.2; }}
.title-bar .counter {{ color: {config.ACCENT}; font-size: 1.3rem; font-weight: 700; white-space: nowrap;
                      margin-left: 24px; }}
.source-tag {{ display: inline-block; padding: 4px 14px; border-radius: 14px; color: white;
              font-weight: 700; font-size: 1.0rem; margin-bottom: 0.4rem; }}
.why-box {{ background: #FFF6E5; border-left: 8px solid {config.ACCENT}; padding: 14px 20px;
           border-radius: 6px; margin-top: 0.6rem; }}
.why-box h3 {{ color: {config.NAVY}; margin-top: 0; }}
.toy-badge {{ background: {config.ACCENT_3}; color: white; padding: 3px 10px; border-radius: 6px;
             font-weight: 700; font-size: 0.95rem; }}
.ok-badge {{ background: #1F9D55; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 700; }}
.grey-badge {{ background: {config.GREY}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 700; }}
.big-title {{ text-align: center; margin-top: 8vh; }}
.big-title h1 {{ font-size: 3.2rem; color: {config.NAVY}; }}
.big-title h3 {{ color: {config.GREY}; font-weight: 500; }}
div.stButton > button {{ font-size: 1.15rem; padding: 0.4rem 1.4rem; }}
[data-testid="stWidgetLabel"] p {{ font-size: 1.1rem !important; }}
button[data-baseweb="tab"] p {{ font-size: 1.12rem !important; font-weight: 600; }}
[data-testid="stCaptionContainer"] {{ font-size: 1.02rem; }}
table.summary {{ width: 100%; border-collapse: collapse; font-size: 1.12rem; }}
table.summary th {{ background: {config.NAVY}; color: white; padding: 10px; text-align: left; }}
table.summary td {{ padding: 10px; border-bottom: 1px solid #DDE3EA; vertical-align: top; }}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Navigation state
# ----------------------------------------------------------------------------
if "slide" not in st.session_state:
    st.session_state.slide = 0


def go(delta):
    st.session_state.slide = min(max(st.session_state.slide + delta, 0), N_SLIDES - 1)


def jump():
    st.session_state.slide = content.SLIDE_TITLES.index(st.session_state.jump_to)


# Keyboard shortcuts: a tiny script that clicks the Previous/Next buttons.
components.html("""
<script>
const doc = window.parent.document;
if (!doc.__r5_keys) {
  doc.__r5_keys = true;
  doc.addEventListener('keydown', (e) => {
    const a = doc.activeElement;
    if (a && (a.getAttribute('role') === 'slider' || ['INPUT', 'TEXTAREA', 'SELECT'].includes(a.tagName))) return;
    let label = null;
    if (e.key === 'ArrowRight' || e.key === 'PageDown') label = 'Next';
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') label = 'Previous';
    if (!label) return;
    const btn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText.includes(label));
    if (btn) { btn.click(); e.preventDefault(); }
  });
}
</script>
""", height=0)

with st.sidebar:
    st.markdown("### Slides")
    st.session_state.jump_to = content.SLIDE_TITLES[st.session_state.slide]
    st.selectbox("Jump to slide", content.SLIDE_TITLES, key="jump_to", on_change=jump)
    st.markdown("---")
    st.markdown("### Export")
    if st.button("Export to PowerPoint", use_container_width=True):
        import export_pptx
        with st.spinner("Building the deck (runs every demo at default settings)..."):
            path = export_pptx.build_presentation()
        st.success(f"Saved to {path.relative_to(config.PROJECT_ROOT)}")
        st.download_button("Download .pptx", path.read_bytes(), file_name=path.name,
                           mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                           use_container_width=True)
    st.caption("Tip: use the arrow keys to change slides.")

slide = content.SLIDES[st.session_state.slide]

# ----------------------------------------------------------------------------
# Layout helpers
# ----------------------------------------------------------------------------
def title_bar(title):
    st.markdown(f'<div class="title-bar"><h1>{html.escape(title)}</h1>'
                f'<span class="counter">Slide {st.session_state.slide + 1} / {N_SLIDES}</span></div>',
                unsafe_allow_html=True)


def nav_buttons(where):
    c1, c2, c3 = st.columns([1, 6, 1])
    c1.button("◀ Previous", on_click=go, args=(-1,), disabled=st.session_state.slide == 0,
              use_container_width=True, key=f"prev_{where}")
    c3.button("Next ▶", on_click=go, args=(1,), disabled=st.session_state.slide == N_SLIDES - 1,
              use_container_width=True, key=f"next_{where}")
    if where == "top":
        c2.progress((st.session_state.slide + 1) / N_SLIDES)


def source_tag(src):
    st.markdown(f'<span class="source-tag" style="background:{config.SOURCE_COLORS[src]}">{src}</span>',
                unsafe_allow_html=True)


def bullets(points):
    st.markdown("\n".join(f"- {p}" for p in points))


def why_box(points):
    items = "".join(f"<li>{html.escape(p)}</li>" for p in points)
    st.markdown(f'<div class="why-box"><h3>Why it matters for our dog</h3><ul>{items}</ul></div>',
                unsafe_allow_html=True)


def show(fig):
    st.pyplot(fig, use_container_width=True, clear_figure=False)


def speaker_notes(text):
    with st.expander("Speaker notes"):
        st.write(text)


# ----------------------------------------------------------------------------
# Cached demo runs (each one is fast; caching keeps slide changes instant)
# ----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Training the toy actuator network...")
def cached_actuator(delay_ms):
    return actuator_net.run(delay_ms)


@st.cache_resource(show_spinner="Tuning both controllers...")
def cached_controllers():
    return domain_rand.tune_both()


@st.cache_resource(show_spinner="Testing on shifted floors...")
def cached_dr_eval():
    ctrls = cached_controllers()
    res = domain_rand.evaluate(ctrls)
    return res, domain_rand.success_bar_figure(res)


@st.cache_resource(show_spinner="Running the mock SDK...")
def cached_sdk():
    return sdk_demo.run(with_gif=True)


@st.cache_resource(show_spinner=False)
def cached_pipeline():
    return pipeline.pipeline_figure()


@st.cache_resource(show_spinner="Loading motion data...")
def cached_kine2go(download):
    return kine2go.run(download=download, with_gif=True)


# ----------------------------------------------------------------------------
# Slides
# ----------------------------------------------------------------------------
def slide_title():
    st.markdown(f"""
<div class="big-title">
  <h1>{html.escape(config.PRESENTATION_TITLE)}</h1>
  <h3>{html.escape(slide['subtitle'])}</h3>
  <br>
  <h2 style="color:{config.NAVY}">{config.AUTHOR}</h2>
  <h3>{config.COURSE}</h3>
  <h3>{config.PRESENTATION_DATE}</h3>
</div>""", unsafe_allow_html=True)
    st.markdown(" ")
    cols = st.columns(4)
    for c, src in zip(cols, config.SOURCE_COLORS):
        c.markdown(f'<div style="text-align:center"><span class="source-tag" '
                   f'style="background:{config.SOURCE_COLORS[src]}">{src}</span></div>', unsafe_allow_html=True)


def slide_pipeline():
    show(cached_pipeline())
    bullets(slide["points"])


def slide_hwangbo():
    source_tag(slide["source"])
    left, right = st.columns([1, 1.35])
    with left:
        st.markdown("#### Key ideas (from my notes)")
        bullets(slide["points"])
    with right:
        st.markdown(f"#### {slide['demo_title']} <span class='toy-badge'>TOY MODEL</span>", unsafe_allow_html=True)
        st.caption(slide["demo_caption"])
        delay = st.slider("Hidden communication delay in the toy actuator (ms)", 0, config.ACT_MAX_DELAY_MS,
                          config.ACT_DEFAULT_DELAY_MS, step=2)
        res = cached_actuator(delay)
        show(res["figures"]["actuator_comparison"])
        e = list(res["errors"].values())
        m1, m2, m3 = st.columns(3)
        m1.metric("Ideal model RMSE", f"{e[0]:.2f} N·m")
        m2.metric("Analytical model RMSE", f"{e[1]:.2f} N·m")
        m3.metric("Learned net RMSE", f"{e[2]:.2f} N·m")
        show(res["figures"]["actuator_delay_sweep"])
        st.caption(f"Demo time: {res['seconds']:.1f} s ({res['n_samples']:,} synthetic samples, "
                   f"{res['log_minutes']:.0f} min of toy logs).")
    why_box(slide["why"])


def slide_survey():
    source_tag(slide["source"])
    left, right = st.columns([1, 1.35])
    with left:
        st.markdown("#### Key ideas (from my notes)")
        bullets(slide["points"])
    with right:
        st.markdown(f"#### {slide['demo_title']} <span class='toy-badge'>TOY MODEL</span>", unsafe_allow_html=True)
        st.caption(slide["demo_caption"])
        results, bar_fig = cached_dr_eval()
        show(bar_fig)
        st.markdown("**Try to break the fixed controller:**")
        s1, s2, s3 = st.columns(3)
        fr = s1.slider("Floor friction μ", 0.0, 0.6, config.DR_NOMINAL["friction"], 0.01)
        ma = s2.slider("Mass (kg)", 0.5, 3.0, config.DR_NOMINAL["mass"], 0.1)
        stg = s3.slider("Motor strength", 0.5, 1.5, config.DR_NOMINAL["strength"], 0.05)
        fig, outcome = domain_rand.live_figure(cached_controllers(), fr, ma, stg)
        show(fig)
        g = cached_controllers()
        st.caption("Gains found by random search - " + "; ".join(
            f"{k}: kp={v[0]:.1f}, kd={v[1]:.2f}, ff={v[2]:.2f}" for k, v in g.items()))
    why_box(slide["why"])


def slide_kine2go():
    source_tag(slide["source"])
    left, right = st.columns([1, 1.35])
    with left:
        st.markdown("#### Key ideas (from my notes)")
        bullets(slide["points"])
        st.markdown("**Column layout used by this app**")
        layout = pd.DataFrame(
            [(k, f"{v.start}:{v.stop}", "from notes" if k == "foot_pos" else "assumed")
             for k, v in config.KINE2GO_ASSUMED_LAYOUT.items()],
            columns=["field", "columns", "status"])
        st.dataframe(layout, hide_index=True, use_container_width=True)
    with right:
        st.markdown(f"#### {slide['demo_title']}")
        st.caption(slide["demo_caption"])
        if "k2g_download" not in st.session_state:
            st.session_state.k2g_download = False
        if st.button("Try to download one real motion.npy from Hugging Face"):
            st.session_state.k2g_download = True
        res = cached_kine2go(st.session_state.k2g_download)
        if res["synthetic"]:
            st.markdown('<span class="toy-badge">SYNTHETIC SAMPLE - not Kine2Go data</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="ok-badge">Real Kine2Go motion.npy loaded</span>', unsafe_allow_html=True)
        st.caption(f"{res['message']}  Shape {res['shape']}, {res['duration_s']:.1f} s at {config.KINE2GO_FPS} Hz.")
        c1, c2 = st.columns(2)
        with c1:
            show(res["figures"]["kine2go_joints"])
        with c2:
            show(res["figures"]["kine2go_feet"])
        c3, c4 = st.columns(2)
        with c3:
            show(res["figures"]["kine2go_footfall"])
        with c4:
            st.image(res["gif"], caption="Animated side view (simplified stick figure)", use_column_width=True)
    why_box(slide["why"])


def slide_sdk():
    source_tag(slide["source"])
    res = cached_sdk()
    if res["real_sdk"]:
        st.markdown('<span class="ok-badge">Real SDK detected (unitree_sdk2py installed) - '
                    'this app still never sends commands to hardware</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="grey-badge">Using mock_unitree.py (real SDK not installed - not needed)</span>',
                    unsafe_allow_html=True)
    left, right = st.columns([1, 1.35])
    with left:
        st.markdown("#### Key ideas (from my notes)")
        bullets(slide["points"])
    with right:
        st.markdown(f"#### {slide['demo_title']} <span class='toy-badge'>MOCK</span>", unsafe_allow_html=True)
        st.caption(slide["demo_caption"])
        tab_a, tab_b = st.tabs(["(a) Policy loop: LowState -> network -> LowCmd",
                                "(b) Investigation layer: Move(vx, vy, vyaw)"])
        with tab_a:
            snaps = res["loop"]["snapshots"]
            i = st.slider("Policy step to inspect", 0, len(snaps) - 1, len(snaps) - 1)
            snap = snaps[i]
            st.markdown(f"**Tick {snap['tick']}** (t = {snap['tick'] * config.SDK_CONTROL_DT * 1000:.0f} ms)")
            c1, c2 = st.columns([1, 1.6])
            with c1:
                st.markdown("Observation vector (45 values)")
                st.dataframe(pd.DataFrame({"obs": sdk_demo.OBS_NAMES, "value": snap["obs"].round(3)}),
                             hide_index=True, height=330, use_container_width=True)
            with c2:
                st.markdown("Outgoing LowCmd.motor_cmd[0..11]")
                st.dataframe(pd.DataFrame(snap["cmd"], columns=["q", "dq", "kp", "kd", "tau"]).round(3),
                             height=330, use_container_width=True)
            show(res["figures"]["sdk_policy_loop"])
        with tab_b:
            c1, c2 = st.columns([1.2, 1])
            with c1:
                st.image(res["gif"], caption="Animated path (synthetic scene, mock SportClient)",
                         use_column_width=True)
            with c2:
                cmds = pd.DataFrame(res["investigation"]["cmds"], columns=["vx", "vy", "vyaw"]).round(2)
                cmds.insert(0, "t (s)", (cmds.index * config.SDK_MOVE_DT).round(1))
                st.markdown(f"{res['n_move_cmds']} Move commands sent, {res['n_spots']} spots investigated")
                st.dataframe(cmds, hide_index=True, height=360, use_container_width=True)
    why_box(slide["why"])


def slide_summary():
    head = "".join(f"<th>{h}</th>" for h in slide["table_header"])
    rows = ""
    for r in slide["table"]:
        tag = f'<span class="source-tag" style="background:{config.SOURCE_COLORS[r[0]]}">{r[0]}</span>'
        rows += "<tr>" + f"<td>{tag}</td>" + "".join(f"<td>{html.escape(c)}</td>" for c in r[1:]) + "</tr>"
    st.markdown(f'<table class="summary"><tr>{head}</tr>{rows}</table>', unsafe_allow_html=True)
    st.markdown("### Next steps")
    st.markdown("\n".join(f"{i + 1}. {s}" for i, s in enumerate(slide["next_steps"])))


def slide_references():
    for r in slide["refs"]:
        st.markdown(f"<p style='padding-left:2em;text-indent:-2em;font-size:1.25rem'>{html.escape(r)}</p>",
                    unsafe_allow_html=True)


RENDER = {"title": slide_title, "pipeline": slide_pipeline, "hwangbo": slide_hwangbo,
          "survey": slide_survey, "kine2go": slide_kine2go, "sdk": slide_sdk,
          "summary": slide_summary, "references": slide_references}

# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------
title_bar(slide["title"] if slide["key"] != "title" else "Readings 5")
nav_buttons("top")
RENDER[slide["key"]]()
speaker_notes(slide["notes"])
nav_buttons("bottom")
