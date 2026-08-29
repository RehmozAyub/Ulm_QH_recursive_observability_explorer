"""Recursive Observability Explorer — THIN entry point.

Sets page config, renders the persistent elements (disclaimer, claim legend),
calls the sidebar builder, integrates the model, and routes to the tab
renderers.  All logic lives in model/, viz/, ui/.
"""

import streamlit as st

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="Recursive Observability Explorer",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for premium dark-mode aesthetics
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Main header gradient */
    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 4px 30px rgba(0,0,0,0.3);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #ffd43b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        color: rgba(255,255,255,0.55);
        font-size: 0.9rem;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 500;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 12px;
    }

    /* Sidebar refinement */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>🔭 Recursive Observability Explorer</h1>
        <p>Interactive simulation of the Recursive Observability Filter (ROF) framework for the Fermi Paradox</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Persistent elements
# ---------------------------------------------------------------------------
from ui.tabs import render_disclaimer, render_claim_legend

render_disclaimer()
render_claim_legend()

# ---------------------------------------------------------------------------
# Sidebar → ModelParams + y0
# ---------------------------------------------------------------------------
from ui.sidebar import build_sidebar

params, y0 = build_sidebar()

# ---------------------------------------------------------------------------
# Solve
# ---------------------------------------------------------------------------
from model.solver import integrate

with st.spinner("Integrating..."):
    result = integrate(params, y0)

if not result.success:
    st.warning(f"⚠️ Solver warning: {result.message}")

# ---------------------------------------------------------------------------
# Tab routing
# ---------------------------------------------------------------------------
from ui.tabs import (
    render_trajectories,
    render_phase_diagram,
    render_lambert,
    render_obs_functions,
    render_regime,
    render_drake,
)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Trajectories",
    "🌀 Phase Diagram",
    "🔬 Lambert Filter",
    "📊 O(I) Functions",
    "🏷️ Regime",
    "🛸 Drake / Decomposition",
])

with tab1:
    render_trajectories(result, params)

with tab2:
    render_phase_diagram(result, params, y0)

with tab3:
    render_lambert(result, params)

with tab4:
    render_obs_functions(params)

with tab5:
    render_regime(result, params)

with tab6:
    render_drake(result, params)
