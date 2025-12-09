"""
This file contains BFS (Breadth-First Search) implementation for flight route optimization.
Based on the DFS implementation structure in flight_optimizer.py.
"""

# Importing modules needed for flight route optimization
# - json for handling JSON data
# - datetime and timedelta for managing dates and times
# - typing for type hinting complex data structures
# - collections.deque for BFS queue implementation

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import deque

# Storing flight as a dictionary 
# Example: {"flight_no": "AA101", "airline": "American Airlines", ..}

Flight = Dict

# - The key is a city/airport name (string)
# - The value is a list of edges (connections)

# Example:
# graph["A"] = [("B", flight1), ("C", flight2)]

Graph = Dict[str, List[Tuple[str, Flight]]]

# Distance data structure
# - The key is the source city/airport (string)
# - The value is another dictionary where:
# - The key is the destination city/airport (string)
# - The value is the distance in miles (float)

# Example:
# {"A" : {"B": 300.0, "C": 450.0}}

DistanceData = Dict[str, Dict[str, float]]


# This code block loads flight data from a JSON file named 'flight_dataset_updated'

# Open JSON file in read mode 'r'
with open('flight_dataset_updated.json', 'r') as file:
    flights = json.load(file)  # Load JSON data into 'flights' variable
    
# Print the number of flights loaded 
print(f"Loaded {len(flights)} flights")

# Print 1 datapoint as a sample
print("\nSample flight:")
print(json.dumps(flights[0], indent=1))


# Distance Data between airports (Nodes) in miles

# Example: 
# distance_data["SFO"]["BOM"] gives distance from SFO to BOM = 8450 miles

# Used to eliminate backward travel in route optimization
# Example: If traveling from SFO to BOM, it should eliminate routes that go away from BOM 
# (e.g., SFO -> DXB -> LHR -> BOM) 


distance_data = {
    "SFO": {
        "SFO": 0, "BOM": 8450, "LHR": 5360, "DXB": 8090, "PEK": 5570, 
        "SIN": 8446, "JFK": 2586, "CDG": 5565, "FRA": 5690, "NRT": 5120
    },
    "BOM": {
        "SFO": 8450, "BOM": 0, "LHR": 4470, "DXB": 1195, "PEK": 2900, 
        "SIN": 2450, "JFK": 7790, "CDG": 4400, "FRA": 4210, "NRT": 4280
    },
    "LHR": {
        "SFO": 5360, "BOM": 4470, "LHR": 0, "DXB": 3410, "PEK": 5090, 
        "SIN": 6760, "JFK": 3450, "CDG": 215, "FRA": 395, "NRT": 5950
    },
    "DXB": {
        "SFO": 8090, "BOM": 1195, "LHR": 3410, "DXB": 0, "PEK": 3950, 
        "SIN": 3650, "JFK": 6840, "CDG": 3250, "FRA": 3000, "NRT": 4900
    },
    "PEK": {
        "SFO": 5570, "BOM": 2900, "LHR": 5090, "DXB": 3950, "PEK": 0, 
        "SIN": 2790, "JFK": 6800, "CDG": 5060, "FRA": 4810, "NRT": 1320
    },
    "SIN": {
        "SFO": 8446, "BOM": 2450, "LHR": 6760, "DXB": 3650, "PEK": 2790, 
        "SIN": 0, "JFK": 9530, "CDG": 6750, "FRA": 6400, "NRT": 3330
    },
    "JFK": {
        "SFO": 2586, "BOM": 7790, "LHR": 3450, "DXB": 6840, "PEK": 6800, 
        "SIN": 9530, "JFK": 0, "CDG": 3635, "FRA": 3850, "NRT": 6730
    },
    "CDG": {
        "SFO": 5565, "BOM": 4400, "LHR": 215, "DXB": 3250, "PEK": 5060, 
        "SIN": 6750, "JFK": 3635, "CDG": 0, "FRA": 280, "NRT": 6050
    },
    "FRA": {
        "SFO": 5690, "BOM": 4210, "LHR": 395, "DXB": 3000, "PEK": 4810, 
        "SIN": 6400, "JFK": 3850, "CDG": 280, "FRA": 0, "NRT": 5930
    },
    "NRT": {
        "SFO": 5120, "BOM": 4280, "LHR": 5950, "DXB": 4900, "PEK": 1320, 
        "SIN": 3330, "JFK": 6730, "CDG": 6050, "FRA": 5930, "NRT": 0
    }
}


# Function to build graph from flight data
# Build adjacency list graph from flight data
# Key is source airport
# Value is list of tuples (destination airport, flight data)


def build_graph_from_json_data(flights: List[Flight]) -> Graph:
    #Build adjacency list graph from flight data
    
    graph: Graph = {} #empty dictionary
    for flight in flights:
        
        source = flight['source']
        destination = flight['destination']
        
        
        # Calculate duration in minutes 
        # Covert HH:MM to integer minutes        
        
        dep_hr, dep_min = map(int, flight['departure_time_gmt'].split(':'))
        arr_hr, arr_min = map(int, flight['arrival_time_gmt'].split(':'))
        
        # Convert to minutes since midnight
        dep_total_mins = dep_hr * 60 + dep_min
        arr_total_mins = arr_hr * 60 + arr_min
        
        # Calculate duration in minutes. Modulo 24 hours to handle overnight flights
        duration_mins = (arr_total_mins - dep_total_mins) % (24 * 60)
        
        # Create edge data dictionary
        edge_data = {
            'flight_no': flight['flight_no'],
            'airline': flight['airline'],
            'days': flight['days'],
            'departure_time_gmt': flight['departure_time_gmt'],
            'arrival_time_gmt': flight['arrival_time_gmt'],
            'duration_mins': duration_mins,
            'distance_miles': flight['distance_miles'],
            'cost': flight['cost']
        }
        
        # Add source to graph if not present
        if source not in graph:
            graph[source] = [] #adds source as key with empty list as value
        
        # Append destination and edge data to the source's adjacency list
        graph[source].append((destination, edge_data))
        
    return graph


def calculate_total_travel_time(route: List[Tuple[str, Flight]], start: str) -> Tuple[int, int]:
    """
    Calculate total travel time for a route including flight time and layovers.
    """
    if not route:
        return 0, 0
    
    total_flight_time = 0
    total_layover_time = 0
    
    for _, flight in route:
        total_flight_time += flight.get('duration_mins', 0)
    
    for i in range(len(route) - 1):
        current_flight = route[i][1]
        next_flight = route[i + 1][1]
        layover = calculate_layover_duration(
            current_flight['arrival_time_gmt'],
            next_flight['departure_time_gmt']
        )
        total_layover_time += layover
    
    return total_flight_time, total_layover_time


def format_duration(minutes: float) -> str:
    """Format duration in minutes to a human-readable string."""
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    if hours > 0:
        return f"{hours}h"
    return f"{mins}m"


def parse_time(time_string: str) -> datetime:
    # Convert time string '02:30' to datetime object to facilitate time calculations
    
    return datetime.strptime(time_string, "%H:%M")


def calculate_layover_duration(arrival_time: str, next_leg_time: str) -> float: #returns duration in float
    #Calculate layover duration in minutes betweeen arrival and next leg departure
    
    #Convert time strings to datetime objects
    arrival = parse_time(arrival_time)
    departure = parse_time(next_leg_time)
    
    #if next leg departs before arrival, assume it's the next day
    if departure < arrival:
        departure = departure + timedelta(days=1)
        
    # Calculate difference in minutes
    layover_minutes = (departure - arrival).total_seconds() / 60
    return layover_minutes


def connection_validity(arrival: str, departure: str, minimum_layover: int = 90) -> bool: #returns true/false depending on layover >= 90
    #Check if connection is valid (minimum layover time)
    
    layover = calculate_layover_duration(arrival, departure)
    
    return layover >= minimum_layover


#Get available flights from current airport
#returns list of tuples (destination airport, flight data)

def available_flights(
    graph: Graph, 
    current_airport: str, 
    arrival_time: Optional[str], 
    layover_time: int = 90, 
    travel_day: Optional[str] = None) -> List[Tuple[str, Flight]]:  
    
    
    #when travel_day is empty string, set to None
    if travel_day == '':
        travel_day = None
    
    #get all flights from current airport
    outgoing_flights = graph.get(current_airport, [])
    
    #Arrival time is NONE at the starting airport
    if arrival_time is None:
        #user has no preference on travel day -> return all outgoing flights
        if travel_day is None:
            return outgoing_flights
        
        #else return flights on the user specified travel_day
        return [(destination, flight) for destination, flight in flights if travel_day in flight.get('days', [])]
    
    
    #Check layover time when not at starting airport
    available = []
    for destination, flight in outgoing_flights:
        
        #if travel_day specified, filter flights by day
        if travel_day is not None and travel_day not in flight.get('days', []):
            continue #skip this flight
        
        #check if connection is valid based on layover time
        if connection_validity(arrival_time, flight['departure_time_gmt'], layover_time):
            available.append((destination, flight))
            
    return available


    
def eliminate_backward_travel(current_airport, next_airport, destination, distance_data, source) -> bool:
    """Function to eliminate backward travel (zig-zag routes)"""
    
    try:
        # If next layover is the destination, always allow it
        if next_airport == destination:
            return True
        
        # Get distances
        distance_current_to_dest = distance_data[current_airport][destination]
        distance_next_to_dest = distance_data[next_airport][destination]
        
        # Reject if moving away from destination
        if distance_next_to_dest >= distance_current_to_dest:
            return False
        
        # Reject if the next airport is too far from current airport
        # The distance between current and next should not exceed the remaining distance to destination
        distance_current_to_next = distance_data[current_airport][next_airport]
        
        # If the leg distance is greater than the remaining distance to destination, it's inefficient
        if distance_current_to_next > distance_current_to_dest:
            return False
        
        # Check geographical efficiency relative to source
        distance_source_to_next = distance_data[source][next_airport]
        distance_source_to_dest = distance_data[source][destination]
        
        # The next airport should be closer to source than destination is
        if distance_source_to_next > distance_source_to_dest:
            return False
        
        return True
        
    except KeyError as missing_data:        
        print(f"Warning: Missing distance data - {missing_data}")
        return True


#Function to convert date string to weekday (to facilitate flight day filtering)

def date_to_weekday(date_str: str) -> Optional[str]: #retruns weekday name or none in a string
    #Convert date string to weekday name
    
    # Handle empty date string
    if not date_str:
        return None    
    
    try:
        # Convert date string to datetime object
        date_object = datetime.strptime(date_str, "%Y-%m-%d")
        return date_object.strftime('%A') #returns weekday name
    
    #retrun None in case of error, e.g., invalid date format
    except Exception:
        return None

#Function to return next day wehn date string is given
def get_next_available_day(current_date_str: str) -> Optional[str]: #retruns next day weekday name or none in a string
    #Get the next day's weekday name
    
    # Handle empty date string
    if not current_date_str:
        return None
    
    try:
        # Convert date string to datetime object
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
        # Calculate next date
        next_date = current_date + timedelta(days=1)
        #return next day's weekday name
        return next_date.strftime('%A')
    except Exception:
        return None
    

def bfs_routes_iterative(flights_graph: Graph, 
                         distance_data: DistanceData, 
                         start: str, 
                         destination: str, 
                         max_layovers: int = 3, 
                         min_layover: int = 90, 
                         user_departure_time: Optional[str] = None, 
                         travel_day: Optional[str] = None) -> List[List[Tuple[str, Flight]]]:
    
    #Iterative BFS algorithm to enumerate all possible routes from start to destination
    all_routes: List[List[Tuple[str, Flight]]] = []
    
    # Get starting flights 
    if user_departure_time is None:
        starting_flights = flights_graph.get(start, [])
    else:
        starting_flights = [
            (dest, flight)
            for dest, flight in flights_graph.get(start, [])
            if parse_time(flight['departure_time_gmt']) >= parse_time(user_departure_time)
        ]
        
    # Filter starting flights by travel day if specified    
    if travel_day is not None:
        starting_flights = [(dest, flight) for dest, flight in starting_flights 
                            if travel_day in flight.get('days', [])]
        
    #Queue-based BFS   
    # Iterate over each starting flight     
    for next_airport, flight in starting_flights:
        queue = deque([(next_airport, 
                      [(next_airport, flight)],
                      {start, next_airport},
                      flight['arrival_time_gmt'])])
        
        
        #BFS         
        while queue:
            current_airport, path, visited, arrival_time = queue.popleft()
            
            # Check if destination reached
            if current_airport == destination:
                all_routes.append(path[:])
                continue
            
            # Limit layovers
            if len(path) > max_layovers:
                continue
            
            
            #Get next available flights from current airport            
            next_flights = available_flights(flights_graph, 
                                            current_airport, 
                                            arrival_time, 
                                            min_layover, 
                                            travel_day)
            
            
            # Explore each next flight
            for next_airport, next_flight in next_flights:
                # Proceed only if next_airport not visited
                if next_airport in visited:
                    continue
                    
                #Backward travel elimination - NOW PASSES source (start)
                if not eliminate_backward_travel(current_airport, 
                                                     next_airport, 
                                                     destination, 
                                                     distance_data,
                                                     start):  # Added start parameter
                    continue
                
                #Build updated path and visited set   
                new_visited = visited | {next_airport}
                new_path = path + [(next_airport, next_flight)]
                
                #Add to queue                
                queue.append((next_airport, 
                              new_path, 
                              new_visited, 
                              next_flight['arrival_time_gmt']))
    
    return all_routes


def print_routes_formatted(routes: List[List[Tuple[str, Flight]]], start: str):
    #Print routes in detailed format (aligned with backend formatting)
    if not routes:
        print("No routes found.")
        return
    
    for i, route in enumerate(routes, 1):
        airports = [start] + [leg[0] for leg in route]
        print(f"\n{'='*50}")
        print(f"Route {i}: {' - '.join(airports)}")
        print('='*50)
        
        total_cost = 0
        current_source = start
        
        for j, (airport, flight) in enumerate(route):
            total_cost += flight.get('cost', 0)
            
            days = flight.get('days', [])
            if isinstance(days, list):
                days_str = (", ".join(days) if len(days) <= 3 else f"{len(days)} days/week")
            else:
                days_str = str(days)
            
            print(f"\n{current_source} → {airport}")
            print(f"  Flight:     {flight.get('flight_no')} ({flight.get('airline')})")
            print(f"  Departure:  {flight.get('departure_time_gmt')} GMT")
            print(f"  Arrival:    {flight.get('arrival_time_gmt')} GMT")
            print(f"  Duration:   {format_duration(flight.get('duration_mins', 0))}")
            print(f"  Days:       {days_str}")
            print(f"  Cost:       ${flight.get('cost', 0)}")
            
            if j < len(route) - 1:
                next_flight = route[j + 1][1]
                layover = calculate_layover_duration(
                    flight['arrival_time_gmt'],
                    next_flight['departure_time_gmt']
                )
                print(f"  Layover:    {format_duration(layover)}")
            
            current_source = airport
        
        total_flight_time, total_layover_time = calculate_total_travel_time(route, start)
        total_travel_time = total_flight_time + total_layover_time
        
        print(f"\n{'─'*50}")
        print(f"Total Flight Time: {format_duration(total_flight_time)}")
        print(f"Total Layover Time: {format_duration(total_layover_time)}")
        print(f"Total Travel Time: {format_duration(total_travel_time)}")
        print(f"Total Cost: ${total_cost}")
        print(f"{'─'*50}\n")


def print_routes_compact(routes: List[List[Tuple[str, Flight]]], start: str):
    #Print routes in compact format
    if not routes:
        print("No routes found.")
        return
    
    for i, route in enumerate(routes, 1):
        leg_airports = [start] + [leg[0] for leg in route]
        print(f"Route {i}: {' -> '.join(leg_airports)}")
        
        for airport, flight in route:
            
            days = flight.get("days", [])
            if isinstance(days, list):
                days_str = ", ".join(days)
            else:
                days_str = str(days)
            
            print(f"  {airport}: {flight['flight_no']} | {flight['airline']} | "
                  f"dep {flight['departure_time_gmt']} arr {flight['arrival_time_gmt']} | "
                  f"days {flight.get('days')}")
        print()


if __name__ == "__main__":
    # Build the graph and distance data
    graph = build_graph_from_json_data(flights)

    print("Graph built successfully!")
    print(f"Number of airports: {len(graph)}")
    print(f"Airports: {', '.join(sorted(graph.keys()))}")


    # Configuration
    source = 'SFO'
    destination = 'BOM'
    travel_date = '2025-02-23'
    max_layovers = 3
    min_layover = 90

    # Resolve weekday
    travel_day = date_to_weekday(travel_date)
    next_day = get_next_available_day(travel_date)

    print(f"Travel date: {travel_date} ({travel_day})")
    print(f"Next available day: {next_day}")
    print(f"\nSearching for routes from {source} to {destination}...\n")

    # Find routes using BFS
    routes = bfs_routes_iterative(graph, distance_data, source, destination, 
                       max_layovers=max_layovers, min_layover=min_layover, 
                       travel_day=travel_day)

    print(f"Found {len(routes)} route(s) using BFS")
    print_routes_formatted(routes, source)


    # Find routes using iterative BFS
    routes_iterative = bfs_routes_iterative(graph, distance_data, source, destination, 
                                           max_layovers=max_layovers, min_layover=min_layover, 
                                           travel_day=travel_day)

    print(f"Found {len(routes_iterative)} route(s) using Iterative BFS")
    print_routes_formatted(routes_iterative, source)


    # Find routes without day restriction
    print(f"Searching for routes from {source} to {destination} (any day)...\n")

    routes_any_day = bfs_routes_iterative(graph, distance_data, source, destination, 
                               max_layovers=max_layovers, min_layover=min_layover, 
                               travel_day=None)

    print(f"Found {len(routes_any_day)} route(s) for any day")
    print_routes_formatted(routes_any_day, source)


    # Find routes with minimum departure time
    departure_time = '18:00'
    print(f"Searching for routes from {source} to {destination} departing after {departure_time}...\n")

    routes_with_time = bfs_routes_iterative(graph, distance_data, source, destination, 
                                 max_layovers=max_layovers, min_layover=min_layover, 
                                 user_departure_time=departure_time, travel_day=None)

    print(f"Found {len(routes_with_time)} route(s) departing after {departure_time}")
    print_routes_formatted(routes_with_time, source)


    # Compare routes for different days
    days_to_check = ['Monday', 'Wednesday', 'Friday', 'Saturday']

    for day in days_to_check:
        routes_by_day = bfs_routes_iterative(graph, distance_data, source, destination, 
                                   max_layovers=max_layovers, min_layover=min_layover, 
                                   travel_day=day)
        print(f"{day}: {len(routes_by_day)} route(s) available")
        if routes_by_day:
            costs = [sum(flight['cost'] for _, flight in route) for route in routes_by_day]
            print(f"  Cost range: ${min(costs)} - ${max(costs)}")
        print()


    # Find route with minimum stops
    if routes_any_day:
        min_stops_route = min(routes_any_day, key=lambda r: len(r))
        print(f"Route with minimum stops ({len(min_stops_route)} stop(s)):")
        print_routes_formatted([min_stops_route], source)
    else:
        print("No routes found")


    # Find cheapest route
    if routes_any_day:
        cheapest_route = min(routes_any_day, 
                            key=lambda r: sum(flight['cost'] for _, flight in r))
        total_cost = sum(flight['cost'] for _, flight in cheapest_route)
        print(f"Cheapest route (${total_cost}):")
        print_routes_formatted([cheapest_route], source)
    else:
        print("No routes found")

