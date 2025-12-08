# Unit tests for core flight route optimization functions

import unittest
import sys
from typing import Dict, List, Tuple
from flight_optimizer_backend import (
    eliminate_backward_travel,
    available_flights,
    dfs_routes_iterative,
    build_graph_from_json_data,
    calculate_layover_duration,
    connection_validity,
    distance_data
)


# Type definitions matching backend
Flight = Dict
Graph = Dict[str, List[Tuple[str, Flight]]]
DistanceData = Dict[str, Dict[str, float]]


class TestCoreFlightFunctions(unittest.TestCase):
    
    def setUp(self):
        # Setup test data that will be used across multiple tests
        
        # Load actual flight data from JSON file
        import json
        try:
            with open('flight_dataset_updated.json', 'r') as file:
                self.flights = json.load(file)
        except FileNotFoundError:
            print("Error: flight_dataset_updated.json not found")
            self.flights = []
        
        # Build graph from loaded flights
        self.test_graph = build_graph_from_json_data(self.flights)
        
    
    # ==========================================
    # Test 1: Eliminate Backward Travel - Valid Forward Progress
    # ==========================================
    
    def test_eliminate_backward_travel_valid(self):
        # Test that forward progress toward destination is allowed
        # Using real airports: SFO -> DXB -> BOM (moving closer to BOM)
        result = eliminate_backward_travel(
            current_airport="SFO",
            next_airport="DXB",
            destination="BOM",
            distance_data=distance_data,
            source="SFO"
        )
        self.assertTrue(result, "Should allow forward progress from SFO through DXB toward BOM")
    
    # ==========================================
    # Test 2: Eliminate Backward Travel - Invalid Backward Movement
    # ==========================================
    
    def test_eliminate_backward_travel_invalid(self):
        # Test that backward movement away from destination is rejected
        # Using real airports: DXB -> SFO when destination is BOM (moving away)
        result = eliminate_backward_travel(
            current_airport="DXB",
            next_airport="SFO",
            destination="BOM",
            distance_data=distance_data,
            source="DXB"
        )
        self.assertFalse(result, "Should reject backward movement from DXB to SFO when going to BOM")
    
    # ==========================================
    # Test 3: Available Flights - Starting Airport
    # ==========================================
    
    def test_available_flights_at_start(self):
        # Test getting available flights from starting airport
        # Check flights from SFO on Wednesday
        result = available_flights(
            graph=self.test_graph,
            current_airport="SFO",
            arrival_time=None,
            travel_day="Wednesday"
        )
        
        # Should return flights operating on Wednesday from SFO
        self.assertGreater(len(result), 0, "Should return flights on Wednesday from SFO")
        
        # Verify all returned flights operate on Wednesday
        for dest, flight in result:
            self.assertIn("Wednesday", flight.get('days', []), 
                         f"Flight {flight['flight_no']} should operate on Wednesday")
    
    # ==========================================
    # Test 4: Available Flights - With Day Filter
    # ==========================================
    
    def test_available_flights_day_filter(self):
        # Test that day filtering works correctly
        # Get flights from BOM on Monday
        result = available_flights(
            graph=self.test_graph,
            current_airport="BOM",
            arrival_time=None,
            travel_day="Monday"
        )
        
        # Verify flights are available on Monday
        self.assertGreater(len(result), 0, "Should return flights on Monday from BOM")
        
        # Check that all flights operate on Monday
        for dest, flight in result:
            self.assertIn("Monday", flight.get('days', []),
                         f"Flight {flight['flight_no']} should operate on Monday")
    
    # ==========================================
    # Test 5: DFS Routes - Direct Path Found
    # ==========================================
    
    def test_dfs_finds_direct_routes(self):
        # Test that DFS finds direct routes when available
        # Check for direct route SFO -> BOM (AI175 operates Wed, Fri, Sun)
        routes = dfs_routes_iterative(
            flights_graph=self.test_graph,
            distance_data=distance_data,
            start="SFO",
            destination="BOM",
            max_layovers=3,
            travel_day="Wednesday"
        )
        
        # Should find at least one route
        self.assertGreater(len(routes), 0, "Should find at least one route from SFO to BOM")
        
        # Check if there's a direct route (1 leg)
        direct_routes = [r for r in routes if len(r) == 1]
        if direct_routes:
            self.assertEqual(direct_routes[0][0][0], "BOM", "Direct route should reach BOM")
    
    # ==========================================
    # Test 6: DFS Routes - Multiple Paths
    # ==========================================
    
    def test_dfs_finds_multiple_paths(self):
        # Test that DFS finds all valid paths
        # Find routes from SFO to BOM (should have direct and multi-stop options)
        routes = dfs_routes_iterative(
            flights_graph=self.test_graph,
            distance_data=distance_data,
            start="SFO",
            destination="BOM",
            max_layovers=3,
            travel_day="Wednesday"
        )
        
        # Should find at least one route
        self.assertGreater(len(routes), 0, "Should find at least one route from SFO to BOM")
        
        # All routes should end at BOM
        for route in routes:
            self.assertEqual(route[-1][0], "BOM", "All routes should end at BOM")
        
        # Print route summary for verification
        print(f"\n  Found {len(routes)} route(s) from SFO to BOM on Wednesday")
        for i, route in enumerate(routes, 1):
            airports = ["SFO"] + [leg[0] for leg in route]
            print(f"    Route {i}: {' -> '.join(airports)} ({len(route)} leg(s))")
    
    # ==========================================
    # Test 7: DFS Routes - Respects Max Layovers
    # ==========================================
    
    def test_dfs_respects_max_layovers(self):
        # Test that DFS respects maximum layover constraint
        # Find routes with strict layover limit
        routes = dfs_routes_iterative(
            flights_graph=self.test_graph,
            distance_data=distance_data,
            start="SFO",
            destination="BOM",
            max_layovers=2,  # Only allow 2 layovers (3 flights total)
            travel_day="Wednesday"
        )
        
        # All routes should have at most 3 legs
        for route in routes:
            self.assertLessEqual(len(route), 3, 
                               f"Route should have at most 3 legs, got {len(route)}")


# ==========================================
# Test runner
# ==========================================

if __name__ == '__main__':
    # Run all tests with verbose output
    unittest.main(verbosity=2)