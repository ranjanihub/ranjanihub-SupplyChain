import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import networkx as nx

st.set_page_config(page_title="Supply Chain Optimization", layout="wide")
st.title("🚚 Supply Chain Optimization Management")

st.subheader("1️⃣ Enter Warehouse Details")

# Initialize session state
if "warehouses" not in st.session_state:
    st.session_state.warehouses = []

with st.form("warehouse_form"):
    name = st.text_input("Warehouse Name")
    lat = st.text_input("Latitude")
    lon = st.text_input("Longitude")
    submitted = st.form_submit_button("Add Warehouse")

    if submitted:
        try:
            lat, lon = float(lat), float(lon)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                st.session_state.warehouses.append({"Name": name, "Latitude": lat, "Longitude": lon})
                st.success(f"Added: {name}")
            else:
                st.error("Latitude must be between -90 and 90, Longitude between -180 and 180.")
        except ValueError:
            st.error("Please enter valid numeric values for latitude and longitude.")

# Convert to DataFrame
df = pd.DataFrame(st.session_state.warehouses)

st.subheader("2️⃣ Cleaned Warehouse Data")
st.dataframe(df)

# Show Map
if not df.empty:
    st.subheader("3️⃣ Warehouse Location Map")

    # Initialize Folium Map
    avg_lat = df["Latitude"].mean()
    avg_lon = df["Longitude"].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=5)

    for _, row in df.iterrows():
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            popup=row["Name"],
            icon=folium.Icon(color='blue')
        ).add_to(m)

    st_data = st_folium(m, width=1000, height=500)

    # Build graph and compute path
    st.subheader("4️⃣ Optimized Warehouse Route")

    # Build graph
    G = nx.Graph()
    for i, row_i in df.iterrows():
        for j, row_j in df.iterrows():
            if i != j:
                dist = geodesic(
                    (row_i["Latitude"], row_i["Longitude"]),
                    (row_j["Latitude"], row_j["Longitude"])
                ).km
                G.add_edge(i, j, weight=dist)

    # Find optimized path (simple TSP using Nearest Neighbor)
    def nearest_neighbor_path(G, start=0):
        visited = [start]
        current = start
        while len(visited) < len(G.nodes):
            next_node = min(
                (node for node in G.nodes if node not in visited),
                key=lambda node: G[current][node]["weight"]
            )
            visited.append(next_node)
            current = next_node
        return visited + [start]  # return to start

    if len(df) >= 2:
        path_indices = nearest_neighbor_path(G)
        path_names = [df.iloc[i]["Name"] for i in path_indices]
        st.markdown("**Optimized Visit Order:**")
        st.write(" ➡️ ".join(path_names))

        # Add path to map
        for i in range(len(path_indices) - 1):
            loc1 = (df.iloc[path_indices[i]]["Latitude"], df.iloc[path_indices[i]]["Longitude"])
            loc2 = (df.iloc[path_indices[i+1]]["Latitude"], df.iloc[path_indices[i+1]]["Longitude"])
            folium.PolyLine([loc1, loc2], color="red", weight=2.5, opacity=1).add_to(m)

        st_folium(m, width=1000, height=500)
    else:
        st.info("Please enter at least 2 warehouses to compute optimized path.")
