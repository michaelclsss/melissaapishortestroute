import pandas as pd
import folium
from geopy.distance import geodesic
from folium import Popup
import osmnx as ox
import networkx as nx

def visualize_tsp_route(route_csv, geocode_csv, output_html="tsp_route_map.html", label="Route", color="blue"):
    # Load data
    route_df = pd.read_csv(route_csv)
    geo_df = pd.read_csv(geocode_csv)

    geo_df["RecordID"] = geo_df["RecordID"].astype(str)
    route_df["RecordID"] = route_df["RecordID"].astype(str)

    # Merge to get full address + lat/lon
    merged = pd.merge(route_df, geo_df, on="RecordID", how="left")
    if merged[["Latitude", "Longitude"]].isnull().any().any():
        raise ValueError("Missing altitudes or longtitudes.")

    # Compute total distance (in km)
    total_distance = 0
    coords = merged[["Latitude", "Longitude"]].values
    for i in range(1, len(coords)):
        total_distance += geodesic(coords[i-1], coords[i]).km
    total_distance = round(total_distance, 2)

    # Start map at first point
    m = folium.Map(location=coords[0], zoom_start=14)

    # Add markers with full address in popup
    for i, row in merged.iterrows():
        popup_html = f"""
        <b>📍 Step {row['Step']}</b><br>
        <b>RecordID:</b> {row['RecordID']}<br>
        <b>Address:</b> {row.get('InputAddress', '')}, {row.get('City', '')}, {row.get('State', '')} {row.get('Zip', '')}
        """

        popup = Popup(popup_html, max_width=300)

        folium.Marker(
            location=(row["Latitude"], row["Longitude"]),
            popup=popup,
            icon=folium.Icon(color="green" if i == 0 else "red" if i == len(merged)-1 else "blue", icon="info-sign")
        ).add_to(m)

    # Draw route line
    folium.PolyLine(locations=coords.tolist(), color=color, weight=4, opacity=0.8, tooltip=f"{label} ({total_distance} km)").add_to(m)

    # Add total distance on map
        # Add total distance on map with better style
    folium.Marker(
        location=coords[0],
        icon=folium.DivIcon(html=f"""
            <div style="
                display: inline-block;
                font-size: 13px;
                font-weight: normal;
                color: #222;
                background-color: rgba(255, 255, 255, 0.95);
                padding: 8px 14px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                white-space: nowrap;
                margin-top: -10px;
                margin-left: 10px;
            ">
            <span style="font-size: 15px;">🚩</span> <b>{label}</b><br>
            Total Distance: <b>{total_distance} km</b>
            </div>
        """)
    ).add_to(m)


    m.save(output_html)
    print(f"✅ Map saved: {output_html}（Total travel length: {total_distance} km）")


def visualize_distance(routecsv, geocsv):
    # Load and merge route + geocode
    route_df = pd.read_csv(routecsv)
    geo_df = pd.read_csv(geocsv)
    df = pd.merge(route_df, geo_df, on="RecordID")

    # Extract coordinates
    coords = list(zip(df["Latitude"], df["Longitude"]))

    # Get road network graph around area
    G = ox.graph_from_point(coords[0], dist=3000, network_type="drive")

    # Map init
    m = folium.Map(location=coords[0], zoom_start=14)

    # Draw road-based routes
    for i in range(len(coords)-1):
        orig_node = ox.distance.nearest_nodes(G, coords[i][1], coords[i][0])
        dest_node = ox.distance.nearest_nodes(G, coords[i+1][1], coords[i+1][0])
        route = nx.shortest_path(G, orig_node, dest_node, weight="length")
        route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]
        folium.PolyLine(route_coords, color="blue", weight=4).add_to(m)

    # Markers
    for i, (lat, lon) in enumerate(coords):
        folium.Marker([lat, lon], popup=f"Stop {i}").add_to(m)

    m.save("distance_map.html")
    print("✅ distance_map.html saved with real road paths")


