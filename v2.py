import numpy as np
import matplotlib.pyplot as plt

# Set up polar plot
fig = plt.figure(figsize=(10, 10))
ax = plt.subplot(111, polar=True)

# Spiral parameters
n_rotations = 3  # Number of full rotations
theta = np.linspace(0, 2*np.pi*n_rotations, 1000)  # Angle values
growth_factor = 2  # Radius doubles each full rotation (2π)

# Logarithmic spiral: r = base^(θ/(2π)) 
# So each full rotation (θ increases by 2π) makes r → r*growth_factor
base = growth_factor**(1/(2*np.pi))
r = base**theta  # Equivalent to: r = e^(θ*ln(base))

# Plot spiral
ax.plot(theta, r, 'b-', linewidth=2)

# Set logarithmic radial scale
ax.set_rscale('log')
ax.set_rticks([2**n for n in range(n_rotations+1)])  # 1, 2, 4, 8...
ax.set_yticklabels([f"$2^{{{n}}}$" for n in range(n_rotations+1)])  # LaTeX labels

# Draw radial lines at 30° intervals (12 divisions)
for k in range(12):
    angle = k * np.pi/6
    ax.plot([angle, angle], [1, 2**n_rotations], 'r--', alpha=0.5)

ax.grid(True)
plt.tight_layout()
plt.show()