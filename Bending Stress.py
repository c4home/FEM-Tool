import math

# Input parameters
length_mm = 42.5  # Length of the beam in mm
outer_radius_mm = 15.8  # Outer radius in mm
inner_radius_mm = 6.4  # Inner radius in mm
load_N = 58000  # Load applied at the center in Newtons

# Calculate maximum bending moment (N·mm)
M = (load_N * length_mm) / 4

# Calculate section modulus S (mm^3)
Ro4 = outer_radius_mm ** 4
Ri4 = inner_radius_mm ** 4
S = (math.pi / 4) * (Ro4 - Ri4) / outer_radius_mm

# Calculate maximum bending stress (MPa)
max_bending_stress = M / S  # N/mm^2 = MPa

# Calculate cross-sectional area (mm^2)
section_area = math.pi * (outer_radius_mm ** 2 - inner_radius_mm ** 2)

# Output results
print(f"Beam length: {length_mm} mm")
print(f"Load applied: {load_N} N")
print(f"Maximum bending moment: {M:.2f} N·mm")
print(f"Section modulus: {S:.2f} mm^3")
print(f"Maximum bending stress: {max_bending_stress:.2f} MPa")
print(f"Cross-sectional area: {section_area:.2f} mm^2")
