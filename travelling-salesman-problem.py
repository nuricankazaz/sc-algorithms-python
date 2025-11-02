from gurobipy import Model, GRB, quicksum
import pandas as pd, math, folium

landmarks = [
    ("New Istanbul Airport", 41.2753, 28.7519),  # Start/End
    ("Hagia Sophia / Sultanahmet", 41.008469, 28.980261),
    ("Topkapi Palace", 41.011574, 28.983269),
    ("Blue Mosque (Sultanahmet Mosque)", 41.005745, 28.977114),
    ("Grand Bazaar", 41.010658, 28.968058),
    ("Eminönü / Spice Bazaar area", 41.01478, 28.9694),
    ("Galata Tower", 41.025658, 28.974155),
    ("Taksim Square", 41.036945, 28.985832),
    ("İstiklal Avenue (approx center)", 41.033806, 28.977905),
    ("Karaköy (Galata Bridge north end)", 41.0225, 28.9733),
    ("Ortaköy", 41.04806, 29.02361),
    ("Beşiktaş (ferry/center)", 41.0439, 29.0073),
    ("Kadıköy (ferry/center)", 41.0427, 29.0073)
]

df = pd.DataFrame(landmarks, columns=["name","lat","lon"]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

n = len(df)
N = range(n)
dist = {(i,j): haversine(df.lat[i], df.lon[i], df.lat[j], df.lon[j])
        for i in N for j in N if i != j}

# Model
m = Model("TSP_Istanbul_Airport")
x = m.addVars(dist.keys(), vtype=GRB.BINARY, name="x")
u = m.addVars(N, vtype=GRB.CONTINUOUS, lb=0, ub=n-1, name="u")

# Objective
m.setObjective(quicksum(dist[i,j]*x[i,j] for i,j in dist), GRB.MINIMIZE)


# Constraints: each node exactly one in/out, except start=0
for i in N:
    m.addConstr(quicksum(x[i,j] for j in N if j != i) == 1)
    m.addConstr(quicksum(x[j,i] for j in N if j != i) == 1)

# Fix start at 0 (airport)
# ensure tour starts and ends there
for i in N:
    for j in N:
        if i != j and i != 0 and j != 0:
            m.addConstr(u[i] - u[j] + n*x[i,j] <= n-1)

m.optimize()

# Extract optimal route
edges = [(i,j) for i,j in dist if x[i,j].x > 0.5]
route = [0]
while len(route) < n:
    next_city = [j for (i,j) in edges if i == route[-1]][0]
    route.append(next_city)
route.append(0)

# Display
print("\nOptimal TSP Route (Start/End: New Istanbul Airport):")
for r in route:
    print(df.loc[r,"name"])
total_distance = sum(dist[i,j] for i,j in zip(route[:-1], route[1:]))
print(f"\nTotal distance: {total_distance:.2f} km")

# --- Folium Map ---
istanbul_center = [41.02, 28.97]
mymap = folium.Map(location=istanbul_center, zoom_start=11)

# Add route polyline
points = [(df.lat[i], df.lon[i]) for i in route]
folium.PolyLine(points, color="blue", weight=3, opacity=0.7).add_to(mymap)

# Add markers
for idx, row in df.iterrows():
    folium.Marker([row.lat, row.lon],
                  popup=f"{idx}: {row.name}",
                  icon=folium.Icon(color="red" if idx == 0 else "green")).add_to(mymap)

mymap
