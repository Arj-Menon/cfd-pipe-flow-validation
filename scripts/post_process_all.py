"""
Pipe Flow Validation — Complete Post-Processing
=================================================
Generates all plots for Project 1:
  1. u+ vs y+ comparison (k-epsilon vs SST k-omega)
  2. Velocity profile development along pipe
  3. Grid independence plot
  4. Summary table

Usage:
  Place both .xy files in the same folder as this script.
  Run: python post_process_all.py

Author: Arjun (CFD Portfolio - Project 1)
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ============================================================
# PARAMETERS
# ============================================================
rho = 1.225           # kg/m3
mu = 1.789e-5         # Pa.s
R = 0.025             # pipe radius [m]
D = 0.05              # pipe diameter [m]
V_bulk = 14.6         # m/s
Re = 50000

# Wall shear stress from each run (UPDATE these with your values)
tau_w_kep = 0.7138     # k-epsilon, enhanced wall treatment (fine mesh)
tau_w_sst = 0.70485    # SST k-omega (fine mesh)

# Colebrook reference
f_colebrook = 0.0209

# File paths (UPDATE if different)
FILE_KEP = "Axial Vel_Kep model.xy"
FILE_SST = "Vout_SST.xy"

# ============================================================
# PARSER — reads Fluent .xy files with multiple datasets
# ============================================================
def parse_fluent_xy(filepath):
    """Parse Fluent XY export file. Returns dict of {label: (positions, velocities)}"""
    datasets = {}
    current_label = None
    positions = []
    velocities = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Detect dataset label
            if line.startswith('((xy/key/label'):
                # Save previous dataset if exists
                if current_label and positions:
                    datasets[current_label] = (np.array(positions), np.array(velocities))
                # Extract label
                current_label = line.split('"')[1]
                positions = []
                velocities = []
                continue
            
            # End of dataset
            if line == ')':
                if current_label and positions:
                    datasets[current_label] = (np.array(positions), np.array(velocities))
                continue
            
            # Skip header lines
            if line.startswith('(') or not line:
                continue
            
            # Parse data
            try:
                parts = line.split()
                if len(parts) >= 2:
                    positions.append(float(parts[0]))
                    velocities.append(float(parts[1]))
            except ValueError:
                continue
    
    return datasets


def to_wall_coords(y_positions, velocities, tau_w):
    """Convert to u+ vs y+ coordinates"""
    u_tau = np.sqrt(tau_w / rho)
    y_wall = R - y_positions
    
    # Remove points at or beyond the wall
    mask = y_wall > 1e-10
    y_wall = y_wall[mask]
    vel = velocities[mask]
    
    y_plus = y_wall * rho * u_tau / mu
    u_plus = vel / u_tau
    
    # Sort by y+
    idx = np.argsort(y_plus)
    return y_plus[idx], u_plus[idx]


# ============================================================
# PLOT 1: u+ vs y+ — Turbulence Model Comparison
# ============================================================
def plot_u_plus_comparison():
    print("Generating u+ vs y+ comparison plot...")
    
    kep_data = parse_fluent_xy(FILE_KEP)
    sst_data = parse_fluent_xy(FILE_SST)
    
    # Use the last station (xd-60) for fully developed profile
    station = "xd-60"
    
    y_kep, vel_kep = kep_data[station]
    y_sst, vel_sst = sst_data[station]
    
    yp_kep, up_kep = to_wall_coords(y_kep, vel_kep, tau_w_kep)
    yp_sst, up_sst = to_wall_coords(y_sst, vel_sst, tau_w_sst)
    
    # Analytical curves
    yp_visc = np.linspace(0.3, 10, 200)
    up_visc = yp_visc
    
    kappa, B = 0.41, 5.2
    yp_log = np.linspace(10, 2000, 500)
    up_log = (1/kappa) * np.log(yp_log) + B
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    ax.semilogx(yp_kep, up_kep, 'o-', color='#2563EB', markersize=3, linewidth=1.2,
                label=f'k-epsilon (Enhanced WT) | f = {8*tau_w_kep/(rho*V_bulk**2):.5f}', zorder=3)
    ax.semilogx(yp_sst, up_sst, 's-', color='#DC2626', markersize=3, linewidth=1.2,
                label=f'SST k-omega | f = {8*tau_w_sst/(rho*V_bulk**2):.5f}', zorder=3)
    
    ax.semilogx(yp_visc, up_visc, '--', color='#16A34A', linewidth=1.5,
                label='Viscous sublayer: u+ = y+')
    ax.semilogx(yp_log, up_log, '--', color='#6B7280', linewidth=1.5,
                label=f'Log-law: u+ = (1/{kappa}) ln(y+) + {B}')
    
    # Region shading
    ax.axvspan(0.3, 5, alpha=0.04, color='green')
    ax.axvspan(5, 30, alpha=0.04, color='orange')
    ax.axvspan(30, 2000, alpha=0.04, color='blue')
    ax.text(2, 28, 'Viscous\nsublayer', fontsize=8, color='green', ha='center', alpha=0.6)
    ax.text(12, 28, 'Buffer\nlayer', fontsize=8, color='orange', ha='center', alpha=0.6)
    ax.text(200, 28, 'Log-law region', fontsize=8, color='blue', ha='center', alpha=0.6)
    
    ax.set_xlabel('y+', fontsize=13)
    ax.set_ylabel('u+', fontsize=13)
    ax.set_title('Turbulence Model Comparison — Velocity Profile in Wall Coordinates\n'
                 f'Re = {Re:,} | Fine Mesh (72,000 cells) | Outlet (x/D = 60)', fontsize=11)
    ax.legend(fontsize=9, loc='upper left')
    ax.set_xlim(0.3, 2000)
    ax.set_ylim(0, 32)
    ax.grid(True, which='both', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('01_u_plus_y_plus_comparison.png', dpi=200, bbox_inches='tight')
    print("  Saved: 01_u_plus_y_plus_comparison.png")
    plt.show()


# ============================================================
# PLOT 2: Velocity Profile Development (Goal 5)
# ============================================================
def plot_velocity_development():
    print("Generating velocity development plot...")
    
    sst_data = parse_fluent_xy(FILE_SST)
    
    stations = ["xd-10", "xd-20", "xd-30", "xd-40", "xd-50", "xd-60"]
    colors = ['#16A34A', '#2563EB', '#DC2626', '#9333EA', '#EA580C', '#0D9488']
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    for station, color in zip(stations, colors):
        if station in sst_data:
            y_pos, vel = sst_data[station]
            # Sort by radial position
            idx = np.argsort(y_pos)
            y_sorted = y_pos[idx]
            v_sorted = vel[idx]
            # Normalise position by R
            ax.plot(y_sorted / R, v_sorted / V_bulk, '-', color=color, linewidth=1.5,
                    label=f'{station.replace("xd-", "x/D = ")}')
    
    ax.set_xlabel('r / R (radial position normalised by radius)', fontsize=12)
    ax.set_ylabel('u / V_bulk (velocity normalised by bulk velocity)', fontsize=12)
    ax.set_title('Velocity Profile Development Along Pipe\n'
                 f'Re = {Re:,} | SST k-omega | Fine Mesh', fontsize=11)
    ax.legend(fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.3)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('02_velocity_development.png', dpi=200, bbox_inches='tight')
    print("  Saved: 02_velocity_development.png")
    plt.show()


# ============================================================
# PLOT 3: Grid Independence
# ============================================================
def plot_grid_independence():
    print("Generating grid independence plot...")
    
    # UPDATE these with your actual values
    cells =  [10000,  32000,  72000]
    tau_w =  [0.7221, 0.7139, 0.7138]
    f_vals = [8 * t / (rho * V_bulk**2) for t in tau_w]
    errors = [abs(f - f_colebrook) / f_colebrook * 100 for f in f_vals]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    
    # Left: friction factor vs cell count
    ax1.plot(cells, f_vals, 'o-', color='#2563EB', markersize=8, linewidth=2)
    ax1.axhline(y=f_colebrook, color='#DC2626', linestyle='--', linewidth=1.5,
                label=f'Colebrook (f = {f_colebrook})')
    for c, f in zip(cells, f_vals):
        ax1.annotate(f'f = {f:.5f}', (c, f), textcoords="offset points",
                     xytext=(10, 10), fontsize=9)
    ax1.set_xlabel('Number of cells', fontsize=12)
    ax1.set_ylabel('Darcy friction factor (f)', fontsize=12)
    ax1.set_title('Grid Independence — Friction Factor', fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    
    # Right: % error vs cell count
    ax2.plot(cells, errors, 's-', color='#EA580C', markersize=8, linewidth=2)
    ax2.axhline(y=5, color='gray', linestyle=':', linewidth=1, label='5% target')
    for c, e in zip(cells, errors):
        ax2.annotate(f'{e:.1f}%', (c, e), textcoords="offset points",
                     xytext=(10, 10), fontsize=9)
    ax2.set_xlabel('Number of cells', fontsize=12)
    ax2.set_ylabel('Error vs Colebrook (%)', fontsize=12)
    ax2.set_title('Grid Independence — Error Convergence', fontsize=11)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    
    plt.tight_layout()
    plt.savefig('03_grid_independence.png', dpi=200, bbox_inches='tight')
    print("  Saved: 03_grid_independence.png")
    plt.show()


# ============================================================
# SUMMARY TABLE
# ============================================================
def print_summary():
    print("\n" + "="*70)
    print("PROJECT 1 — PIPE FLOW VALIDATION SUMMARY")
    print("="*70)
    
    u_tau_kep = np.sqrt(tau_w_kep / rho)
    u_tau_sst = np.sqrt(tau_w_sst / rho)
    f_kep = 8 * tau_w_kep / (rho * V_bulk**2)
    f_sst = 8 * tau_w_sst / (rho * V_bulk**2)
    err_kep = abs(f_kep - f_colebrook) / f_colebrook * 100
    err_sst = abs(f_sst - f_colebrook) / f_colebrook * 100
    
    print(f"\nFlow conditions:")
    print(f"  Re = {Re:,}")
    print(f"  D = {D*1000:.0f} mm, L = 3 m (L/D = 60)")
    print(f"  V_bulk = {V_bulk} m/s")
    print(f"  rho = {rho} kg/m3, mu = {mu:.3e} Pa.s")
    
    print(f"\nFriction factor comparison (fine mesh, 72,000 cells):")
    print(f"  {'Model':<30} {'tau_w [Pa]':<12} {'u_tau [m/s]':<14} {'f':<10} {'Error':<8}")
    print(f"  {'-'*74}")
    print(f"  {'k-eps (Enhanced WT)':<30} {tau_w_kep:<12.4f} {u_tau_kep:<14.4f} {f_kep:<10.5f} {err_kep:<8.1f}%")
    print(f"  {'SST k-omega':<30} {tau_w_sst:<12.4f} {u_tau_sst:<14.4f} {f_sst:<10.5f} {err_sst:<8.1f}%")
    print(f"  {'Colebrook (analytical)':<30} {'--':<12} {'--':<14} {f_colebrook:<10.5f} {'ref':<8}")
    
    print(f"\nGrid independence (k-eps, Enhanced WT):")
    cells =  [10000, 32000, 72000]
    taus =   [0.7221, 0.7139, 0.7138]
    names =  ['Coarse (50x200)', 'Medium (80x400)', 'Fine (120x600)']
    print(f"  {'Mesh':<20} {'Cells':<10} {'tau_w [Pa]':<12} {'f':<10} {'Error':<8} {'Change':<8}")
    print(f"  {'-'*68}")
    prev_f = None
    for name, c, t in zip(names, cells, taus):
        f = 8 * t / (rho * V_bulk**2)
        err = abs(f - f_colebrook) / f_colebrook * 100
        change = "--" if prev_f is None else f"{abs(f - prev_f)/prev_f * 100:.2f}%"
        print(f"  {name:<20} {c:<10} {t:<12.4f} {f:<10.5f} {err:<8.1f}% {change:<8}")
        prev_f = f
    
    print(f"\nKey findings:")
    print(f"  - Grid independent from medium mesh (0.05% change medium to fine)")
    print(f"  - SST k-omega outperforms k-eps by ~{err_kep - err_sst:.1f} percentage points")
    print(f"  - Flow fully developed by x/D ~ 20-30")
    print(f"  - Lesson: Std wall functions at y+~3 gave wrong tau_w;")
    print(f"    Enhanced wall treatment required for this mesh resolution")
    print("="*70)


# ============================================================
# RUN ALL
# ============================================================
if __name__ == "__main__":
    # Check files exist
    for f in [FILE_KEP, FILE_SST]:
        if not os.path.exists(f):
            print(f"ERROR: Cannot find '{f}' in current directory.")
            print(f"Current directory: {os.getcwd()}")
            print(f"Files here: {os.listdir('.')}")
            exit(1)
    
    plot_u_plus_comparison()
    plot_velocity_development()
    plot_grid_independence()
    print_summary()
    
    print("\nAll plots saved. Add these to your GitHub repo under figures/")
