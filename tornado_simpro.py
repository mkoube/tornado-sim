"""
╔══════════════════════════════════════════════════════════════════╗
║         TORNADO SIMULATOR — Rankine Vortex + Updraft Model       ║
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

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"] { background-color: #070b14; color: #c8d8f0; }

h1 {
    font-family: 'Orbitron', monospace !important;
    font-weight: 900 !important;
    font-size: 2.4rem !important;
    letter-spacing: 0.12em !important;
    background: linear-gradient(135deg, #4af0ff 0%, #7b5fff 50%, #ff6b35 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0 !important;
}
h2, h3 {
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    color: #4af0ff !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1020 0%, #0d1525 100%) !important;
    border-right: 1px solid #1a2a4a;
}
[data-testid="stSidebar"] label {
    font-family: 'Share Tech Mono', monospace !important;
    color: #8ab4d8 !important;
    font-size: 0.85rem !important;
}
[data-testid="metric-container"] {
    background: rgba(74,240,255,0.05) !important;
    border: 1px solid rgba(74,240,255,0.2) !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
[data-testid="metric-container"] label {
    font-family: 'Share Tech Mono', monospace !important;
    color: #8ab4d8 !important;
    font-size: 0.75rem !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    color: #4af0ff !important;
    font-size: 1.3rem !important;
}
hr { border-color: #1a2a4a !important; }
[data-testid="stPlotlyChart"] { border: 1px solid #1a2a4a; border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌪️ VORTEX CONTROLS")
    st.markdown("---")
    st.markdown("### STRUCTURE")
    R_c = st.slider("Core Radius (R_c) [m]", 50, 500, 150, 10)
    max_wind = st.slider("Max Wind Speed [m/s]", 20, 150, 70, 5)
    st.markdown("### DYNAMICS")
    updraft_strength = st.slider("Updraft Strength [m/s]", 5, 80, 30, 5)
    inflow_angle = st.slider("Inflow Angle [degrees]", 5, 45, 20, 1)
    st.markdown("### VISUALIZATION")
    n_particles = st.slider("Number of Particles", 500, 5000, 2000, 100)
    max_height = st.slider("Simulation Height [m]", 500, 5000, 2000, 100)
    color_mode = st.selectbox(
        "Color By",
        ["Speed (total)", "Tangential velocity", "Vertical velocity", "Radius"]
    )
    st.markdown("### ANIMATION")
    n_frames = st.slider("Animation Frames", 20, 80, 40, 5,
                         help="More frames = smoother but slower to generate.")
    anim_speed = st.slider("Frame Delay [ms]", 30, 200, 70, 10,
                           help="Lower = faster animation.")
    st.markdown("---")
    st.caption("Rankine Vortex Model + Updraft\nMaxi — SIL 2026 Science Project")


# ─── HELPER: AXIS STYLE ─────────────────────────────────────────────────────────
def axis_style(label):
    return dict(
        title=dict(text=label,
                   font=dict(family="Share Tech Mono", color="#4af0ff", size=11)),
        tickfont=dict(family="Share Tech Mono", color="#4a6a8a", size=9),
        gridcolor="#0f1e30",
        showbackground=True,
        backgroundcolor="rgba(7,11,20,0.5)",
        zerolinecolor="#1a2a4a",
    )


# ─── PHYSICS: STATIC SNAPSHOT ───────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def simulate_tornado(R_c, max_wind, updraft_strength, inflow_angle, n_particles, max_height):
    """
    Rankine Vortex kinematic model:
      Inner core  (r <= R_c): V_theta = V_max * (r / R_c)  [solid-body rotation]
      Outer region (r >  R_c): V_theta = V_max * (R_c / r) [irrotational decay]
      Radial inflow : V_r = -V_theta * tan(alpha) * exp(-z/H)
      Vertical updraft: V_z = W * exp(-r^2/2Rc^2) * height_factor
    """
    rng = np.random.default_rng(seed=42)
    r_u = rng.uniform(0.01 * R_c, 3.0 * R_c, n_particles // 2)
    r_l = np.clip(rng.lognormal(np.log(R_c), 0.6, n_particles - n_particles // 2),
                  0.01 * R_c, 3.0 * R_c)
    r     = np.concatenate([r_u, r_l])
    theta = rng.uniform(0, 2 * np.pi, n_particles)
    z     = rng.uniform(0, max_height, n_particles)

    V_theta = np.where(r <= R_c, max_wind * (r / R_c), max_wind * (R_c / r))
    alpha   = np.radians(inflow_angle)
    V_r     = -V_theta * np.tan(alpha) * np.exp(-z / (max_height * 0.6))
    V_z     = updraft_strength * np.exp(-0.5 * (r / R_c)**2) * (0.5 + 0.5 * z / max_height)

    dt  = 1.0
    V_x = V_r * np.cos(theta) - V_theta * np.sin(theta)
    V_y = V_r * np.sin(theta) + V_theta * np.cos(theta)
    x   = r * np.cos(theta) + V_x * dt * 0.3
    y   = r * np.sin(theta) + V_y * dt * 0.3
    z_d = z + V_z * dt * 0.5
    V_total = np.sqrt(V_theta**2 + V_r**2 + V_z**2)
    return x, y, z_d, r, V_theta, V_r, V_z, V_total


# ─── PHYSICS: ANIMATION FRAMES ──────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def build_animation_frames(R_c, max_wind, updraft_strength, inflow_angle,
                            n_particles, max_height, n_frames):
    """
    Advects particles through time using their local Rankine velocity:
        x(t+dt) = x(t) + Vx * dt
        y(t+dt) = y(t) + Vy * dt
        z(t+dt) = z(t) + Vz * dt
    Particles exiting the top are recycled to the base (continuous debris effect).
    Rotation + updraft combined = helical spiral animation.
    """
    rng = np.random.default_rng(seed=7)
    n   = n_particles

    r0     = np.concatenate([
        rng.uniform(0.01 * R_c, 3.0 * R_c, n // 2),
        np.clip(rng.lognormal(np.log(R_c), 0.6, n - n // 2), 0.01 * R_c, 3.0 * R_c)
    ])
    theta0 = rng.uniform(0, 2 * np.pi, n)
    px     = r0 * np.cos(theta0)
    py     = r0 * np.sin(theta0)
    pz     = rng.uniform(0, max_height, n)
    alpha  = np.radians(inflow_angle)
    dt     = 0.9
    frames = []

    for _ in range(n_frames):
        r_cur     = np.maximum(np.sqrt(px**2 + py**2), 1.0)
        theta_cur = np.arctan2(py, px)

        V_th = np.where(r_cur <= R_c, max_wind * (r_cur / R_c), max_wind * (R_c / r_cur))
        V_r  = -V_th * np.tan(alpha) * np.exp(-pz / (max_height * 0.6))
        V_z  = updraft_strength * np.exp(-0.5 * (r_cur / R_c)**2) * (0.5 + 0.5 * pz / max_height)
        Vx   = V_r * np.cos(theta_cur) - V_th * np.sin(theta_cur)
        Vy   = V_r * np.sin(theta_cur) + V_th * np.cos(theta_cur)

        px += Vx * dt
        py += Vy * dt
        pz += V_z * dt

        # Recycle particles that escape the top
        exited = pz > max_height
        n_exit = int(exited.sum())
        if n_exit:
            new_th      = rng.uniform(0, 2 * np.pi, n_exit)
            pz[exited]  = rng.uniform(0, max_height * 0.05, n_exit)
            px[exited]  = r0[exited] * np.cos(new_th)
            py[exited]  = r0[exited] * np.sin(new_th)

        speed = np.sqrt(Vx**2 + Vy**2 + V_z**2)
        frames.append((px.copy(), py.copy(), pz.copy(), speed.copy()))

    return frames


# ─── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("# 🌪️ TORNADO SIMULATOR")
st.markdown(
    "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.85rem;'>"
    "Rankine Vortex Model · Interactive 3D Particle Field · Real-Time Parameter Control"
    "</span>", unsafe_allow_html=True
)
st.markdown("---")

with st.spinner("Solving vortex dynamics..."):
    x, y, z, r, V_theta, V_r, V_z, V_total = simulate_tornado(
        R_c, max_wind, updraft_strength, inflow_angle, n_particles, max_height
    )

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Core Radius",  f"{R_c} m")
c2.metric("Max Wind",     f"{max_wind} m/s")
c3.metric("Updraft",      f"{updraft_strength} m/s")
c4.metric("Inflow Angle", f"{inflow_angle} deg")
c5.metric("Particles",    f"{n_particles:,}")
st.markdown("<br>", unsafe_allow_html=True)


# ─── TABS ───────────────────────────────────────────────────────────────────────
tab_static, tab_anim = st.tabs(["📡  STATIC 3D VIEW", "▶  ANIMATION"])


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 1 — STATIC 3D SCATTER
# ══════════════════════════════════════════════════════════════════════════════════
with tab_static:
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
        marker=dict(
            size=1.8, color=c_data, colorscale=colorscale, opacity=0.85,
            colorbar=dict(
                title=dict(text=c_label, side="right",
                           font=dict(family="Share Tech Mono", color="#8ab4d8", size=11)),
                thickness=14, len=0.7, x=1.02,
                tickfont=dict(family="Share Tech Mono", color="#8ab4d8", size=10),
            ),
        ),
        name="Air parcels",
        hovertemplate="x: %{x:.0f} m<br>y: %{y:.0f} m<br>z: %{z:.0f} m<extra></extra>",
    ))

    z_ax = np.linspace(0, max_height, 80)
    fig.add_trace(go.Scatter3d(
        x=np.zeros(80), y=np.zeros(80), z=z_ax, mode="lines",
        line=dict(color="rgba(74,240,255,0.7)", width=3),
        name="Vortex axis", hoverinfo="skip",
    ))

    phi = np.linspace(0, 2 * np.pi, 120)
    fig.add_trace(go.Scatter3d(
        x=R_c * np.cos(phi), y=R_c * np.sin(phi), z=np.zeros(120), mode="lines",
        line=dict(color="rgba(255,107,53,0.8)", width=2, dash="dot"),
        name=f"Core radius ({R_c} m)", hoverinfo="skip",
    ))

    fig.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor="#070b14",
        font=dict(family="Share Tech Mono", color="#8ab4d8"),
        margin=dict(l=0, r=60, t=30, b=0), height=680,
        legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a", borderwidth=1,
                    font=dict(family="Share Tech Mono", size=11, color="#8ab4d8"),
                    x=0.01, y=0.99),
        scene=dict(
            bgcolor="#070b14",
            xaxis=axis_style("X [m]"),
            yaxis=axis_style("Y [m]"),
            zaxis=axis_style("Height [m]"),
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.8), up=dict(x=0, y=0, z=1)),
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=1.4),
        ),
    )
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": True, "displaylogo": False})

    st.markdown("---")
    st.markdown("### VORTEX PHYSICS REFERENCE")
    ca, cb, cc = st.columns(3)
    with ca:
        st.markdown("**TANGENTIAL VELOCITY**")
        st.markdown(
            "<span style='font-family:Share Tech Mono;font-size:0.82rem;color:#8ab4d8'>"
            "Rankine profile:<br>"
            "r <= R_c : V = V_max*(r/R_c) [solid body]<br>"
            "r >  R_c : V = V_max*(R_c/r) [irrotational]"
            "</span>", unsafe_allow_html=True)
    with cb:
        st.markdown("**RADIAL INFLOW**")
        st.markdown(
            "<span style='font-family:Share Tech Mono;font-size:0.82rem;color:#8ab4d8'>"
            "V_r = -V_theta * tan(a) * exp(-z/H)<br>"
            "a = inflow angle, H = scale height.<br>"
            "Inflow weakens aloft (boundary layer)."
            "</span>", unsafe_allow_html=True)
    with cc:
        st.markdown("**VERTICAL UPDRAFT**")
        st.markdown(
            "<span style='font-family:Share Tech Mono;font-size:0.82rem;color:#8ab4d8'>"
            "V_z = W * exp(-r^2/2Rc^2) * (0.5+0.5z/H)<br>"
            "Gaussian core * chimney height factor.<br>"
            "Peak at core, grows with altitude."
            "</span>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANIMATED TORNADO
# ══════════════════════════════════════════════════════════════════════════════════
with tab_anim:
    st.markdown(
        "<span style='font-family:Share Tech Mono;color:#4a6a8a;font-size:0.82rem'>"
        "Particulas advectadas frame a frame  |  Rotacion + Updraft combinados  |  "
        "Presiona Play para iniciar  |  Podes rotar el grafico mientras anima"
        "</span>", unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner(f"Generando {n_frames} frames de animacion..."):
        anim_frames = build_animation_frames(
            R_c, max_wind, updraft_strength, inflow_angle,
            n_particles, max_height, n_frames
        )

    px0, py0, pz0, spd0 = anim_frames[0]
    phi2 = np.linspace(0, 2 * np.pi, 120)
    v_max_color = float(max_wind) * 1.2

    fig_anim = go.Figure(
        data=[
            # Trace 0 — animated particle cloud
            go.Scatter3d(
                x=px0, y=py0, z=pz0, mode="markers",
                marker=dict(
                    size=1.6, color=spd0, colorscale="Plasma",
                    cmin=0, cmax=v_max_color, opacity=0.88,
                    colorbar=dict(
                        title=dict(text="Speed [m/s]", side="right",
                                   font=dict(family="Share Tech Mono", color="#8ab4d8", size=11)),
                        thickness=14, len=0.65, x=1.02,
                        tickfont=dict(family="Share Tech Mono", color="#8ab4d8", size=10),
                    ),
                ),
                name="Debris / air parcels", hoverinfo="skip",
            ),
            # Trace 1 — static vortex axis (not animated)
            go.Scatter3d(
                x=[0, 0], y=[0, 0], z=[0, max_height], mode="lines",
                line=dict(color="rgba(74,240,255,0.6)", width=3),
                name="Vortex axis", hoverinfo="skip",
            ),
            # Trace 2 — static core ring (not animated)
            go.Scatter3d(
                x=R_c * np.cos(phi2), y=R_c * np.sin(phi2), z=np.zeros(120), mode="lines",
                line=dict(color="rgba(255,107,53,0.7)", width=2, dash="dot"),
                name=f"Core radius ({R_c} m)", hoverinfo="skip",
            ),
        ],
        frames=[
            go.Frame(
                data=[go.Scatter3d(
                    x=px, y=py, z=pz, mode="markers",
                    marker=dict(size=1.6, color=spd, colorscale="Plasma",
                                cmin=0, cmax=v_max_color, opacity=0.88),
                )],
                traces=[0],   # only update the particle trace
                name=str(i),
            )
            for i, (px, py, pz, spd) in enumerate(anim_frames)
        ],
    )

    fig_anim.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor="#070b14",
        font=dict(family="Share Tech Mono", color="#8ab4d8"),
        margin=dict(l=0, r=60, t=30, b=60), height=720,
        legend=dict(bgcolor="rgba(7,11,20,0.8)", bordercolor="#1a2a4a", borderwidth=1,
                    font=dict(family="Share Tech Mono", size=11, color="#8ab4d8"),
                    x=0.01, y=0.99),
        scene=dict(
            bgcolor="#070b14",
            xaxis=axis_style("X [m]"),
            yaxis=axis_style("Y [m]"),
            zaxis=axis_style("Height [m]"),
            camera=dict(eye=dict(x=1.7, y=1.7, z=0.7), up=dict(x=0, y=0, z=1)),
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=1.4),
        ),
        # ── Play / Pause buttons ─────────────────────────────────────────────────
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=-0.05, x=0.5, xanchor="center",
            bgcolor="#0d1525",
            bordercolor="#1a2a4a",
            font=dict(family="Orbitron", color="#4af0ff", size=11),
            buttons=[
                dict(
                    label="  PLAY",
                    method="animate",
                    args=[None, {
                        "frame": {"duration": anim_speed, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 0},
                        "mode": "immediate",
                    }],
                ),
                dict(
                    label="  PAUSE",
                    method="animate",
                    args=[[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    }],
                ),
            ],
        )],
        # ── Frame scrubber slider ────────────────────────────────────────────────
        sliders=[dict(
            active=0,
            currentvalue=dict(
                prefix="Frame: ",
                font=dict(family="Share Tech Mono", color="#4af0ff", size=11),
            ),
            pad=dict(t=10, b=10, l=20, r=20),
            bgcolor="#0d1525",
            bordercolor="#1a2a4a",
            tickcolor="#1a2a4a",
            font=dict(family="Share Tech Mono", color="#4a6a8a", size=8),
            steps=[
                dict(
                    args=[[str(i)], {
                        "frame": {"duration": anim_speed, "redraw": True},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    }],
                    label=str(i) if i % 5 == 0 else "",
                    method="animate",
                )
                for i in range(n_frames)
            ],
        )],
    )

    st.plotly_chart(fig_anim, use_container_width=True,
                    config={"displayModeBar": True, "displaylogo": False})

    st.markdown(
        "<span style='font-family:Share Tech Mono;color:#2a4a6a;font-size:0.75rem'>"
        "Cada frame advecta las particulas con su velocidad local Rankine (Vx, Vy, Vz). "
        "Las que salen por arriba se reciclan en la base — debris continuo. "
        "Ajusta 'Frame Delay' en el sidebar para cambiar la velocidad."
        "</span>", unsafe_allow_html=True
    )
