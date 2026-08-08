"""Simulation engine for path finding and turn scheduling."""

import heapq

from pydantic import BaseModel

from .config_maker import Config, connection, hub


ZONE_COST = {
    "normal": 1,
    "priority": 1,
    "restricted": 2,
}


class simulation_engine(BaseModel):
    """Coordinate path finding and turn scheduling for the drones."""

    config: Config | None = None
    adjacency_list: dict[str, list[tuple[hub, connection]]] = {}
    path: list[str] = []
    cost: int = 0

    def build_adjacency(self) -> None:
        """Build the adjacency graph for the configured hubs."""
        assert self.config is not None
        start_name = self.config.start.name
        end_name = self.config.end.name
        assert start_name is not None
        assert end_name is not None
        all_hubs: dict[str, hub] = {
            start_name: self.config.start,
            end_name: self.config.end,
        }
        for hub_item in self.config.hubs:
            if hub_item.name is not None:
                all_hubs[hub_item.name] = hub_item

        self.adjacency_list = {name: [] for name in all_hubs}

        for conn in self.config.connections:
            assert conn.hub1 is not None
            assert conn.hub2 is not None
            if conn.hub2.zone_type != "blocked":
                assert conn.hub1.name is not None
                self.adjacency_list[conn.hub1.name].append((conn.hub2, conn))
            if conn.hub1.zone_type != "blocked":
                assert conn.hub2.name is not None
                self.adjacency_list[conn.hub2.name].append((conn.hub1, conn))

    def dijkstra_once(self, start: hub, end: hub) -> tuple[list[hub], int]:
        """Find the cheapest path from start to end using Dijkstra."""
        assert start.name is not None
        assert end.name is not None
        start_name = start.name
        end_name = end.name
        cheapest_distances: dict[str, int] = {start_name: 0}
        previous_tracker: dict[str, hub] = {}
        visited: set[str] = set()
        priority_queue: list[tuple[int, str, hub]] = [(0, start_name, start)]

        while priority_queue:
            cost, name, current = heapq.heappop(priority_queue)

            if name in visited:
                continue
            visited.add(name)

            if name == end_name:
                break

            for neighbor, _conn in self.adjacency_list.get(name, []):
                assert neighbor.name is not None
                neighbor_name = neighbor.name
                zone_cost = ZONE_COST.get(neighbor.zone_type or "normal", 1)
                new_cost = cost + zone_cost

                if new_cost < cheapest_distances.get(
                    neighbor_name,
                    float("inf"),
                ):
                    cheapest_distances[neighbor_name] = new_cost
                    previous_tracker[neighbor_name] = current
                    heapq.heappush(
                        priority_queue,
                        (new_cost, neighbor_name, neighbor),
                    )

        if end_name not in cheapest_distances:
            return [], -1

        path: list[hub] = [end]
        node = end
        while node.name != start_name:
            assert node.name is not None
            node = previous_tracker[node.name]
            path.append(node)
        path.reverse()

        return path, cheapest_distances[end_name]

    def get_connection(self, hub1: hub, hub2: hub) -> connection | None:
        """Return the connection object between two hubs."""
        assert hub1.name is not None
        assert hub2.name is not None
        for neighbor, conn in self.adjacency_list.get(hub1.name, []):
            if neighbor.name == hub2.name:
                return conn
        return None

    def path_finder(self) -> bool:
        """Find a path for the drones and assign their initial attributes."""
        assert self.config is not None
        self.build_adjacency()
        results: list[tuple[list[str], int]] = []

        hubs, self.cost = self.dijkstra_once(
            self.config.start,
            self.config.end,
        )
        hub_names: list[str] = []
        for hub_item in hubs:
            assert hub_item.name is not None
            hub_names.append(hub_item.name)
        results.append((hub_names, self.cost))

        self.path = hub_names
        self.config.assign_drone_attributes(hubs)
        return True if self.path and self.cost != -1 else False

    def turn_scheduler(self) -> list[tuple[tuple[int, str], ...]]:
        """Compute the turn-by-turn movement schedule for all drones."""
        assert self.config is not None
        turn_log: list[tuple[tuple[int, str], ...]] = []
        start_name = self.config.start.name
        assert start_name is not None
        zone_occupancy: dict[str, int] = {start_name: len(self.config.drones)}
        connection_occupancy: dict[str, int] = {}

        while not all(d.finished for d in self.config.drones):
            turn_moves: dict[int, str] = {}

            for d in self.config.drones:
                if d.finished:
                    continue
                if d.transit_turns_left > 0:
                    assert d.current_hub is not None
                    assert d.transit_target is not None
                    assert d.transit_conn_key is not None
                    d.transit_turns_left -= 1
                    if d.transit_turns_left == 0:
                        assert d.current_hub.name is not None
                        zone_occupancy[d.current_hub.name] -= 1
                        connection_occupancy[d.transit_conn_key] -= 1
                        d.current_hub = d.transit_target
                        d.path_index += 1
                        assert d.current_hub.name is not None
                        zone_occupancy[d.current_hub.name] = (
                            zone_occupancy.get(d.current_hub.name, 0) + 1
                        )
                        assert d.id is not None
                        turn_moves[d.id] = d.current_hub.name
                        if d.current_hub.name == self.config.end.name:
                            d.finished = True
            for d in self.config.drones:
                if d.finished or d.transit_turns_left > 0:
                    continue

                next_hub = d.path[d.path_index + 1]
                assert d.current_hub is not None
                assert next_hub.name is not None
                conn = self.get_connection(d.current_hub, next_hub)
                assert conn is not None
                conn_key = f"{d.current_hub.name}-{next_hub.name}"

                zone_full = zone_occupancy.get(next_hub.name, 0) >= (
                    next_hub.max_drones or 1
                )
                conn_full = connection_occupancy.get(conn_key, 0) >= (
                    conn.max_link_capacity or 1
                )

                if zone_full or conn_full:
                    d.in_queue = True
                    continue

                d.in_queue = False
                assert d.current_hub.name is not None
                zone_occupancy[d.current_hub.name] -= 1
                connection_occupancy[conn_key] = (
                    connection_occupancy.get(conn_key, 0) + 1
                )

                zone_cost = ZONE_COST.get(next_hub.zone_type or "normal", 1)

                if zone_cost == 1:
                    assert next_hub.name is not None
                    zone_occupancy[next_hub.name] = (
                        zone_occupancy.get(next_hub.name, 0) + 1
                    )
                    connection_occupancy[conn_key] -= 1
                    d.current_hub = next_hub
                    d.path_index += 1
                    assert d.id is not None
                    turn_moves[d.id] = next_hub.name
                    if next_hub.name == self.config.end.name:
                        d.finished = True
                else:
                    assert next_hub.name is not None
                    zone_occupancy[next_hub.name] = (
                        zone_occupancy.get(next_hub.name, 0) + 1
                    )
                    d.transit_turns_left = zone_cost
                    d.transit_target = next_hub
                    d.transit_conn_key = conn_key
                    assert d.id is not None
                    turn_moves[d.id] = conn_key

            turn_log.append(tuple(turn_moves.items()))

        return turn_log
