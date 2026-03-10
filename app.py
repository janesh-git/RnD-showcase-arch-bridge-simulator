import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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

# 1. Solid Bridge Blocks
arch_color = '#e6e6e6'
core_color = '#cce5ff'

ax.fill_between(x_arch, y_bottom, y_top, color=arch_color, alpha=1.0, zorder=1)
ax.plot(x_arch, y_top, 'k-', linewidth=2, zorder=3)
ax.plot(x_arch, y_bottom, 'k-', linewidth=2, zorder=3)

# Middle Third Core
ax.fill_between(x_arch, y_mid_bot, y_mid_top, color=core_color, alpha=1.0, zorder=2)
ax.plot(x_arch, y_mid_top, color='blue', linestyle=':', alpha=0.5, zorder=3)
ax.plot(x_arch, y_mid_bot, color='blue', linestyle=':', alpha=0.5, zorder=3)

# 2. Rounded, machined end-caps for the bridge
theta_left = np.linspace(np.pi/2, 3*np.pi/2, 50)
ax.add_patch(patches.Circle((0,0), thickness/2, facecolor=arch_color, edgecolor='none', zorder=1))
ax.plot((thickness/2) * np.cos(theta_left), (thickness/2) * np.sin(theta_left), 'k-', linewidth=2, zorder=3)

theta_right = np.linspace(-np.pi/2, np.pi/2, 50)
ax.add_patch(patches.Circle((span,0), thickness/2, facecolor=arch_color, edgecolor='none', zorder=1))
ax.plot(span + (thickness/2) * np.cos(theta_right), (thickness/2) * np.sin(theta_right), 'k-', linewidth=2, zorder=3)

# 3. Ground and Natural Structural Supports
ground_y = -span * 0.12 # Ground scales naturally with the span
tri_w = span * 0.05     # Width of support bases

# Thick Ground Line
ax.plot([-span*0.1, span*1.1], [ground_y, ground_y], color='#333333', linewidth=4, zorder=1)

# Left and Right Base Triangles (Anchored to ground)
left_tri = np.array([[0, 0], [-tri_w/2, ground_y], [tri_w/2, ground_y]])
ax.fill(left_tri[:,0], left_tri[:,1], color='#666666', zorder=10)

right_tri = np.array([[span, 0], [span - tri_w/2, ground_y], [span + tri_w/2, ground_y]])
ax.fill(right_tri[:,0], right_tri[:,1], color='#666666', zorder=10)

# Physical Pins (White cutouts with black inner bolts to complete the mechanical look)
ax.add_patch(patches.Circle((0, 0), radius=thickness/2.5, facecolor='white', edgecolor='black', linewidth=2, zorder=11))
ax.add_patch(patches.Circle((span, 0), radius=thickness/2.5, facecolor='white', edgecolor='black', linewidth=2, zorder=11))
ax.add_patch(patches.Circle((0, 0), radius=thickness/8, facecolor='#666666', edgecolor='black', linewidth=1, zorder=12))
ax.add_patch(patches.Circle((span, 0), radius=thickness/8, facecolor='#666666', edgecolor='black', linewidth=1, zorder=12))

# Virtual Crown Hinge
ax.plot(span/2, rise, marker='o', markersize=10, markerfacecolor='white', markeredgecolor='black', markeredgewidth=2, zorder=12, label='Virtual Crown Hinge')

# 4. Thrust Line
if is_in_middle_third:
    line_color = '#2ca02c'
    status = "SAFE: Thrust line in middle third. Pure compression."
elif is_inside_blocks:
    line_color = '#ff7f0e'
    status = "WARNING: Thrust line exited middle third. Tension cracks forming!"
else:
    line_color = '#d62728'
    status = "CRITICAL: Thrust line exited geometry. COLLAPSE!"

# Drew thrust line at zorder=13 so it elegantly stems directly out of the mechanical pins
ax.plot(x_arch, y_thrust, color=line_color, linewidth=3, zorder=13, label='Thrust Line')

# 5. Draw loads
max_w = max(load_weights) if load_weights else 1
for pos, W in zip(load_positions, load_weights):
    if W > 0:
        y_at_top = (4 * rise / span**2) * pos * (span - pos) + (thickness / 2)
        arrow_len_max = rise * 0.15
        arrow_len = max(arrow_len_max * (W / max_w) if max_w > 0 else 1, 0.3)
        top_of_arrow = y_at_top + arrow_len + 0.1 
        
        ax.arrow(pos, top_of_arrow, 0, -arrow_len, head_width=span*0.015, head_length=rise*0.02, fc='black', ec='black', zorder=15)
        ax.text(pos, top_of_arrow + 0.1, f"{W} kg", ha='center', fontsize=9, fontweight='bold')

ax.set_title(status, color=line_color, fontweight='bold', fontsize=14)
ax.set_xlabel('Bridge Span', fontsize=12)
ax.set_ylabel('Height', fontsize=12)

# Adjust margins to fit the new ground line
y_limit_top = rise + thickness + 1.5 
ax.set_ylim(ground_y - 0.5, y_limit_top)
ax.axis('equal')
ax.grid(True, linestyle=':', alpha=0.6)

# Hide axis to make it look purely like a diagram (optional, looks cleaner)
# ax.axis('off') 

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
