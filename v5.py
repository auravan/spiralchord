import numpy as np
import matplotlib.pyplot as plt

# Set up polar plot with logarithmic radial scale
fig = plt.figure(figsize=(10, 10))
ax = plt.subplot(111, polar=True)

# Spiral parameters
n_rotations = 3  # Number of full rotations
b = np.log(2)/(2*np.pi)  # Growth rate for doubling each rotation (e^(bθ))
theta = np.linspace(0, 2*np.pi*n_rotations, 1000)
r = np.exp(b * theta)  # Logarithmic spiral r = e^(bθ)

# Create logarithmic radial scale
ax.set_rscale('log')
ax.set_rticks([2**n for n in range(n_rotations+1)])  # 1, 2, 4, 8...
ax.set_yticklabels([f'$2^{{{n}}}$' for n in range(n_rotations+1)])  # LaTeX labels

# Plot the logarithmic spiral (blue)
ax.plot(theta, r, 'b-', linewidth=2, alpha=0.7)

# Create 12 divisions (30° each)
angles = np.linspace(0, 2*np.pi, 13)  # 13 points for 12 divisions

# Draw dividing lines (light gray)
for angle in angles[:-1]:
    ax.plot([angle, angle], [1, 2**n_rotations], color='lightgray', linestyle='-', linewidth=0.5)

# Sectors to fill (0-based index)
sectors_to_fill = [1, 3, 6, 8, 10]  # 2nd, 4th, 7th, 9th, 11th sectors

# Fill specified sectors (black)
for i in sectors_to_fill:
    sector_theta = np.linspace(angles[i], angles[i+1], 100)
    ax.fill_between(sector_theta, 1, 2**n_rotations, color='black', alpha=0.3)

# Configure plot appearance
ax.set_xticks(angles[:-1])
ax.set_xticklabels([f'{int(np.degrees(ang))}°' for ang in angles[:-1]])
ax.grid(True, which='both', alpha=0.3)
ax.set_title("Logarithmic Spiral with Doubling Radius per Rotation", pad=20)

plt.tight_layout()
plt.show()