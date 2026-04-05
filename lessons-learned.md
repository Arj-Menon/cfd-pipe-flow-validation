# Lessons Learned — Pipe Flow Validation

## 1. Wall Treatment Must Match y⁺

**Problem:** Standard wall functions produced τ_w = 1.22 Pa (f = 0.037), nearly double the Colebrook value of 0.021.

**Root cause:** Standard wall functions assume the first cell centroid lies in the log-law region (y⁺ > 30). Our mesh was designed for y⁺ ≈ 1–3, placing the first cell inside the viscous sublayer. The wall function applied the log-law formula at y⁺ = 3, where it doesn't hold, and computed a shear stress that was physically wrong.

**Fix:** Switched to Enhanced Wall Treatment, which uses a blended formulation that transitions smoothly from the viscous sublayer (u⁺ = y⁺) through the buffer layer to the log-law. Result: τ_w dropped to 0.72 Pa (f = 0.022), within 5% of Colebrook.

**Rule of thumb:**
- y⁺ < 5 → Enhanced Wall Treatment or SST k-ω (resolves sublayer)
- 5 < y⁺ < 30 → Avoid this range (buffer layer, neither formulation is ideal)
- y⁺ > 30 → Standard wall functions are valid

## 2. Grid Independence Is Cheap for 2D Axisymmetric

Running three meshes (10k, 32k, 72k cells) took minutes total. There is no excuse for skipping grid independence in a 2D simulation. The coarse mesh had 5.9% error; the medium mesh brought it to 4.7% with only 1.1% change; the fine mesh confirmed convergence at 0.05% change. In practice, the medium mesh was sufficient.

## 3. SST k-ω vs k-ε at Low y⁺

At y⁺ ≈ 3, SST k-ω (3.3% error) outperformed k-ε with Enhanced Wall Treatment (4.7% error). This is expected — SST k-ω was specifically designed to handle the near-wall region through its ω-based formulation, while k-ε relies on a blending function that is an approximation.

For this mesh resolution, SST k-ω is the better choice. The difference is small (1.4 percentage points) but consistent.

## 4. Entry Length Verification Is Non-Negotiable

The pipe was 60 diameters long. Velocity profiles showed the flow was fully developed by x/D ≈ 20. Without checking this, we would be comparing CFD results against an analytical solution that assumes fully developed conditions — comparing apples to oranges. Always verify your assumptions.

## 5. Convergence Monitors Beat Residuals

Residuals dropping below 10⁻⁵ is necessary but not sufficient. The wall shear stress monitor flatlined well before residuals reached their final values. Physical monitors (forces, flow rates, shear stress) are the real convergence indicators.
