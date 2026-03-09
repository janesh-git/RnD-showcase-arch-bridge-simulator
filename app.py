import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Live Arch Bridge R&D")

st.title("🌉 Live Arch Bridge Structural Simulator")
st.markdown("Adjust the sliders to place weights on the bridge. Watch how the **Thrust Line** reacts!")

# --- UI CONTROLS (SIDEBAR) ---
st.sidebar.header("1. Bridge Geometry")
span = st.sidebar.slider("Span (Width)", min_value=5.0, max_value=20.0, value=10.0, step=0.5)
rise = st.sidebar.slider("Rise (Height)", min_value=2.0, max_value=10.0, value=4.0, step=0.5)
thickness = st.sidebar.slider("Block Thickness", min_value=0.5, max_value=3.0, value=1.5, step=0.1)

# Added self-weight so the arch behaves like real, heavy stone blocks
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
# Parabolic centerline
y_center = (4 * rise / span**2) * x_arch * (span - x_arch)

# Arch Boundaries
y_top = y_center + (thickness / 2)
y_bottom = y_center - (thickness / 2)

# Middle-Third Boundaries (The "Safe Core")
y_mid_top = y_center + (thickness / 6)
y_mid_bot = y_center - (thickness / 6)

# 1. Moments from the bridge's own weight
R_dead_left = (self_weight * span) / 2
M_dead = R_dead_left * x_arch - self_weight * (x_arch**2) / 2

# 2. Moments from applied weights
R_live_left = sum(W * (span - pos) / span for pos, W in zip(load_positions, load_weights))
M_live = np.zeros_like(x_arch)
for i, x_val in enumerate(x_arch):
    m = R_live_left * x_val
    for pos, W in zip(load_positions, load_weights):
        if pos < x_val:
            m -= W * (x_val - pos)
    M_live[i] = m

# Total Moment
M_total = M_dead + M_live

# Horizontal Thrust (pinned at the crown: x = span/2)
moment_at_crown = M_total[len(x_arch)//2]
H = moment_at_crown / rise if rise != 0 else 1

# Thrust Line Geometry
y_thrust = M_total / H if H != 0 else np.zeros_like(x_arch)

# Safety checks
is_in_middle_third = np.all((y_thrust <= y_mid_top) & (y_thrust >= y_mid_bot))
is_inside_blocks = np.all((y_thrust <= y_top) & (y_thrust >= y_bottom))

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(12, 6))

# Draw the blocks
ax.plot(x_arch, y_top, 'k-', linewidth=2)
ax.plot(x_arch, y_bottom, 'k-', linewidth=2)
ax.fill_between(x_arch, y_bottom, y_top, color='#cccccc', alpha=0.5, label='Masonry Blocks')

# Draw the Middle-Third core
ax.plot(x_arch, y_mid_top, color='blue', linestyle=':', alpha=0.5)
ax.plot(x_arch, y_mid_bot, color='blue', linestyle=':', alpha=0.5)
ax.fill_between(x_arch, y_mid_bot, y_mid_top, color='#87CEFA', alpha=0.5, label='Middle-Third (Compression Core)')

# Determine thrust line status and color
if is_in_middle_third:
    line_color = '#2ca02c' # Green
    status = "PERFECT: Thrust line is in the middle third. Pure compression!"
elif is_inside_blocks:
    line_color = '#ff7f0e' # Orange
    status = "WARNING: Thrust line exited the middle third. Tension cracks are forming!"
else:
    line_color = '#d62728' # Red
    status = "CRITICAL: Thrust line exited the blocks entirely. COLLAPSE!"

# Plot thrust line
ax.plot(x_arch, y_thrust, color=line_color, linewidth=3, label='Thrust Line')

# --- CHANGED: Shrink the load arrow visualization ---
max_w = max(load_weights) if load_weights else 1
for pos, W in zip(load_positions, load_weights):
    if W > 0:
        # 1. Find the y-coordinate of the top of the arch at this x-position
        y_at_top = (4 * rise / span**2) * pos * (span - pos) + (thickness / 2)
        
        # 2. Calculate scaled length. (Smaller multiplier keeps it short)
        # Old scaling: rise * 0.3
        # New scaling: rise * 0.15 (Halved the base length)
        # Added minimum length so very tiny weights are still visible
        arrow_len_max = rise * 0.15
        arrow_len = arrow_len_max * (W / max_w) if max_w > 0 else 1
        arrow_len = max(arrow_len, 0.3) # Set a minimum visible length
        
        # 3. Reduce the empty space (offset) above the arrow
        # Old offset: arrow_len + 0.5
        # New offset: arrow_len + 0.1 (Brings it tighter to the arch)
        top_of_arrow = y_at_top + arrow_len + 0.1 
        
        # 4. Draw the arrow
        ax.arrow(pos, top_of_arrow, 0, -arrow_len, 
                 head_width=span*0.015, # also shrunk the head width slightly
                 head_length=rise*0.02, # also shrunk the head length slightly
                 fc='black', ec='black')
        
        # 5. Place the text closer to the arrow
        ax.text(pos, top_of_arrow + 0.1, f"{W} kg", ha='center', fontsize=9, fontweight='bold')

ax.set_title(status, color=line_color, fontweight='bold', fontsize=14)
ax.set_xlabel('Bridge Span', fontsize=12)
ax.set_ylabel('Height', fontsize=12)

# Ensure the y-axis has a bit of extra padding at the top so text is never cut off
y_limit_top = rise + thickness + 1.5 
ax.set_ylim(-0.5, y_limit_top)

ax.axis('equal')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=3)

# Display plot in Streamlit
st.pyplot(fig)

st.markdown("""
### 🏗️ How to read this chart:
* **Green Line:** Safe. The blocks are pressing tightly together.
* **Orange Line:** Danger. The line left the blue core. The joints on the opposite side of the line are pulling apart and cracking.
* **Red Line:** Failure. The line pushed completely outside the stones. The bridge has fallen.
""")