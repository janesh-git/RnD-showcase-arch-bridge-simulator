import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Safety Analysis of Arch Geometry")

st.title("Safety Analysis of Arch Geometry")
st.markdown("Adjust the sliders to place weights on the bridge. Watch how the **Thrust Line** reacts to the loads.")

# --- UI CONTROLS (SIDEBAR) ---
st.sidebar.header("1. Bridge Geometry")
span = st.sidebar.slider("Span (Width)", min_value=5.0, max_value=20.0, value=10.0, step=0.5)
rise = st.sidebar.slider("Rise (Height)", min_value=2.0, max_value=10.0, value=4.0, step=0.5)
thickness = st.sidebar.slider("Block Thickness", min_value=0.5, max_value=3.0, value=1.5, step=0.1)

self_weight = st.sidebar.slider("Bridge Self-Weight (Uniform Load)", min_value=0.0, max_value=20.0, value=5.0, step=1.0)

st.sidebar.header("2. Live Loads (Weights)")
num_loads = st.sidebar.number_input("Number of Weights", min_value=0, max_value=3, value=1)

load_positions = []
load_weights = []

for i in range(num_loads):
    st.sidebar.subheader(f"Weight #{i+1}")
    pos = st.sidebar.slider(f"Position of Weight #{i+1}", min_value=0.0, max_value=span, value=span/2, step=0.1, key=f"pos_{i}")
    weight = st.sidebar.slider(f"Mass of Weight #{i+1}", min_value=0.0, max_value=100.0, value=20.0, step=5.0, key=f"w_{i}")
    load_positions.append(pos)
    load_weights.append(weight)

# --- PHYSICS & MATH ---
x_arch = np.linspace(0, span, 500)
y_center = (4 * rise / span**2) * x_arch * (span - x_arch)

y_top = y_center + (thickness / 2)
y_bottom = y_center - (thickness / 2)
y_mid_top = y_center + (thickness / 6)
y_mid_bot = y_center - (thickness / 6)

# Moments
R_dead_left = (self_weight * span) / 2
M_dead = R_dead_left * x_arch - self_weight * (x_arch**2) / 2

R_live_left = sum(W * (span - pos) / span for pos, W in zip(load_positions, load_weights))
M_live = np.zeros_like(x_arch)
for i, x_val in enumerate(x_arch):
    m = R_live_left * x_val
    for pos, W in zip(load_positions, load_weights):
        if pos < x_val:
            m -= W * (x_val - pos)
    M_live[i] = m

M_total = M_dead + M_live

# 3-Pinned Arch Calculation
moment_at_crown = M_total[len(x_arch)//2]
H = moment_at_crown / rise if rise != 0 else 1
y_thrust = M_total / H if H != 0 else np.zeros_like(x_arch)

is_in_middle_third = np.all((y_thrust <= y_mid_top) & (y_thrust >= y_mid_bot))
is_inside_blocks = np.all((y_thrust <= y_top) & (y_thrust >= y_bottom))

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(12, 6))

# Draw the blocks
ax.plot(x_arch, y_top, 'k-', linewidth=2)
ax.plot(x_arch, y_bottom, 'k-', linewidth=2)

# Vertical end caps to make the bridge look solid
ax.plot([0, 0], [y_bottom[0], y_top[0]], 'k-', linewidth=2)
ax.plot([span, span], [y_bottom[-1], y_top[-1]], 'k-', linewidth=2)

ax.fill_between(x_arch, y_bottom, y_top, color='#cccccc', alpha=0.5, label='Masonry Blocks')

# Middle Third Core
ax.plot(x_arch, y_mid_top, color='blue', linestyle=':', alpha=0.5)
ax.plot(x_arch, y_mid_bot, color='blue', linestyle=':', alpha=0.5)
ax.fill_between(x_arch, y_mid_bot, y_mid_top, color='#87CEFA', alpha=0.5, label='Middle-Third Core')

if is_in_middle_third:
    line_color = '#2ca02c'
    status = "SAFE: Thrust line in middle third. Pure compression."
elif is_inside_blocks:
    line_color = '#ff7f0e'
    status = "WARNING: Thrust line exited middle third. Tension cracks forming!"
else:
    line_color = '#d62728'
    status = "CRITICAL: Thrust line exited geometry. COLLAPSE!"

ax.plot(x_arch, y_thrust, color=line_color, linewidth=3, label='Thrust Line')

# --- GROUND AND STRUCTURAL SUPPORTS ---
ground_y = -thickness / 2

# Thick Ground Line
ax.plot([-span*0.1, span*1.1], [ground_y, ground_y], color='#333333', linewidth=4, zorder=1)

# Left Support Triangle (Custom drawn to sit perfectly on the ground)
triangle_h = thickness / 2
triangle_w = span * 0.04
left_triangle = np.array([[0, 0], [-triangle_w/2, ground_y], [triangle_w/2, ground_y], [0, 0]])
ax.fill(left_triangle[:,0], left_triangle[:,1], color='black', zorder=5)

# Right Support Triangle
right_triangle = np.array([[span, 0], [span - triangle_w/2, ground_y], [span + triangle_w/2, ground_y], [span, 0]])
ax.fill(right_triangle[:,0], right_triangle[:,1], color='black', zorder=5)

# Virtual Crown Hinge (Keep the circle)
ax.plot(span/2, rise, marker='o', markersize=10, markerfacecolor='white', markeredgecolor='black', markeredgewidth=2, zorder=6, label='Virtual Crown Hinge')

# Draw loads
max_w = max(load_weights) if load_weights else 1
for pos, W in zip(load_positions, load_weights):
    if W > 0:
        y_at_top = (4 * rise / span**2) * pos * (span - pos) + (thickness / 2)
        arrow_len_max = rise * 0.15
        arrow_len = max(arrow_len_max * (W / max_w) if max_w > 0 else 1, 0.3)
        top_of_arrow = y_at_top + arrow_len + 0.1 
        
        ax.arrow(pos, top_of_arrow, 0, -arrow_len, head_width=span*0.015, head_length=rise*0.02, fc='black', ec='black')
        ax.text(pos, top_of_arrow + 0.1, f"{W} kg", ha='center', fontsize=9, fontweight='bold')

ax.set_title(status, color=line_color, fontweight='bold', fontsize=14)
ax.set_xlabel('Bridge Span', fontsize=12)
ax.set_ylabel('Height', fontsize=12)

# Adjust y-limits so the ground isn't cut off
y_limit_top = rise + thickness + 1.5 
ax.set_ylim(ground_y - 1.0, y_limit_top)
ax.axis('equal')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=4)

st.pyplot(fig)

# --- CLEAN LEGEND WITH COLORED DOTS ---
st.markdown("""
### How to read this chart:
* <span style='color:#2ca02c;'>●</span> **Green Line:** Safe. The blocks are pressing tightly together.
* <span style='color:#ff7f0e;'>●</span> **Orange Line:** Danger. The line left the blue core. The joints on the opposite side of the line are pulling apart and cracking.
* <span style='color:#d62728;'>●</span> **Red Line:** Failure. The line pushed completely outside the stones. The bridge has fallen.
""", unsafe_allow_html=True)

st.markdown("---")

# --- ASSUMPTIONS ONLY ---
st.markdown("### Engineering Assumptions")
st.markdown("""
Based on Jacques Heyman's framework for masonry:
1. **Three-Hinged Arch:** We assume virtual hinges at the two base supports and the crown. This makes the structure statically determinate.
2. **Zero Tensile Strength:** Masonry blocks and mortar cannot handle pulling forces. If the line leaves the middle third, joints crack.
3. **Infinite Compressive Strength:** We assume the stones will not crush under pressure.
4. **No Sliding:** Friction between the blocks is high enough that they will not slide past one another.
""")
