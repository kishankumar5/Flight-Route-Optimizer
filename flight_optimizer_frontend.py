import streamlit as st
import json
from datetime import datetime
from flight_optimizer_backend import (
    build_graph_from_json_data,
    dfs_routes_iterative,
    getOptimalRoute,
    date_to_weekday,
    distance_data,
    calculate_layover_duration,
    calculate_total_travel_time,
    format_duration 
)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Custom CSS for styling flight information display
CUSTOM_CSS = """
    <style>
        .flight-main {
            font-size: 18px !important;
            font-weight: 700 !important;
            padding-top: 4px;
        }
        .flight-sub {
            font-size: 15px !important;
            color: #bbbbbb !important;
            margin-top: 5px;
            margin-bottom: 8px;
        }
        .optimal-route {
            font-size: 22px !important;
            font-weight: 800 !important;
            margin-bottom: 10px;
        }
        .total-cost-label {
            color: white !important;
            font-weight: 700 !important;
            margin-left: 10px;
            font-size: 20px !important;
        }
        .total-cost-value {
            color: green !important;    
            font-weight: 900 !important;
            font-size: 26px !important;
            margin-left: 10px;
        }
        .layover-info {
            font-size: 14px !important;
            color: #ffa500 !important;
            font-weight: 600 !important;
            margin-top: 5px;
            margin-bottom: 5px;
        }
        .travel-time-summary {
            font-size: 16px !important;
            color: #4CAF50 !important;
            font-weight: 600 !important;
            margin-top: 10px;
            margin-bottom: 5px;
        }
    </style>
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data
def load_flight_data():
    """
    Load flight data from JSON file.
    Returns None if file not found, otherwise returns flight data.
    """
    try:
        with open('flight_dataset_updated.json', 'r') as file:
            flights = json.load(file)
        return flights
    except FileNotFoundError:
        st.error("Error: flight_dataset_updated.json not found.")
        return None


def render_flight_leg(current_source, destination_airport, flight):
    """
    Render a single flight leg with formatted details.
    
    Args:
        current_source: Source airport code
        destination_airport: Destination airport code
        flight: Flight details dictionary
    """
    # Render main flight info
    st.markdown(
        f"<div class='flight-main'>{current_source} → {destination_airport} | "
        f"{flight['airline']} - {flight['flight_no']} | "
        f"{flight['departure_time_gmt']} - {flight['arrival_time_gmt']} GMT | "
        f"Cost: ${flight['cost']}</div>",
        unsafe_allow_html=True
    )
    
    # Render flight days
    days_str = ", ".join(flight.get("days", []))
    st.markdown(
        f"<div class='flight-sub'>Days: {days_str}</div>",
        unsafe_allow_html=True
    )


def render_route_details(source, route, show_separator=True):
    """
    Render complete details for a flight route including layover information.
    
    Args:
        source: Starting airport code
        route: List of (airport, flight) tuples
        show_separator: Whether to show separator between flight legs
    """
    for i, (airport, flight) in enumerate(route):
        # Determine source airport for this leg
        current_source = source if i == 0 else route[i - 1][0]
        
        # Render flight leg
        render_flight_leg(current_source, airport, flight)
        
        # Display flight duration
        duration_str = format_duration(flight['duration_mins'])
        st.markdown(
            f"<div class='flight-sub'>Flight Duration: {duration_str}</div>",
            unsafe_allow_html=True
        )
        
        # Calculate and display layover if not the last flight
        if i < len(route) - 1:
            next_flight = route[i + 1][1]
            layover = calculate_layover_duration(
                flight['arrival_time_gmt'],
                next_flight['departure_time_gmt']
            )
            layover_str = format_duration(layover)
            st.markdown(
                f"<div class='layover-info'>⏱️ Layover: {layover_str}</div>",
                unsafe_allow_html=True
            )
        
        # Add separator between legs (except after last leg)
        if show_separator and i < len(route) - 1:
            st.markdown("---")
    
    # Display total travel time summary
    total_flight_time, total_layover_time = calculate_total_travel_time(route, source)
    total_travel_time = total_flight_time + total_layover_time
    
    st.markdown("---")
    st.markdown(
        f"""<div class='travel-time-summary'>
        ✈️ Total Flight Time: {format_duration(total_flight_time)} | 
        ⏱️ Total Layover: {format_duration(total_layover_time)} | 
        🕒 Total Travel Time: {format_duration(total_travel_time)}
        </div>""",
        unsafe_allow_html=True
    )


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="Flight Route Finder",
        page_icon="✈️",
        layout="wide"
    )
    
    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Header
    st.title("Flight Route Finder")
    st.markdown("Find the best flight routes with customizable layover options")
    
    # Load flight data
    flights = load_flight_data()
    if flights is None:
        st.stop()
    
    # Build graph and get available airports
    graph = build_graph_from_json_data(flights)
    airports = sorted(graph.keys())
    
    # ========================================================================
    # USER INPUT SECTION
    # ========================================================================
    if "use_max_layovers" not in st.session_state:
        st.session_state.use_max_layovers = False

    if "get_cheapest_route" not in st.session_state:
        st.session_state.get_cheapest_route = False

    if "get_fastest_route" not in st.session_state:
        st.session_state.get_fastest_route = False


    # ----------------------------
    #       TOGGLE FUNCTIONS
    # ----------------------------
    def toggle_limit():
        if st.session_state.use_max_layovers:
            st.session_state.get_cheapest_route = False
            st.session_state.get_fastest_route = False


    def toggle_cheapest():
        if st.session_state.get_cheapest_route:
            st.session_state.use_max_layovers = False
            st.session_state.get_fastest_route = False


    def toggle_fastest():
        if st.session_state.get_fastest_route:
            st.session_state.use_max_layovers = False
            st.session_state.get_cheapest_route = False


    # ----------------------------
    #       INPUT UI BLOCK
    # ----------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        source = st.selectbox(
            "Source Airport *",
            airports,
            index=airports.index("SFO")
        )

    with col2:
        destination = st.selectbox(
            "Destination Airport *",
            airports,
            index=airports.index("BOM")
        )

    with col3:
        departure_date = st.date_input(
            "Departure Date (Optional)",
            value=None
        )

    with col4:
        departure_time = st.time_input(
            "Departure Time (Optional)",
            value=None
        )


    # ----------------------------
    #    LAYOVER + MODE OPTIONS
    # ----------------------------
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        use_max_layovers = st.checkbox(
            "Limit Maximum Layovers (Default: 3)",
            key="use_max_layovers",
            on_change=toggle_limit
        )

        max_layovers = st.number_input(
            "Maximum Layovers",
            min_value=1,
            max_value=5,
            value=3
        ) if st.session_state.use_max_layovers else 3


    with col6:
        get_cheapest_route = st.checkbox(
            "Cheapest",
            key="get_cheapest_route",
            on_change=toggle_cheapest
        )


    with col7:
        get_fastest_route = st.checkbox(
            "Fastest",
            key="get_fastest_route",
            on_change=toggle_fastest
        )
    # ========================================================================
    # ROUTE SEARCH
    # ========================================================================
    
    if st.button("Search Routes", type="primary"):
        # Validate input
        if source == destination:
            st.error("Source and destination airports must be different!")
            st.stop()
        
        # Search for routes
        with st.spinner("Searching for routes..."):
            # Prepare optional parameters
            travel_day = date_to_weekday(str(departure_date)) if departure_date else None
            user_departure_time = departure_time.strftime("%H:%M") if departure_time else None
            
            # Execute route search
            if st.session_state.use_max_layovers:
                # BFS with layover limit
                # remove the below two lines after the comments and replace it with
                # bfs implementation so that when checked it routes to bfs
                optimal_route = getOptimalRoute(graph,source,destination,'cost')
                routes = [optimal_route] if optimal_route else []
            elif st.session_state.get_cheapest_route:
                optimal_route = getOptimalRoute(graph,source,destination,'cost')
                routes = [optimal_route] if optimal_route else []
            elif st.session_state.get_fastest_route:
                optimal_route = getOptimalRoute(graph,source,destination,'duration')
                routes = [optimal_route] if optimal_route else []
            else:
                routes = dfs_routes_iterative(
                    graph,
                    distance_data,
                    source,
                    destination,
                    max_layovers=max_layovers,
                    min_layover=90,
                    user_departure_time=user_departure_time,
                    travel_day=travel_day
                )
            # st.error(routes)
            # Validate results
            if not routes:
                st.warning("No routes found.")
                st.stop()
            
            # Filter for complete routes that reach destination
            complete_routes = [rt for rt in routes if rt[-1][0] == destination]
            if not complete_routes:
                st.warning("No complete routes reach the destination.")
                complete_routes = routes
            
            # Sort routes by total cost
            route_costs = sorted(
                [(rt, sum(f["cost"] for _, f in rt)) for rt in complete_routes],
                key=lambda x: x[1]
            )
            # st.error(route_costs[0])
        
        # ====================================================================
        # DISPLAY OPTIMAL ROUTE
        # ====================================================================
        
        st.markdown("---")
        st.subheader("Optimal Route")
        
        cheapest_route, cheapest_cost = route_costs[0]
        airports_list = [source] + [leg[0] for leg in cheapest_route]
        route_path = " → ".join(airports_list)
        
        # Display route overview with total cost
        st.markdown(
            f"""
            <div class="optimal-route">
                {route_path}
                <span class="total-cost-label">Total Cost:</span>
                <span class="total-cost-value">${cheapest_cost}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Display detailed flight information
        st.markdown("##### Flight Details")
        render_route_details(source, cheapest_route, show_separator=True)
        
        # ====================================================================
        # DISPLAY ALTERNATIVE ROUTES
        # ====================================================================
        
        if len(route_costs) > 1:
            st.markdown("---")
            st.subheader("Other Available Routes")
            
            # Display each alternative route in an expander
            for idx, (route, total_cost) in enumerate(route_costs[1:], start=2):
                # Format route path for header
                airports_list = [source] + [leg[0] for leg in route]
                route_path = " → ".join(airports_list)
                
                # Display route in expander
                with st.expander(f"Route {idx}: {route_path} | ${total_cost}"):
                    st.markdown("##### Flight Details")
                    render_route_details(source, route, show_separator=True)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
    
    