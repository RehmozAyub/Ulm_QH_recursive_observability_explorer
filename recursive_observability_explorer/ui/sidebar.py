"""Sidebar builder — constructs the full Streamlit sidebar and returns
a populated ModelParams + initial conditions + active selections.
"""

from __future__ import annotations

from typing import Tuple

import json
import streamlit as st

from model.config import (
    ModelParams, BOUNDS, PARAM_GROUPS, PARAM_LABELS,
    params_to_json, params_from_json, params_to_dict,
)
from model.functions import F_REGISTRY, O_REGISTRY, E_REGISTRY, B_REGISTRY, X_REGISTRY, C_REGISTRY, S_REGISTRY
from model.stages import get_stage, stage_keys, STAGE_LABELS


def _clear_widget_state():
    """Clear all keys in session_state related to user overrides."""
    keys_to_clear = [
        "F_key_selector", "O_key_selector", "obs_mode_selector", "threshold_sign_selector",
        "E_key_selector", "B_key_selector", "X_key_selector", "C_key_selector", "S_key_selector",
        "I0_input", "R0_input", "O0_input", "n_points_input", "rtol_input", "atol_input",
        "time_varying_checkbox"
    ]
    for k in list(st.session_state.keys()):
        if k.startswith("slider_") or k in keys_to_clear:
            del st.session_state[k]


def build_sidebar() -> Tuple[ModelParams, Tuple[float, float, float]]:
    """Render the sidebar controls and return (ModelParams, y0).

    Uses Streamlit session state to preserve user edits while allowing
    preset resets.
    """
    st.sidebar.markdown("## 🎛️ Controls")

    # Load preset defaults into session state if not yet set
    if "_preset_params" not in st.session_state:
        default_params, default_y0 = get_stage("s3")
        st.session_state["_preset_params"] = params_to_dict(default_params)
        st.session_state["_preset_y0"] = default_y0

    base_dict = st.session_state["_preset_params"]
    base_y0 = st.session_state["_preset_y0"]

    # ------------------------------------------------------------------
    # Stage preset selector
    # ------------------------------------------------------------------
    st.sidebar.markdown("### Stage Presets")
    stage_options = {k: STAGE_LABELS[k] for k in stage_keys()}
    selected_stage = st.sidebar.selectbox(
        "Preset",
        options=list(stage_options.keys()),
        format_func=lambda k: stage_options[k],
        key="stage_selector",
    )

    col1, col2 = st.sidebar.columns(2)
    if col1.button("Apply preset", use_container_width=True):
        preset_params, preset_y0 = get_stage(selected_stage)
        preset_dict = params_to_dict(preset_params)
        
        # Identify current user overrides (values that differ from the current base_dict)
        slider_overrides = {}
        for pname in base_dict:
            key = f"slider_{pname}"
            if key in st.session_state:
                val = st.session_state[key]
                old_val = base_dict.get(pname)
                if old_val is not None and abs(val - old_val) > 1e-9:
                    slider_overrides[key] = val
                    
        other_overrides = {}
        if "F_key_selector" in st.session_state and st.session_state["F_key_selector"] != base_dict.get("F_key"):
            other_overrides["F_key_selector"] = st.session_state["F_key_selector"]
        if "O_key_selector" in st.session_state and st.session_state["O_key_selector"] != base_dict.get("O_key"):
            other_overrides["O_key_selector"] = st.session_state["O_key_selector"]
        if "obs_mode_selector" in st.session_state and st.session_state["obs_mode_selector"] != base_dict.get("obs_mode"):
            other_overrides["obs_mode_selector"] = st.session_state["obs_mode_selector"]
        if "threshold_sign_selector" in st.session_state and st.session_state["threshold_sign_selector"] != base_dict.get("threshold_sign"):
            other_overrides["threshold_sign_selector"] = st.session_state["threshold_sign_selector"]
        if "E_key_selector" in st.session_state and st.session_state["E_key_selector"] != base_dict.get("E_key"):
            other_overrides["E_key_selector"] = st.session_state["E_key_selector"]
        if "B_key_selector" in st.session_state and st.session_state["B_key_selector"] != base_dict.get("B_key"):
            other_overrides["B_key_selector"] = st.session_state["B_key_selector"]
        if "X_key_selector" in st.session_state and st.session_state["X_key_selector"] != base_dict.get("X_key"):
            other_overrides["X_key_selector"] = st.session_state["X_key_selector"]
        if "C_key_selector" in st.session_state and st.session_state["C_key_selector"] != base_dict.get("C_key"):
            other_overrides["C_key_selector"] = st.session_state["C_key_selector"]
        if "S_key_selector" in st.session_state and st.session_state["S_key_selector"] != base_dict.get("S_key"):
            other_overrides["S_key_selector"] = st.session_state["S_key_selector"]
        if "time_varying_checkbox" in st.session_state and st.session_state["time_varying_checkbox"] != base_dict.get("time_varying", False):
            other_overrides["time_varying_checkbox"] = st.session_state["time_varying_checkbox"]
            
        if "I0_input" in st.session_state and abs(st.session_state["I0_input"] - base_y0[0]) > 1e-9:
            other_overrides["I0_input"] = st.session_state["I0_input"]
        if "R0_input" in st.session_state and abs(st.session_state["R0_input"] - base_y0[1]) > 1e-9:
            other_overrides["R0_input"] = st.session_state["R0_input"]
        if "O0_input" in st.session_state and abs(st.session_state["O0_input"] - base_y0[2]) > 1e-9:
            other_overrides["O0_input"] = st.session_state["O0_input"]
            
        if "n_points_input" in st.session_state and st.session_state["n_points_input"] != base_dict.get("n_points"):
            other_overrides["n_points_input"] = st.session_state["n_points_input"]
        if "rtol_input" in st.session_state and abs(st.session_state["rtol_input"] - base_dict.get("rtol", 1e-6)) > 1e-12:
            other_overrides["rtol_input"] = st.session_state["rtol_input"]
        if "atol_input" in st.session_state and abs(st.session_state["atol_input"] - base_dict.get("atol", 1e-9)) > 1e-15:
            other_overrides["atol_input"] = st.session_state["atol_input"]

        # Reset widgets in session state so defaults are reloaded from the new preset base
        _clear_widget_state()
        
        # Set new preset as base
        st.session_state["_preset_params"] = preset_dict
        st.session_state["_preset_y0"] = preset_y0
        
        # Re-apply user overrides
        for k, v in slider_overrides.items():
            st.session_state[k] = v
        for k, v in other_overrides.items():
            st.session_state[k] = v
            
        st.rerun()

    if col2.button("Reset to preset", use_container_width=True):
        preset_params, preset_y0 = get_stage(selected_stage)
        # Clear widget keys to force reset to new base
        _clear_widget_state()
        st.session_state["_preset_params"] = params_to_dict(preset_params)
        st.session_state["_preset_y0"] = preset_y0
        st.rerun()

    time_varying = st.sidebar.checkbox(
        "Enable time-varying drivers",
        value=bool(base_dict.get("time_varying", False)),
        key="time_varying_checkbox",
        help="If enabled, drivers (A, A_rec, A_ref, Q) vary over time using illustrative profiles rather than remaining constant."
    )

    # ------------------------------------------------------------------
    # Function selectors
    # ------------------------------------------------------------------
    st.sidebar.markdown("### Function Selectors")

    F_key = st.sidebar.selectbox(
        "F(I) recursion type",
        options=list(F_REGISTRY.keys()),
        index=list(F_REGISTRY.keys()).index(base_dict.get("F_key", "saturating")),
        key="F_key_selector",
    )
    O_key = st.sidebar.selectbox(
        "O(I) observability model",
        options=list(O_REGISTRY.keys()),
        index=list(O_REGISTRY.keys()).index(base_dict.get("O_key", "peaked")),
        key="O_key_selector",
    )
    obs_mode = st.sidebar.selectbox(
        "Observability mode",
        options=["dynamic", "static"],
        index=0 if base_dict.get("obs_mode", "dynamic") == "dynamic" else 1,
        key="obs_mode_selector",
    )
    threshold_sign = st.sidebar.selectbox(
        "Threshold sign (sigmoid)",
        options=[1, -1],
        format_func=lambda x: "+1 (rising)" if x == 1 else "−1 (falling)",
        index=0 if base_dict.get("threshold_sign", 1) == 1 else 1,
        key="threshold_sign_selector",
    )
    E_key = st.sidebar.selectbox(
        "E_use (energy-use model)",
        options=list(E_REGISTRY.keys()),
        index=list(E_REGISTRY.keys()).index(base_dict.get("E_key", "linear")),
        key="E_key_selector",
    )
    B_key = st.sidebar.selectbox(
        "B_cast (broadcast model)",
        options=list(B_REGISTRY.keys()),
        index=list(B_REGISTRY.keys()).index(base_dict.get("B_key", "linear")),
        key="B_key_selector",
    )
    X_key = st.sidebar.selectbox(
        "X_expand (expansion model)",
        options=list(X_REGISTRY.keys()),
        index=list(X_REGISTRY.keys()).index(base_dict.get("X_key", "linear")),
        key="X_key_selector",
    )
    C_key = st.sidebar.selectbox(
        "C_compress (compression model)",
        options=list(C_REGISTRY.keys()),
        index=list(C_REGISTRY.keys()).index(base_dict.get("C_key", "linear")),
        key="C_key_selector",
    )
    S_key = st.sidebar.selectbox(
        "S_stealth (stealth model)",
        options=list(S_REGISTRY.keys()),
        index=list(S_REGISTRY.keys()).index(base_dict.get("S_key", "linear")),
        key="S_key_selector",
    )

    # ------------------------------------------------------------------
    # Initial conditions
    # ------------------------------------------------------------------
    st.sidebar.markdown("### Initial Conditions")
    I0 = st.sidebar.number_input("I₀", min_value=0.0, max_value=100.0,
                                  value=float(base_y0[0]), step=0.1, key="I0_input")
    R0 = st.sidebar.number_input("R₀", min_value=0.0, max_value=100.0,
                                  value=float(base_y0[1]), step=0.1, key="R0_input")
    O0 = st.sidebar.number_input("O₀", min_value=0.0, max_value=100.0,
                                  value=float(base_y0[2]), step=0.1, key="O0_input")

    # ------------------------------------------------------------------
    # Parameter sliders (grouped)
    # ------------------------------------------------------------------
    param_overrides = {}
    for group_name, param_names in PARAM_GROUPS.items():
        with st.sidebar.expander(group_name, expanded=False):
            for pname in param_names:
                if pname not in BOUNDS:
                    continue
                lo, hi = BOUNDS[pname]
                default_val = base_dict.get(pname, ModelParams.__dataclass_fields__[pname].default)
                label = PARAM_LABELS.get(pname, pname)
                # Determine step size
                span = hi - lo
                step = 0.01 if span <= 1.0 else (0.1 if span <= 10.0 else 1.0)
                val = st.slider(
                    label,
                    min_value=float(lo),
                    max_value=float(hi),
                    value=float(default_val),
                    step=step,
                    key=f"slider_{pname}",
                )
                param_overrides[pname] = val

    # ------------------------------------------------------------------
    # Solver settings
    # ------------------------------------------------------------------
    with st.sidebar.expander("Solver settings", expanded=False):
        n_points = st.number_input(
            "n_points (output resolution)",
            min_value=100, max_value=10000,
            value=int(base_dict.get("n_points", 1000)),
            step=100, key="n_points_input",
        )
        rtol = st.number_input(
            "rtol", min_value=1e-12, max_value=1e-2,
            value=float(base_dict.get("rtol", 1e-6)),
            format="%.1e", key="rtol_input",
        )
        atol = st.number_input(
            "atol", min_value=1e-15, max_value=1e-3,
            value=float(base_dict.get("atol", 1e-9)),
            format="%.1e", key="atol_input",
        )

    # ------------------------------------------------------------------
    # JSON import/export
    # ------------------------------------------------------------------
    st.sidebar.markdown("### Import / Export")
    json_col1, json_col2 = st.sidebar.columns(2)

    # Export
    export_params = ModelParams(
        **{**base_dict, **param_overrides,
           "F_key": F_key, "O_key": O_key,
           "obs_mode": obs_mode, "threshold_sign": threshold_sign,
           "E_key": E_key, "B_key": B_key, "X_key": X_key, "C_key": C_key, "S_key": S_key,
           "n_points": n_points, "rtol": rtol, "atol": atol,
           "time_varying": time_varying}
    )
    json_str = params_to_json(export_params)
    json_col1.download_button(
        "⬇ Download JSON",
        data=json_str,
        file_name="rof_params.json",
        mime="application/json",
        use_container_width=True,
    )

    # Import
    uploaded = json_col2.file_uploader("⬆ Upload JSON", type=["json"], key="json_upload")
    if uploaded is not None:
        try:
            imported = params_from_json(uploaded.read().decode())
            st.session_state["_preset_params"] = params_to_dict(imported)
            st.session_state["_preset_y0"] = (I0, R0, O0)
            st.sidebar.success("Parameters loaded!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Import failed: {e}")

    # ------------------------------------------------------------------
    # Assemble final ModelParams
    # ------------------------------------------------------------------
    final_dict = {
        **base_dict,
        **param_overrides,
        "F_key": F_key,
        "O_key": O_key,
        "obs_mode": obs_mode,
        "threshold_sign": threshold_sign,
        "E_key": E_key,
        "B_key": B_key,
        "X_key": X_key,
        "C_key": C_key,
        "S_key": S_key,
        "n_points": n_points,
        "rtol": rtol,
        "atol": atol,
        "time_varying": time_varying,
    }
    params = ModelParams(**{
        k: v for k, v in final_dict.items()
        if k in ModelParams.__dataclass_fields__
    })
    y0 = (I0, R0, O0)

    return params, y0
