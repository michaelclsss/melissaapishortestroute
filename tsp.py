import pandas as pd
import numpy as np
from geocode import use_api
from distance_calculation import construct_matrix
from visualize import visualize_tsp_route,visualize_distance
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve_tsp_with_start(distance_csv, start_id, selected_ids=None):
    # Load distance matrix
    df = pd.read_csv(distance_csv, index_col=0)
    df.index = df.index.astype(str)
    df.columns = df.columns.astype(str)
    start_id = str(start_id)

    if start_id not in df.index:
        raise ValueError(f"❌ RecordID {start_id} is not in the distance matrix.")

    if selected_ids:
        selected_ids = [str(i) for i in selected_ids]
        if start_id not in selected_ids:
            selected_ids.insert(0, start_id)
    else:
        selected_ids = df.index.tolist()

    reordered_ids = [start_id] + [i for i in selected_ids if i != start_id]
    df = df.loc[reordered_ids, reordered_ids]

    # Convert km to meters and build OR-Tools distance matrix
    distance_matrix = (df.values * 1000).astype(int)
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        print("❌ No route found. Please check your input.")
        return

    # Retrieve route path
    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))  # Return to start

    ordered_ids = [reordered_ids[i] for i in route]
    result_df = pd.DataFrame({
        "Step": range(len(ordered_ids)),
        "RecordID": ordered_ids
    })

    result_df.to_csv("shortest_route_custom_start.csv", index=False)
    print("✅ Route saved to shortest_route_custom_start.csv")
    print(result_df)

def run_tcs():
    print("📍 Custom Start TSP Route Solver\n")
    user_file = input("Enter file of your csv with locations formatted as:(RecordID,Address,City,State,Zip): ")
    key = input("Enter Melissa API License key: ")
    use_api(key, user_file)
    construct_matrix()
    start_point = input("Enter the starting RecordID: ").strip()
    raw_targets = input("Enter RecordIDs to visit (comma-separated), or leave blank to include all: ").strip()

    selected_ids = None
    if raw_targets:
        selected_ids = [s.strip() for s in raw_targets.split(',') if s.strip().isdigit()]

    solve_tsp_with_start("distance_matrix_km.csv", start_point, selected_ids)
    visualize_tsp_route("shortest_route_custom_start.csv", "geocode.csv")
    visualize_distance("shortest_route_custom_start.csv", "geocode.csv")
    
