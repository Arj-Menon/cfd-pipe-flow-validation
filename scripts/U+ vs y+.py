"""
u+ vs y+ Velocity Profile Plotter
==================================
Converts raw Fluent XY export (radial position vs axial velocity)
into non-dimensional wall coordinates and compares against the
analytical law of the wall.

Usage:
    1. Export velocity profile from Fluent as .xy file
    2. Update the filename and parameters below
    3. Run: python plot_u_plus_y_plus.py

Author: Arjun (CFD Portfolio - Project 1: Pipe Flow Validation)
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# USER INPUTS — update these for each run
# ============================================================

# Path to your exported Fluent .xy file
# Format expected: two columns — radial position [m], axial velocity [m/s]
# Lines starting with ( are headers — script skips them automatically
DATA_FILE = "V_out"

# Flow parameters
rho = 1.225          # density [kg/m3]
mu = 1.789e-5        # dynamic viscosity [Pa.s]
R = 0.025            # pipe radius [m]
tau_w = 0.7221       # wall shear stress from Fluent [Pa] — UPDATE for each mesh/model

# Computed quantities
u_tau = np.sqrt(tau_w / rho)   # friction velocity [m/s]
print(f"Friction velocity u_tau = {u_tau:.4f} m/s")

# ============================================================
# READ DATA
# ============================================================

y_positions = []
velocities = []

with open(DATA_FILE, 'r') as f:
    for line in f:
        line = line.strip()
        # Skip empty lines and Fluent headers (lines starting with ( or other non-numeric chars)
        if not line or line.startswith('(') or line.startswith(')'):
            continue
        try:
            parts = line.split()
            if len(parts) >= 2:
                y_pos = float(parts[0])    # radial position from axis [m]
                u_vel = float(parts[1])    # axial velocity [m/s]
                y_positions.append(y_pos)
                velocities.append(u_vel)
        except ValueError:
            continue  # skip any non-numeric lines

y_positions = np.array(y_positions)
velocities = np.array(velocities)

print(f"Loaded {len(y_positions)} data points")
print(f"Radial range: {y_positions.min():.6f} to {y_positions.max():.6f} m")
print(f"Velocity range: {velocities.min():.4f} to {velocities.max():.4f} m/s")

# ============================================================
# CONVERT TO WALL COORDINATES
# ============================================================

# Distance from wall (not from axis)
y_wall = R - y_positions

# Remove points exactly at the wall (y_wall = 0) to avoid log(0)
mask = y_wall > 0
y_wall = y_wall[mask]
u_vel = velocities[mask]

# Non-dimensionalise
y_plus = y_wall * rho * u_tau / mu
u_plus = u_vel / u_tau

# Sort by y+ for clean plotting
sort_idx = np.argsort(y_plus)
y_plus = y_plus[sort_idx]
u_plus = u_plus[sort_idx]

# ============================================================
# ANALYTICAL PROFILES
# ============================================================

# Viscous sublayer: u+ = y+ (valid for y+ < 5)
y_plus_visc = np.linspace(0.1, 10, 100)
u_plus_visc = y_plus_visc

# Log-law: u+ = (1/kappa) * ln(y+) + B (valid for y+ > 30)
kappa = 0.41
B = 5.2
y_plus_log = np.linspace(10, 1000, 500)
u_plus_log = (1/kappa) * np.log(y_plus_log) + B

# ============================================================
# PLOT
# ============================================================

fig, ax = plt.subplots(1, 1, figsize=(10, 7))

# CFD data
ax.semilogx(y_plus, u_plus, 'o-', color='#2563EB', markersize=3, 
            linewidth=1.2, label='CFD (k-ε, Enhanced Wall Treatment)', zorder=3)

# Viscous sublayer
ax.semilogx(y_plus_visc, u_plus_visc, '--', color='#16A34A', linewidth=1.5, 
            label='Viscous sublayer: u⁺ = y⁺')

# Log-law
ax.semilogx(y_plus_log, u_plus_log, '--', color='#DC2626', linewidth=1.5, 
            label=f'Log-law: u⁺ = (1/{kappa}) ln(y⁺) + {B}')

# Formatting
ax.set_xlabel('y⁺', fontsize=13)
ax.set_ylabel('u⁺', fontsize=13)
ax.set_title('Velocity Profile in Wall Coordinates — Pipe Flow Validation\n'
             f'Re = 50,000 | Coarse Mesh (10,000 cells) | τ_w = {tau_w} Pa', fontsize=12)
ax.legend(fontsize=10, loc='upper left')
ax.set_xlim(0.5, 2000)
ax.set_ylim(0, 30)
ax.grid(True, which='both', alpha=0.3)

# Add region annotations
ax.axvspan(0.5, 5, alpha=0.05, color='green', label='_nolegend_')
ax.axvspan(5, 30, alpha=0.05, color='orange', label='_nolegend_')
ax.axvspan(30, 2000, alpha=0.05, color='blue', label='_nolegend_')
ax.text(2, 27, 'Viscous\nsublayer', fontsize=8, color='green', ha='center', alpha=0.7)
ax.text(12, 27, 'Buffer\nlayer', fontsize=8, color='orange', ha='center', alpha=0.7)
ax.text(200, 27, 'Log-law region', fontsize=8, color='blue', ha='center', alpha=0.7)

plt.tight_layout()
plt.savefig('u_plus_vs_y_plus_coarse.png', dpi=200, bbox_inches='tight')
plt.show()

print(f"\nPlot saved as 'u_plus_vs_y_plus_coarse.png'")
print(f"\nKey values:")
print(f"  u_tau = {u_tau:.4f} m/s")
print(f"  tau_w = {tau_w:.4f} Pa")
print(f"  f_CFD = {8 * tau_w / (rho * 14.6**2):.5f}")
print(f"  f_Colebrook = 0.0209")
print(f"  Error = {abs(8*tau_w/(rho*14.6**2) - 0.0209)/0.0209 * 100:.1f}%")