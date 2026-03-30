"""
╔══════════════════════════════════════════════════════════════════╗
║         TORNADO SIMULATOR — Rankine Vortex + Updraft Model       ║
║         v3.0 — SIL 2026 Science Project — Maxi                  ║
║                                                                  ║
║  HOW TO RUN:                                                     ║
║    1. pip install streamlit plotly numpy                         ║
║    2. streamlit run tornado_sim.py                               ║
║    3. Open http://localhost:8501                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tornado Simulator",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"] { background-color: #070b14; color: #c8d8f0; }

h1 {
    font-family: 'Orbitron', monospace !important;
    font-weight: 900 !important; font-size: 2.4rem !important;
    letter-spacing: 0.12em !important;
    background: linear-gradient(135deg, #4af0ff 0%, #7b5fff 50%, #ff6b35 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0 !important;
}
h2, h3 {
    font-family: 'Orbitron', monospace !important; font-weight: 700 !important;
    color: #4af0ff !important; letter-spacing: 0.08em !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1020 0%, #0d1525 100%) !important;
    border-right: 1px solid #1a2a4a;
}
[data-testid="stSidebar"] label {
    font-family: 'Share Tech Mono', monospace !important;
    color: #8ab4d8 !important; font-size: 0.85rem !important;
}
[data-testid="metric-container"] {
    background: rgba(74,240,255,0.05) !important;
    border: 1px solid rgba(74,240,255,0.2) !important;
    border-radius: 8px !important; padding: 12px !important;
}
[data-testid="metric-container"] label {
    font-family: 'Share Tech Mono', monospace !important;
    color: #8ab4d8 !important; font-size: 0.75rem !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    color: #4af0ff !important; font-size: 1.3rem !important;
}
hr { border-color: #1a2a4a !important; }
[data-testid="stPlotlyChart"] {
    border: 1px solid #1a2a4a; border-radius: 12px; overflow: hidden;
}
.fujita-badge {
    display: inline-block;
    font-family: 'Orbitron', monospace;
    font-size: 2rem; font-weight: 900;
    padding: 12px 28px;
    border-radius: 10px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ─── FUJITA SCALE DATA ──────────────────────────────────────────────────────────
FUJITA = [
    {"cat": "F0", "v_min": 0,   "v_max": 32,  "color": "#6ee7b7", "bg": "rgba(110,231,183,0.15)",
     "label": "Débil",      "damage": "Daño leve. Ramas rotas, carteles caídos, daño superficial en techos."},
    {"cat": "F1", "v_min": 33,  "v_max": 49,  "color": "#fbbf24", "bg": "rgba(251,191,36,0.15)",
     "label": "Moderado",   "damage": "Daño moderado. Techos dañados, autos desplazados, árboles derribados."},
    {"cat": "F2", "v_min": 50,  "v_max": 69,  "color": "#f97316", "bg": "rgba(249,115,22,0.15)",
     "label": "Significativo", "damage": "Daño considerable. Techos arrancados, casas de madera destruidas, autos volcados."},
    {"cat": "F3", "v_min": 70,  "v_max": 92,  "color": "#ef4444", "bg": "rgba(239,68,68,0.15)",
     "label": "Severo",     "damage": "Daño severo. Paredes derrumbadas, trenes volcados, árboles desarraigados."},
    {"cat": "F4", "v_min": 93,  "v_max": 116, "color": "#dc2626", "bg": "rgba(220,38,38,0.15)",
     "label": "Devastador", "damage": "Daño devastador. Casas bien construidas destruidas totalmente, estructuras grandes dañadas."},
    {"cat": "F5", "v_min": 117, "v_max": 999, "color": "#9b1c1c", "bg": "rgba(155,28,28,0.15)",
     "label": "Increíble",  "damage": "Daño increíble. Estructuras de hormigón destruidas, autos volando cientos de metros."},
]

# Preset: Tornado F1 Santa Rosa del Monday, Paraguay — Diciembre 2025
SANTA_ROSA_PRESET = {
    "R_c": 120,
    "max_wind": 45,
    "updraft_strength": 25,
    "inflow_angle": 18,
    "n_particles": 2500,
    "max_height": 1800,
}

def get_fujita(v_ms):
    for f in FUJITA:
        if f["v_min"] <= v_ms <= f["v_max"]:
            return f
    return FUJITA[-1]


# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌪️ VORTEX CONTROLS")
    st.markdown("---")

    # Preset button
    use_preset = st.button("⚡ Preset: Santa Rosa del Monday F1",
                           width="stretch")
    if use_preset:
        for k, v in SANTA_ROSA_PRESET.items():
            st.session_state[k] = v
    st.markdown("---")

    def sv(key, default):
        return st.session_state.get(key, default)

    st.markdown("### STRUCTURE")
    R_c = st.slider("Core Radius (R_c) [m]", 50, 500,
                    sv("R_c", 150), 10, key="R_c")
    max_wind = st.slider("Max Wind Speed [m/s]", 20, 150,
                         sv("max_wind", 70), 5, key="max_wind")

    st.markdown("### DYNAMICS")
    updraft_strength = st.slider("Updraft Strength [m/s]", 5, 80,
                                 sv("updraft_strength", 30), 5, key="updraft_strength")
    inflow_angle = st.slider("Inflow Angle [degrees]", 5, 45,
                             sv("inflow_angle", 20), 1, key="inflow_angle")

    st.markdown("### VISUALIZATION")
    n_particles = st.slider("Number of Particles", 500, 5000,
                            sv("n_particles", 2000), 100, key="n_particles")
    max_height = st.slider("Simulation Height [m]", 500, 5000, 2000, 100)
    color_mode = st.selectbox("Color By",
        ["Speed (total)", "Tangential velocity", "Vertical velocity", "Radius"])

    st.markdown("### ANIMATION")
    n_frames   = st.slider("Animation Frames", 20, 80, 40, 5)
    anim_speed = st.slider("Frame Delay [ms]", 30, 200, 70, 10)

    st.markdown("### PARTICLE TRACKER")
    track_r     = st.slider("Tracked particle — Radius [m]", 10, 500, 100, 10)
    track_theta = st.slider("Tracked particle — Start angle [deg]", 0, 360, 45, 5)
    track_steps = st.slider("Trajectory steps", 20, 200, 80, 10)

    st.markdown("---")
    st.caption("Rankine Vortex Model + Updraft\nMaxi — SIL 2026 Science Project")


# ─── HELPERS ────────────────────────────────────────────────────────────────────
def axis_style(label):
    return dict(
        title=dict(text=label,
                   font=dict(family="Share Tech Mono", color="#4af0ff", size=11)),
        tickfont=dict(family="Share Tech Mono", color="#4a6a8a", size=9),
        gridcolor="#0f1e30", showbackground=True,
        backgroundcolor="rgba(7,11,20,0.5)", zerolinecolor="#1a2a4a",
    )

def axis_2d(label):
    return dict(
        title=dict(text=label,
                   font=dict(family="Share Tech Mono", color="#4af0ff", size=12)),
        tickfont=dict(family="Share Tech Mono", color="#4a6a8a", size=10),
        gridcolor="#0f1e30", zerolinecolor="#1a2a4a",
        showgrid=True,
    )

def rankine_vtheta(r_arr, R_c, max_wind):
    return np.where(r_arr <= R_c,
                    max_wind * (r_arr / R_c),
                    max_wind * (R_c / r_arr))


# ─── PHYSICS FUNCTIONS ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def simulate_tornado(R_c, max_wind, updraft_strength, inflow_angle, n_particles, max_height):
    rng   = np.random.default_rng(seed=42)
    r_u   = rng.uniform(0.01*R_c, 3.0*R_c, n_particles//2)
    r_l   = np.clip(rng.lognormal(np.log(R_c), 0.6, n_particles - n_particles//2),
                    0.01*R_c, 3.0*R_c)
    r     = np.concatenate([r_u, r_l])
    theta = rng.uniform(0, 2*np.pi, n_particles)
    z     = rng.uniform(0, max_height, n_particles)

    V_theta = rankine_vtheta(r, R_c, max_wind)
    alpha   = np.radians(inflow_angle)
    V_r     = -V_theta * np.tan(alpha) * np.exp(-z / (max_height*0.6))
    V_z     = updraft_strength * np.exp(-0.5*(r/R_c)**2) * (0.5 + 0.5*z/max_height)

    dt  = 1.0
    V_x = V_r*np.cos(theta) - V_theta*np.sin(theta)
    V_y = V_r*np.sin(theta) + V_theta*np.cos(theta)
    x   = r*np.cos(theta) + V_x*dt*0.3
    y   = r*np.sin(theta) + V_y*dt*0.3
    z_d = z + V_z*dt*0.5
    return x, y, z_d, r, V_theta, V_r, V_z, np.sqrt(V_theta**2+V_r**2+V_z**2)


@st.cache_data(show_spinner=False)
def build_animation_frames(R_c, max_wind, updraft_strength, inflow_angle,
                            n_particles, max_height, n_frames):
    rng  = np.random.default_rng(seed=7)
    n    = n_particles
    r0   = np.concatenate([
        rng.uniform(0.01*R_c, 3.0*R_c, n//2),
        np.clip(rng.lognormal(np.log(R_c), 0.6, n-n//2), 0.01*R_c, 3.0*R_c)
    ])
    t0   = rng.uniform(0, 2*np.pi, n)
    px, py = r0*np.cos(t0), r0*np.sin(t0)
    pz   = rng.uniform(0, max_height, n)
    alpha = np.radians(inflow_angle)
    dt, frames = 0.9, []

    for _ in range(n_frames):
        rc    = np.maximum(np.sqrt(px**2+py**2), 1.0)
        tc    = np.arctan2(py, px)
        V_th  = rankine_vtheta(rc, R_c, max_wind)
        V_r   = -V_th*np.tan(alpha)*np.exp(-pz/(max_height*0.6))
        V_z   = updraft_strength*np.exp(-0.5*(rc/R_c)**2)*(0.5+0.5*pz/max_height)
        Vx    = V_r*np.cos(tc) - V_th*np.sin(tc)
        Vy    = V_r*np.sin(tc) + V_th*np.cos(tc)
        px += Vx*dt; py += Vy*dt; pz += V_z*dt
        ex = pz > max_height
        if ex.sum():
            nt = rng.uniform(0, 2*np.pi, ex.sum())
            pz[ex] = rng.uniform(0, max_height*0.05, ex.sum())
            px[ex] = r0[ex]*np.cos(nt); py[ex] = r0[ex]*np.sin(nt)
        frames.append((px.copy(), py.copy(), pz.copy(),
                       np.sqrt(Vx**2+Vy**2+V_z**2).copy()))
    return frames


@st.cache_data(show_spinner=False)
def compute_trajectory(R_c, max_wind, updraft_strength, inflow_angle,
                       max_height, r_start, theta_deg, steps):
    """Track a single particle through the vortex field."""
    alpha = np.radians(inflow_angle)
    dt    = 1.2
    th    = np.radians(theta_deg)
    px, py, pz = r_start*np.cos(th), r_start*np.sin(th), 0.0
    xs, ys, zs, speeds = [px], [py], [pz], []

    for _ in range(steps):
        rc  = max(np.sqrt(px**2+py**2), 1.0)
        tc  = np.arctan2(py, px)
        Vth = float(rankine_vtheta(np.array([rc]), R_c, max_wind)[0])
        Vr  = -Vth*np.tan(alpha)*np.exp(-pz/(max_height*0.6))
        Vz  = updraft_strength*np.exp(-0.5*(rc/R_c)**2)*(0.5+0.5*pz/max_height)
        Vx  = Vr*np.cos(tc) - Vth*np.sin(tc)
        Vy  = Vr*np.sin(tc) + Vth*np.cos(tc)
        px += Vx*dt; py += Vy*dt; pz += Vz*dt
        if pz > max_height: break
        xs.append(px); ys.append(py); zs.append(pz)
        speeds.append(np.sqrt(Vx**2+Vy**2+Vz**2))

    return np.array(xs), np.array(ys), np.array(zs), np.array(speeds if speeds else [0])


# ─── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("# 🌪️ TORNADO SIMULATOR")
st.markdown(
    "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.85rem;'>"
    "Rankine Vortex Model · Interactive 3D Particle Field · Real-Time Parameter Control"
    "</span>", unsafe_allow_html=True)
st.markdown("---")

with st.spinner("Solving vortex dynamics..."):
    x, y, z, r, V_theta, V_r, V_z, V_total = simulate_tornado(
        R_c, max_wind, updraft_strength, inflow_angle, n_particles, max_height)

# Fujita classification
fuj = get_fujita(max_wind)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Core Radius",  f"{R_c} m")
c2.metric("Max Wind",     f"{max_wind} m/s")
c3.metric("Updraft",      f"{updraft_strength} m/s")
c4.metric("Inflow Angle", f"{inflow_angle} deg")
c5.metric("Particles",    f"{n_particles:,}")
c6.metric("Fujita Scale", fuj["cat"])

st.markdown("<br>", unsafe_allow_html=True)


# ─── TABS ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📡  3D VIEW",
    "▶  ANIMATION",
    "📊  VELOCITY PROFILES",
    "🗺️  TOP-DOWN VIEW",
    "🎯  PARTICLE TRACKER",
    "ℹ️  ACERCA DE",
])


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 1 — STATIC 3D + FUJITA PANEL
# ══════════════════════════════════════════════════════════════════════════════════
with tab1:
    col_plot, col_info = st.columns([3, 1])

    with col_info:
        st.markdown("### FUJITA SCALE")
        for f in FUJITA:
            is_current = (f["cat"] == fuj["cat"])
            border = f"3px solid {f['color']}" if is_current else f"1px solid {f['color']}33"
            scale  = "1.04" if is_current else "1"
            st.markdown(
                f"""<div style='
                    background:{f["bg"]};
                    border:{border};
                    border-radius:8px;
                    padding:8px 12px;
                    margin-bottom:6px;
                    transform:scale({scale});
                    transition:transform 0.2s;
                '>
                <span style='font-family:Orbitron,monospace;font-size:1.1rem;
                             font-weight:900;color:{f["color"]}'>{f["cat"]}</span>
                <span style='font-family:Share Tech Mono;font-size:0.78rem;
                             color:#8ab4d8;margin-left:8px'>{f["label"]}</span><br>
                <span style='font-family:Share Tech Mono;font-size:0.72rem;
                             color:#4a6a8a'>{f["v_min"]}–{f["v_max"]} m/s</span>
                {"<br><span style='font-family:Share Tech Mono;font-size:0.7rem;color:#c8d8f0'>" + f['damage'] + "</span>" if is_current else ""}
                </div>""",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:rgba(74,240,255,0.07);border:1px solid #1a2a4a;"
            f"border-radius:8px;padding:10px;font-family:Share Tech Mono;font-size:0.78rem;color:#8ab4d8'>"
            f"<b style='color:#4af0ff'>Santa Rosa del Monday</b><br>"
            f"Diciembre 2025 · Paraguay<br>"
            f"Clasificacion: <b style='color:{FUJITA[1]['color']}'>F1</b><br>"
            f"V_max estimado: ~40-50 m/s<br>"
            f"Radio del core: ~100-150 m<br>"
            f"Duracion: ~8 min<br>"
            f"Trayectoria: ~12 km NE"
            f"</div>", unsafe_allow_html=True)

    with col_plot:
        color_map = {
            "Speed (total)":       (V_total, "Plasma",  "Total Speed [m/s]"),
            "Tangential velocity": (V_theta, "Viridis", "Tangential V [m/s]"),
            "Vertical velocity":   (V_z,     "Cividis", "Vertical V [m/s]"),
            "Radius":              (r,       "Turbo",   "Radius from Core [m]"),
        }
        c_data, colorscale, c_label = color_map[color_mode]

        fig = go.Figure()
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode="markers",
            marker=dict(size=1.8, color=c_data, colorscale=colorscale, opacity=0.85,
                        colorbar=dict(
                            title=dict(text=c_label, side="right",
                                       font=dict(family="Share Tech Mono", color="#8ab4d8", size=11)),
                            thickness=14, len=0.7, x=1.02,
                            tickfont=dict(family="Share Tech Mono", color="#8ab4d8", size=10),
                        )),
            name="Air parcels",
            hovertemplate="x:%{x:.0f}m  y:%{y:.0f}m  z:%{z:.0f}m<extra></extra>",
        ))
        z_ax = np.linspace(0, max_height, 80)
        fig.add_trace(go.Scatter3d(
            x=np.zeros(80), y=np.zeros(80), z=z_ax, mode="lines",
            line=dict(color="rgba(74,240,255,0.7)", width=3),
            name="Vortex axis", hoverinfo="skip",
        ))
        phi = np.linspace(0, 2*np.pi, 120)
        fig.add_trace(go.Scatter3d(
            x=R_c*np.cos(phi), y=R_c*np.sin(phi), z=np.zeros(120), mode="lines",
            line=dict(color="rgba(255,107,53,0.8)", width=2, dash="dot"),
            name=f"Core radius ({R_c} m)", hoverinfo="skip",
        ))
        fig.update_layout(
            paper_bgcolor="#070b14", plot_bgcolor="#070b14",
            font=dict(family="Share Tech Mono", color="#8ab4d8"),
            margin=dict(l=0, r=60, t=30, b=0), height=620,
            legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a",
                        borderwidth=1, font=dict(family="Share Tech Mono", size=11, color="#8ab4d8"),
                        x=0.01, y=0.99),
            scene=dict(bgcolor="#070b14",
                       xaxis=axis_style("X [m]"), yaxis=axis_style("Y [m]"),
                       zaxis=axis_style("Height [m]"),
                       camera=dict(eye=dict(x=1.6, y=1.6, z=0.8), up=dict(x=0, y=0, z=1)),
                       aspectmode="manual", aspectratio=dict(x=1, y=1, z=1.4)),
        )
        st.plotly_chart(fig, width="stretch",
                        config={"displayModeBar": True, "displaylogo": False})


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANIMATION
# ══════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(
        "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.82rem'>"
        "Particulas advectadas frame a frame  |  Rotacion + Updraft combinados  |  "
        "Presiona PLAY para iniciar  |  Podes rotar mientras anima"
        "</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner(f"Generando {n_frames} frames..."):
        anim_frames = build_animation_frames(
            R_c, max_wind, updraft_strength, inflow_angle,
            n_particles, max_height, n_frames)

    px0, py0, pz0, spd0 = anim_frames[0]
    phi2 = np.linspace(0, 2*np.pi, 120)
    vcap  = float(max_wind) * 1.2

    fig_a = go.Figure(
        data=[
            go.Scatter3d(x=px0, y=py0, z=pz0, mode="markers",
                marker=dict(size=1.6, color=spd0, colorscale="Plasma",
                            cmin=0, cmax=vcap, opacity=0.88,
                            colorbar=dict(
                                title=dict(text="Speed [m/s]", side="right",
                                           font=dict(family="Share Tech Mono", color="#8ab4d8", size=11)),
                                thickness=14, len=0.65, x=1.02,
                                tickfont=dict(family="Share Tech Mono", color="#8ab4d8", size=10),
                            )),
                name="Debris", hoverinfo="skip"),
            go.Scatter3d(x=[0,0], y=[0,0], z=[0,max_height], mode="lines",
                line=dict(color="rgba(74,240,255,0.6)", width=3),
                name="Vortex axis", hoverinfo="skip"),
            go.Scatter3d(x=R_c*np.cos(phi2), y=R_c*np.sin(phi2), z=np.zeros(120),
                mode="lines", line=dict(color="rgba(255,107,53,0.7)", width=2, dash="dot"),
                name=f"Core ({R_c} m)", hoverinfo="skip"),
        ],
        frames=[
            go.Frame(
                data=[go.Scatter3d(x=px, y=py, z=pz, mode="markers",
                    marker=dict(size=1.6, color=spd, colorscale="Plasma",
                                cmin=0, cmax=vcap, opacity=0.88))],
                traces=[0], name=str(i))
            for i, (px, py, pz, spd) in enumerate(anim_frames)
        ],
    )
    fig_a.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor="#070b14",
        font=dict(family="Share Tech Mono", color="#8ab4d8"),
        margin=dict(l=0, r=60, t=30, b=60), height=700,
        legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a", borderwidth=1,
                    font=dict(family="Share Tech Mono", size=11, color="#8ab4d8"),
                    x=0.01, y=0.99),
        scene=dict(bgcolor="#070b14",
                   xaxis=axis_style("X [m]"), yaxis=axis_style("Y [m]"),
                   zaxis=axis_style("Height [m]"),
                   camera=dict(eye=dict(x=1.7, y=1.7, z=0.7), up=dict(x=0, y=0, z=1)),
                   aspectmode="manual", aspectratio=dict(x=1, y=1, z=1.4)),
        updatemenus=[dict(
            type="buttons", showactive=False,
            y=-0.05, x=0.5, xanchor="center",
            bgcolor="#0d1525", bordercolor="#1a2a4a",
            font=dict(family="Orbitron", color="#4af0ff", size=11),
            buttons=[
                dict(label="  PLAY", method="animate",
                     args=[None, {"frame": {"duration": anim_speed, "redraw": True},
                                  "fromcurrent": True, "transition": {"duration": 0},
                                  "mode": "immediate"}]),
                dict(label="  PAUSE", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate", "transition": {"duration": 0}}]),
            ])],
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="Frame: ",
                              font=dict(family="Share Tech Mono", color="#4af0ff", size=11)),
            pad=dict(t=10, b=10, l=20, r=20),
            bgcolor="#0d1525", bordercolor="#1a2a4a", tickcolor="#1a2a4a",
            font=dict(family="Share Tech Mono", color="#4a6a8a", size=8),
            steps=[dict(
                args=[[str(i)], {"frame": {"duration": anim_speed, "redraw": True},
                                 "mode": "immediate", "transition": {"duration": 0}}],
                label=str(i) if i % 5 == 0 else "", method="animate")
                for i in range(n_frames)
            ])],
    )
    st.plotly_chart(fig_a, width="stretch",
                    config={"displayModeBar": True, "displaylogo": False})


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 3 — VELOCITY PROFILES (Rankine curve + vertical profile)
# ══════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### PERFIL DE VELOCIDAD RADIAL — Curva de Rankine")
    st.markdown(
        "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.82rem'>"
        "Muestra cómo cambia la velocidad tangencial V_θ con la distancia al centro. "
        "El pico ocurre exactamente en r = R_c (radio del core)."
        "</span>", unsafe_allow_html=True)

    r_arr  = np.linspace(1, 3.5*R_c, 600)
    vt_arr = rankine_vtheta(r_arr, R_c, max_wind)

    # Compare with Santa Rosa preset
    sr    = SANTA_ROSA_PRESET
    r_sr  = np.linspace(1, 3.5*sr["R_c"], 600)
    vt_sr = rankine_vtheta(r_sr, sr["R_c"], sr["max_wind"])

    fig_r = go.Figure()

    # Current config
    fig_r.add_trace(go.Scatter(
        x=r_arr, y=vt_arr, mode="lines",
        line=dict(color="#4af0ff", width=2.5),
        name=f"Config actual (R_c={R_c}m, V={max_wind}m/s)",
        hovertemplate="r=%{x:.0f} m<br>V_θ=%{y:.1f} m/s<extra></extra>",
    ))

    # Santa Rosa F1
    fig_r.add_trace(go.Scatter(
        x=r_sr, y=vt_sr, mode="lines",
        line=dict(color="#fbbf24", width=2, dash="dash"),
        name="Santa Rosa del Monday F1 (estimado)",
        hovertemplate="r=%{x:.0f} m<br>V_θ=%{y:.1f} m/s<extra></extra>",
    ))

    # Vertical lines at R_c
    fig_r.add_vline(x=R_c, line=dict(color="#4af0ff", width=1, dash="dot"),
                    annotation_text=f"R_c = {R_c} m",
                    annotation_font=dict(family="Share Tech Mono", color="#4af0ff", size=11))
    fig_r.add_vline(x=sr["R_c"], line=dict(color="#fbbf24", width=1, dash="dot"),
                    annotation_text=f"R_c Santa Rosa = {sr['R_c']} m",
                    annotation_font=dict(family="Share Tech Mono", color="#fbbf24", size=11))

    # Fujita zones as horizontal bands
    for f in FUJITA:
        fig_r.add_hrect(y0=f["v_min"], y1=min(f["v_max"], max_wind*1.5),
                        fillcolor=f["color"], opacity=0.06, line_width=0,
                        annotation_text=f["cat"],
                        annotation_position="right",
                        annotation_font=dict(family="Orbitron", color=f["color"], size=10))

    fig_r.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor="#070b14",
        font=dict(family="Share Tech Mono", color="#8ab4d8"),
        height=380, margin=dict(l=20, r=80, t=30, b=20),
        legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a", borderwidth=1,
                    font=dict(family="Share Tech Mono", size=11, color="#8ab4d8")),
        xaxis=axis_2d("Radio desde el centro [m]"),
        yaxis=axis_2d("Velocidad tangencial V_θ [m/s]"),
    )
    st.plotly_chart(fig_r, width="stretch",
                    config={"displayModeBar": False, "displaylogo": False})

    st.markdown("---")
    st.markdown("### PERFIL VERTICAL DE UPDRAFT")
    st.markdown(
        "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.82rem'>"
        "Velocidad vertical V_z en el eje del core (r=0) vs. altura. "
        "Muestra el efecto chimenea — el updraft se acelera con la altitud."
        "</span>", unsafe_allow_html=True)

    z_arr  = np.linspace(0, max_height, 400)
    # At core center (r→0, Gaussian=1)
    vz_core = updraft_strength * 1.0 * (0.5 + 0.5 * z_arr / max_height)
    # At r = R_c (Gaussian = exp(-0.5))
    vz_rc   = updraft_strength * np.exp(-0.5) * (0.5 + 0.5 * z_arr / max_height)

    fig_z = go.Figure()
    fig_z.add_trace(go.Scatter(
        x=vz_core, y=z_arr, mode="lines",
        line=dict(color="#4af0ff", width=2.5),
        name="En el eje central (r=0)",
        hovertemplate="V_z=%{x:.1f} m/s<br>z=%{y:.0f} m<extra></extra>",
    ))
    fig_z.add_trace(go.Scatter(
        x=vz_rc, y=z_arr, mode="lines",
        line=dict(color="#7b5fff", width=2, dash="dash"),
        name=f"En r = R_c ({R_c} m)",
        hovertemplate="V_z=%{x:.1f} m/s<br>z=%{y:.0f} m<extra></extra>",
    ))
    fig_z.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor="#070b14",
        font=dict(family="Share Tech Mono", color="#8ab4d8"),
        height=340, margin=dict(l=20, r=40, t=30, b=20),
        legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a", borderwidth=1,
                    font=dict(family="Share Tech Mono", size=11, color="#8ab4d8")),
        xaxis=axis_2d("Velocidad vertical V_z [m/s]"),
        yaxis=axis_2d("Altura [m]"),
    )
    st.plotly_chart(fig_z, width="stretch",
                    config={"displayModeBar": False, "displaylogo": False})


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 4 — TOP-DOWN VIEW (vista desde arriba)
# ══════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### CORTE TRANSVERSAL — Vista desde arriba")
    st.markdown(
        "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.82rem'>"
        "Proyección XY de las partículas (planta). Muestra el patrón de espiral del inflow "
        "y la concentración de partículas en el core. Color = velocidad total."
        "</span>", unsafe_allow_html=True)

    fig_top = go.Figure()

    # Particle scatter (top view)
    fig_top.add_trace(go.Scatter(
        x=x, y=y, mode="markers",
        marker=dict(size=2.5, color=V_total, colorscale="Plasma", opacity=0.7,
                    colorbar=dict(
                        title=dict(text="Speed [m/s]", side="right",
                                   font=dict(family="Share Tech Mono", color="#8ab4d8", size=11)),
                        thickness=14,
                        tickfont=dict(family="Share Tech Mono", color="#8ab4d8", size=10),
                    )),
        name="Air parcels",
        hovertemplate="x:%{x:.0f}m  y:%{y:.0f}m<extra></extra>",
    ))

    # Core radius circle
    phi_c = np.linspace(0, 2*np.pi, 200)
    fig_top.add_trace(go.Scatter(
        x=R_c*np.cos(phi_c), y=R_c*np.sin(phi_c), mode="lines",
        line=dict(color="rgba(255,107,53,0.9)", width=2, dash="dot"),
        name=f"Core radius ({R_c} m)",
    ))

    # 2× R_c circle
    fig_top.add_trace(go.Scatter(
        x=2*R_c*np.cos(phi_c), y=2*R_c*np.sin(phi_c), mode="lines",
        line=dict(color="rgba(74,240,255,0.3)", width=1, dash="dot"),
        name=f"2× Core radius ({2*R_c} m)",
    ))

    # Streamlines — a few spiral arrows showing inflow direction
    alpha = np.radians(inflow_angle)
    for th_start in np.linspace(0, 2*np.pi, 8, endpoint=False):
        r_s = 2.8 * R_c
        for _ in range(60):
            rc_s = max(r_s, 1.0)
            Vth_s = float(rankine_vtheta(np.array([rc_s]), R_c, max_wind)[0])
            Vr_s  = -Vth_s * np.tan(alpha)
            dth   = (Vth_s / rc_s) * 0.8
            dr    = Vr_s * 0.8
            th_start += dth; r_s += dr
            if r_s < R_c * 0.3: break

    # Eye marker
    fig_top.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=dict(size=10, color="#4af0ff", symbol="circle-open", line=dict(width=2)),
        name="Vortex eye",
    ))

    fig_top.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor="#070b14",
        font=dict(family="Share Tech Mono", color="#8ab4d8"),
        height=580, margin=dict(l=20, r=80, t=30, b=20),
        legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a", borderwidth=1,
                    font=dict(family="Share Tech Mono", size=11, color="#8ab4d8")),
        xaxis=dict(**axis_2d("X [m]"), scaleanchor="y", scaleratio=1, zeroline=True),
        yaxis=dict(**axis_2d("Y [m]"), zeroline=True),
    )
    st.plotly_chart(fig_top, width="stretch",
                    config={"displayModeBar": True, "displaylogo": False})

    # Zone info
    st.markdown("---")
    ca, cb, cc = st.columns(3)
    with ca:
        st.markdown(
            f"<div style='background:rgba(255,107,53,0.1);border:1px solid rgba(255,107,53,0.4);"
            f"border-radius:8px;padding:10px;font-family:Share Tech Mono;font-size:0.8rem;color:#8ab4d8'>"
            f"<b style='color:#ff6b35'>ZONA CORE</b><br>"
            f"r &lt; {R_c} m<br>"
            f"Rotacion solida. Velocidad crece linealmente.<br>"
            f"V_max en borde = {max_wind} m/s"
            f"</div>", unsafe_allow_html=True)
    with cb:
        st.markdown(
            f"<div style='background:rgba(123,95,255,0.1);border:1px solid rgba(123,95,255,0.4);"
            f"border-radius:8px;padding:10px;font-family:Share Tech Mono;font-size:0.8rem;color:#8ab4d8'>"
            f"<b style='color:#7b5fff'>ZONA TRANSICION</b><br>"
            f"r = {R_c}–{2*R_c} m<br>"
            f"Maximo de velocidad. Pared del vortex.<br>"
            f"Mayor intensidad de dano."
            f"</div>", unsafe_allow_html=True)
    with cc:
        st.markdown(
            f"<div style='background:rgba(74,240,255,0.07);border:1px solid rgba(74,240,255,0.2);"
            f"border-radius:8px;padding:10px;font-family:Share Tech Mono;font-size:0.8rem;color:#8ab4d8'>"
            f"<b style='color:#4af0ff'>ZONA EXTERIOR</b><br>"
            f"r &gt; {2*R_c} m<br>"
            f"Decaimiento irrotacional (1/r).<br>"
            f"Inflow espiral hacia el centro."
            f"</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 5 — SINGLE PARTICLE TRAJECTORY
# ══════════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### TRAYECTORIA DE PARTICULA INDIVIDUAL")
    st.markdown(
        "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.82rem'>"
        "Sigue una sola particula desde su posicion inicial hasta que sale por la cima. "
        "Muestra la helice caracteristica del vortice — espiral + ascenso combinados. "
        "Ajusta el radio y angulo inicial en el sidebar."
        "</span>", unsafe_allow_html=True)

    tx, ty, tz, tspeeds = compute_trajectory(
        R_c, max_wind, updraft_strength, inflow_angle,
        max_height, track_r, track_theta, track_steps)

    fig_tr = go.Figure()

    # Background cloud (faint)
    fig_tr.add_trace(go.Scatter3d(
        x=x[::4], y=y[::4], z=z[::4], mode="markers",
        marker=dict(size=1.2, color="#1a2a4a", opacity=0.3),
        name="Background field", hoverinfo="skip",
    ))

    # Trajectory line
    fig_tr.add_trace(go.Scatter3d(
        x=tx, y=ty, z=tz, mode="lines+markers",
        line=dict(color="#ff6b35", width=5),
        marker=dict(size=3, color=np.linspace(0, 1, len(tx)),
                    colorscale=[[0,"#fbbf24"],[0.5,"#ff6b35"],[1,"#7b5fff"]],
                    opacity=0.9),
        name="Particle trajectory",
        hovertemplate="Step %{pointNumber}<br>x:%{x:.0f}m y:%{y:.0f}m z:%{z:.0f}m<extra></extra>",
    ))

    # Start marker
    fig_tr.add_trace(go.Scatter3d(
        x=[tx[0]], y=[ty[0]], z=[tz[0]], mode="markers",
        marker=dict(size=10, color="#6ee7b7", symbol="circle",
                    line=dict(color="#ffffff", width=1)),
        name="Start position",
    ))

    # End marker
    if len(tx) > 1:
        fig_tr.add_trace(go.Scatter3d(
            x=[tx[-1]], y=[ty[-1]], z=[tz[-1]], mode="markers",
            marker=dict(size=10, color="#ef4444", symbol="x",
                        line=dict(color="#ffffff", width=1)),
            name="End position",
        ))

    # Vortex axis
    fig_tr.add_trace(go.Scatter3d(
        x=np.zeros(60), y=np.zeros(60), z=np.linspace(0, max_height, 60),
        mode="lines", line=dict(color="rgba(74,240,255,0.5)", width=2),
        name="Vortex axis", hoverinfo="skip",
    ))

    fig_tr.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor="#070b14",
        font=dict(family="Share Tech Mono", color="#8ab4d8"),
        margin=dict(l=0, r=40, t=30, b=0), height=580,
        legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a", borderwidth=1,
                    font=dict(family="Share Tech Mono", size=11, color="#8ab4d8"),
                    x=0.01, y=0.99),
        scene=dict(bgcolor="#070b14",
                   xaxis=axis_style("X [m]"), yaxis=axis_style("Y [m]"),
                   zaxis=axis_style("Height [m]"),
                   camera=dict(eye=dict(x=1.5, y=1.5, z=0.9), up=dict(x=0, y=0, z=1)),
                   aspectmode="manual", aspectratio=dict(x=1, y=1, z=1.4)),
    )
    st.plotly_chart(fig_tr, width="stretch",
                    config={"displayModeBar": True, "displaylogo": False})

    # Stats
    if len(tspeeds) > 0:
        st.markdown("---")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Pasos completados", len(tx))
        s2.metric("Altura maxima", f"{tz.max():.0f} m")
        s3.metric("Velocidad maxima", f"{tspeeds.max():.1f} m/s")
        s4.metric("Distancia recorrida",
                  f"{np.sum(np.sqrt(np.diff(tx)**2+np.diff(ty)**2+np.diff(tz)**2)):.0f} m")

        st.markdown(
            "<span style='font-family:Share Tech Mono;color:#2a4a6a;font-size:0.75rem'>"
            "La trayectoria helicoidal es el resultado de la superposicion de rotacion tangencial "
            "(V_theta) + inflow radial (V_r) + updraft vertical (V_z). "
            "Particulas mas cerca del core rotan mas rapido y ascienden antes."
            "</span>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 6 — ACERCA DE
# ══════════════════════════════════════════════════════════════════════════════════
with tab6:

    def card(titulo, icono, color, contenido):
        st.markdown(
            f"""<div style='
                background: rgba(255,255,255,0.03);
                border: 1px solid {color}44;
                border-left: 4px solid {color};
                border-radius: 10px;
                padding: 18px 22px;
                margin-bottom: 16px;
            '>
            <div style='font-family:Orbitron,monospace;font-size:1rem;font-weight:700;
                        color:{color};margin-bottom:10px'>{icono} {titulo}</div>
            <div style='font-family:Share Tech Mono,monospace;font-size:0.85rem;
                        color:#c8d8f0;line-height:1.7'>{contenido}</div>
            </div>""",
            unsafe_allow_html=True
        )

    # ── HEADER ──────────────────────────────────────────────────────────────────
    st.markdown(
        """<div style='
            background: linear-gradient(135deg, rgba(74,240,255,0.08) 0%, rgba(123,95,255,0.08) 100%);
            border: 1px solid rgba(74,240,255,0.2);
            border-radius: 14px;
            padding: 28px 32px;
            margin-bottom: 24px;
            text-align: center;
        '>
        <div style='font-family:Orbitron,monospace;font-size:1.8rem;font-weight:900;
                    background:linear-gradient(135deg,#4af0ff,#7b5fff,#ff6b35);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;margin-bottom:10px'>
            🌪️ SIMULADOR DE TORNADOS
        </div>
        <div style='font-family:Share Tech Mono,monospace;font-size:0.9rem;color:#8ab4d8'>
            Proyecto Científico · SIL 2026 · Basado en el tornado F1 de Santa Rosa del Monday, Paraguay (Diciembre 2025)
        </div>
        </div>""",
        unsafe_allow_html=True
    )

    # ── QUÉ ES ESTO ─────────────────────────────────────────────────────────────
    card(
        "¿QUÉ ES ESTA APP?", "🤔", "#4af0ff",
        """Esta es una <b style='color:#4af0ff'>simulación computacional interactiva</b> de tornados,
        desarrollada como proyecto científico escolar. Usamos matemáticas reales para recrear 
        cómo se mueve el viento dentro de un tornado — sin necesidad de estar cerca de uno.<br><br>
        Todo lo que ves en pantalla (las partículas girando, los gráficos, los números) 
        es calculado en tiempo real por la computadora usando fórmulas de física atmosférica.
        Podés cambiar los parámetros del sidebar y ver cómo cambia el tornado al instante."""
    )

    # ── DE DÓNDE VIENE LA IDEA ──────────────────────────────────────────────────
    card(
        "¿DE DÓNDE VIENE LA IDEA?", "💡", "#fbbf24",
        """En <b style='color:#fbbf24'>diciembre de 2025</b>, un tornado categoría F1 golpeó 
        <b style='color:#fbbf24'>Santa Rosa del Monday, Paraguay</b> — uno de los eventos 
        meteorológicos más intensos registrados en la región oriental del país.<br><br>
        Ese evento nos motivó a preguntarnos: <i>¿podemos modelar matemáticamente cómo funciona 
        un tornado como ese?</i> Esta app es nuestra respuesta. El botón 
        <b style='color:#ff6b35'>⚡ Preset Santa Rosa del Monday</b> en el sidebar carga 
        exactamente los parámetros estimados de ese tornado real."""
    )

    # ── CÓMO FUNCIONA ───────────────────────────────────────────────────────────
    card(
        "¿CÓMO FUNCIONA LA SIMULACIÓN?", "⚙️", "#7b5fff",
        """Usamos el <b style='color:#7b5fff'>Modelo de Vórtice de Rankine</b>, que es el modelo 
        estándar que usan los meteorólogos para describir tornados y huracanes. 
        Se divide en dos zonas:<br><br>
        &nbsp;&nbsp;🔴 <b>Zona interior (core)</b>: el aire rota como un sólido rígido — 
        cuanto más lejos del centro, más rápido.<br>
        &nbsp;&nbsp;🔵 <b>Zona exterior</b>: el viento se va debilitando a medida que te alejás, 
        siguiendo la fórmula 1/r.<br><br>
        A esto le sumamos dos efectos extra: el <b>inflow</b> (aire que entra en espiral hacia 
        adentro) y el <b>updraft</b> (corriente vertical que succiona todo hacia arriba). 
        La combinación de los tres crea el movimiento helicoidal característico del tornado."""
    )

    # ── QUÉ HACE CADA PESTAÑA ───────────────────────────────────────────────────
    st.markdown(
        "<div style='font-family:Orbitron,monospace;font-size:1rem;font-weight:700;"
        "color:#4af0ff;margin:8px 0 14px 0'>📂 ¿QUÉ HACE CADA PESTAÑA?</div>",
        unsafe_allow_html=True
    )

    tabs_info = [
        ("📡 3D VIEW",          "#4af0ff", "Vista principal del tornado en 3D. Podés rotar, hacer zoom y cambiar el color de las partículas. El panel derecho muestra la Escala Fujita y dónde cae tu configuración actual."),
        ("▶ ANIMATION",         "#7b5fff", "El tornado animado en tiempo real. Las partículas se mueven siguiendo la física del modelo — giran y suben al mismo tiempo. Presioná PLAY y podés seguir rotando el gráfico mientras corre."),
        ("📊 VELOCITY PROFILES", "#fbbf24", "Dos gráficos 2D que muestran la física en detalle: la curva de Rankine (cómo cambia la velocidad con la distancia) y el perfil vertical del updraft. Compara tu config con el F1 de Santa Rosa."),
        ("🗺️ TOP-DOWN VIEW",    "#6ee7b7", "Vista desde arriba del tornado (como si lo vieras desde un satélite). Muestra el patrón de espiral y las tres zonas de peligro: core, transición y exterior."),
        ("🎯 PARTICLE TRACKER", "#ff6b35", "Elige un punto de partida y seguí el recorrido exacto de una sola partícula dentro del vórtice. La trayectoria helicoidal muestra perfectamente cómo un tornado levanta y arrastra objetos."),
    ]

    for nombre, color, desc in tabs_info:
        st.markdown(
            f"""<div style='
                display:flex; align-items:flex-start; gap:14px;
                background:rgba(255,255,255,0.02);
                border:1px solid {color}33;
                border-radius:8px; padding:12px 16px; margin-bottom:10px;
            '>
            <div style='font-family:Orbitron,monospace;font-size:0.85rem;font-weight:700;
                        color:{color};min-width:160px;padding-top:2px'>{nombre}</div>
            <div style='font-family:Share Tech Mono,monospace;font-size:0.83rem;
                        color:#c8d8f0;line-height:1.6'>{desc}</div>
            </div>""",
            unsafe_allow_html=True
        )

    # ── CONTROLES DEL SIDEBAR ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    card(
        "¿QUÉ CONTROLAN LOS SLIDERS?", "🎛️", "#6ee7b7",
        """<b style='color:#6ee7b7'>Core Radius (R_c)</b> — El tamaño del ojo del tornado. 
        Más grande = tornado más ancho. Un F1 real tiene ~100–200 m.<br>
        <b style='color:#6ee7b7'>Max Wind Speed</b> — La velocidad del viento en el borde del core. 
        Determina automáticamente la categoría Fujita (F0 a F5).<br>
        <b style='color:#6ee7b7'>Updraft Strength</b> — Qué tan fuerte sube el aire. 
        Un updraft fuerte = tornado alto y activo.<br>
        <b style='color:#6ee7b7'>Inflow Angle</b> — Qué tan cerrada es la espiral. 
        Mayor ángulo = el aire cae hacia el centro más rápido.<br>
        <b style='color:#6ee7b7'>Number of Particles</b> — Solo cambia la densidad visual, 
        no afecta la física.<br>
        <b style='color:#ff6b35'>⚡ Preset Santa Rosa</b> — Carga de un clic los parámetros 
        estimados del tornado real de diciembre 2025."""
    )

    # ── TECNOLOGÍA ──────────────────────────────────────────────────────────────
    card(
        "¿CON QUÉ ESTÁ HECHO?", "🛠️", "#ff6b35",
        """Esta app está programada en <b style='color:#ff6b35'>Python</b>, 
        usando tres librerías principales:<br><br>
        &nbsp;&nbsp;🔢 <b>NumPy</b> — hace todos los cálculos matemáticos del modelo físico.<br>
        &nbsp;&nbsp;📊 <b>Plotly</b> — genera los gráficos 3D interactivos que podés rotar y explorar.<br>
        &nbsp;&nbsp;🌐 <b>Streamlit</b> — convierte el código Python en esta página web con sliders y pestañas.<br><br>
        El código fuente completo está disponible en GitHub y puede correrse 
        localmente con un solo comando: <b style='color:#4af0ff'>streamlit run tornado_sim.py</b>"""
    )

    # ── LIMITACIONES ────────────────────────────────────────────────────────────
    card(
        "¿QUÉ NO PUEDE HACER ESTA SIMULACIÓN?", "⚠️", "#ef4444",
        """Es importante ser honestos sobre los límites del modelo:<br><br>
        ❌ <b>No predice</b> cuándo o dónde va a ocurrir un tornado real.<br>
        ❌ <b>No simula</b> cómo se forma el tornado desde la tormenta — eso requiere 
        resolver ecuaciones de Navier-Stokes, que están más allá del nivel escolar.<br>
        ❌ <b>No incluye</b> efectos de terreno, humedad, temperatura ni fricción con el suelo.<br>
        ❌ Los valores del preset de Santa Rosa son <b>estimaciones</b> basadas en 
        la categoría Fujita observada, no mediciones directas.<br><br>
        ✅ Lo que sí hace es representar fielmente la <b>estructura cinemática</b> 
        (de velocidades) de un tornado real usando el modelo estándar de la meteorología."""
    )

    # ── FOOTER ──────────────────────────────────────────────────────────────────
    st.markdown(
        """<div style='
            text-align:center;
            margin-top:30px;
            padding:20px;
            border-top:1px solid #1a2a4a;
            font-family:Share Tech Mono,monospace;
            font-size:0.8rem;
            color:#2a4a6a;
        '>
        Proyecto Científico · Intercolegial SIL 2026 · Paraguay<br>
        Modelo: Rankine Combined Vortex · Stack: Python + NumPy + Plotly + Streamlit<br>
        <span style='color:#1a3a5a'>Inspirado en el tornado F1 de Santa Rosa del Monday · Diciembre 2025</span>
        </div>""",
        unsafe_allow_html=True
    )
