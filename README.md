# Flight Route Optimizer

## Introduction
Choosing a flight is a personal decision. Some travelers prefer the lowest cost, even if it means longer travel time, while others prioritize the shortest duration. For example, one traveler may choose a direct flight from SFO to BOM for speed, while another may opt for a cheaper route with a layover in DXB. There is no single best option—every traveler values something different. Our project aims to determine the most efficient route from a source to a destination based on user preferences: minimizing cost, travel time, or layovers.

We model airports as nodes and flights as directed, weighted edges in a graph. Each edge represents a direct flight, with weights for distance and cost. By representing flight data as a graph, we apply different algorithms to match users’ preferences:
- **DFS**: Enumerates all possible routes (no specific preference)
- **BFS**: Finds routes with minimal layovers
- **Dijkstra’s Algorithm**: Finds the least expensive route

## Setup Instructions

1. **Create a Python virtual environment**
   ```sh
   python3 -m venv .venv
   ```
2. **Activate the virtual environment**
   ```sh
   source .venv/bin/activate
   ```
3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

## Running the Project

- **Test DFS implementation**
  ```sh
  python flight_optimizer_backend.py
  ```
- **Run unit tests**
  ```sh
  python dfs_unit_test.py
  ```
- **Launch the frontend**
  ```sh
  streamlit run flight_optimizer_frontend.py
  ```

## Features
- Enumerate all possible flight routes
- Find routes with minimal layovers
- Find the cheapest route
- Sort and display alternative routes by layover and cost

---
This project demonstrates how graph algorithms can be applied to real-world flight selection, adapting to what each traveler values most.
