import numpy as np
import matplotlib.pyplot as plt

# Set up polar plot
fig = plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)

# Create 12 divisions (30° each)
angles = np.linspace(0, 2*np.pi, 13)  # 13 points for 12 divisions
radius = 1  # Constant radius for all divisions

# Sectors to fill (0-based index, starting from 0°)
sectors_to_fill = [1, 3, 6, 8, 10]  # Corresponding to 2nd, 4th, 7th, 9th, 11th sectors

# Plot filled sectors
for i in sectors_to_fill:
    theta = np.linspace(angles[i], angles[i+1], 100)  # 100 points for smooth arc
    ax.fill_between(
        theta,          # Angle values
        0, radius,      # From center to outer edge
        color='black',
        alpha=1
    )

# Remove all grid lines and labels
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.spines['polar'].set_visible(False)

# Set the radial limit
ax.set_rmax(radius)

plt.tight_layout()
plt.show()