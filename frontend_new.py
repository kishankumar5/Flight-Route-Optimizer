import streamlit as st
import json
from datetime import datetime

# Import functions from flight_optimizer.py
from flight_optimizer import (
    build_graph_from_json_data,
    dfs_routes_iterative,
    date_to_weekday,
    distance_data
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
        with open('flight_dataset.json', 'r') as file:
            flights = json.load(file)
        return flights
    except FileNotFoundError:
        st.error("Error: flight_dataset.json not found.")
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
    Render complete details for a flight route.
    
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
        
        # Add separator between legs (except after last leg)
        if show_separator and i < len(route) - 1:
            st.markdown("---")


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
    
    # Layover configuration
    col5 = st.columns(3)[0]
    with col5:
        use_max_layovers = st.checkbox(
            "Limit Maximum Layovers (Default: 3)",
            value=False
        )
        max_layovers = st.number_input(
            "Maximum Layovers",
            1, 5, 3
        ) if use_max_layovers else 3
    
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
    
    