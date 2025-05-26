import numpy as np
import matplotlib.pyplot as plt

# Set up polar plot
fig = plt.figure(figsize=(10, 10))
ax = plt.subplot(111, polar=True)

# Parameters for spiral
n_rotations = 3
theta = np.linspace(0, 2*np.pi*n_rotations, 1000)
growth_factor = 2
base = growth_factor**(1/(2*np.pi))
r = base**theta

# Plot the logarithmic spiral (blue)
ax.plot(theta, r, 'b-', linewidth=2)

# Create 12 divisions (30° each)
angles = np.linspace(0, 2*np.pi, 13)  # 13 points for 12 divisions
max_radius = r.max()

# Draw dividing lines (light gray)
for angle in angles[:-1]:
    ax.plot([angle, angle], [0, max_radius], color='lightgray', linestyle='-', linewidth=1)

# Sectors to fill (0-based index)
sectors_to_fill = [1, 3, 6, 8, 10]  # 2nd, 4th, 7th, 9th, 11th sectors

# Fill specified sectors (black)
for i in sectors_to_fill:
    sector_theta = np.linspace(angles[i], angles[i+1], 100)
    ax.fill_between(sector_theta, 0, max_radius, color='black', alpha=0.7)

# Configure plot appearance
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.spines['polar'].set_visible(False)
ax.set_rmax(max_radius)

plt.tight_layout()
plt.show()