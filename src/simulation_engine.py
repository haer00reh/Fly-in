import heapq
from os import path

from config_maker import Config, hub, connection, drone, start_hub, end_hub
from pydantic import BaseModel


ZONE_COST = {
    "normal": 1,
    "priority": 1,
    "restricted": 2,
}


class simulation_engine(BaseModel):
    config: Config | None = None
    adjacency_list: dict[str, list[tuple[hub, connection]]] = {}
    path: list[str] = []
    cost: int = 0

    def build_adjacency(self) -> None:
        all_hubs = {self.config.start.name: self.config.start,
                    self.config.end.name: self.config.end}
        for h in self.config.hubs:
            all_hubs[h.name] = h

        self.adjacency_list = {name: [] for name in all_hubs}

        for conn in self.config.connections:
            h1, h2 = conn.hub1, conn.hub2
            if h2.zone_type != "blocked":
                self.adjacency_list[h1.name].append((h2, conn))
            if h1.zone_type != "blocked":
                self.adjacency_list[h2.name].append((h1, conn))

    def dijkstra_once(self, start: hub, end: hub) -> tuple[list[hub], int]:
        cheapest_distances: dict[str, int] = {start.name: 0}
        previous_tracker: dict[str, hub] = {}
        visited: set[str] = set()
        priority_queue: list[tuple[int, str, hub]] = [(0, start.name, start)]

        while priority_queue:
            cost, name, current = heapq.heappop(priority_queue)

            if name in visited:
                continue
            visited.add(name)

            if name == end.name:
                break

            for neighbor, conn in self.adjacency_list.get(name, []):
                zone_cost = ZONE_COST.get(neighbor.zone_type or "normal", 1)
                new_cost = cost + zone_cost

                if new_cost < cheapest_distances.get(neighbor.name, float("inf")):
                    cheapest_distances[neighbor.name] = new_cost
                    previous_tracker[neighbor.name] = current
                    heapq.heappush(priority_queue, (new_cost, neighbor.name, neighbor))

        if end.name not in cheapest_distances:
            return [], -1

        path: list[hub] = [end]
        node = end
        while node.name != start.name:
            node = previous_tracker[node.name]
            path.append(node)
        path.reverse()

        return path, cheapest_distances[end.name]

    def get_connection(self, hub1: hub, hub2: hub) -> connection | None:
        for neighbor, conn in self.adjacency_list.get(hub1.name, []):
            if neighbor.name == hub2.name:
                return conn
        return None

    def path_finder(self) -> bool:
        self.build_adjacency()
        results: list = []

        hubs, self.cost = self.dijkstra_once(self.config.start, self.config.end)
        results.append(( [hub.name for hub in hubs], self.cost ))

        self.path = [hub.name for hub in hubs]
        self.config.assign_drone_attributes(hubs)
        return True if self.path and self.cost != -1 else False

    def turn_scheduler(self) -> list[str]:
        turn_log: list[str] = []
        zone_occupancy = {self.config.start.name: len(self.config.drones)}
        connection_occupancy: dict[str, int] = {}

        while not all(d.finished for d in self.config.drones):
            turn_moves: list[str] = []

            for d in self.config.drones:
                if d.finished:
                    continue
                if d.transit_turns_left > 0:
                    d.transit_turns_left -= 1
                    if d.transit_turns_left == 0:
                        zone_occupancy[d.current_hub.name] -= 1
                        connection_occupancy[d.transit_conn_key] -= 1 
                        d.current_hub = d.transit_target
                        d.path_index += 1
                        zone_occupancy[d.current_hub.name] = zone_occupancy.get(d.current_hub.name, 0) + 1
                        turn_moves.append(f"D{d.id}-{d.current_hub.name}")
                        if d.current_hub.name == self.config.end.name:
                            d.finished = True
            for d in self.config.drones:
                if d.finished or d.transit_turns_left > 0:
                    continue

                next_hub = d.path[d.path_index + 1]
                conn = self.get_connection(d.current_hub, next_hub)
                conn_key = f"{d.current_hub.name}-{next_hub.name}"

                zone_full = zone_occupancy.get(next_hub.name, 0) >= (next_hub.max_drones or 1)
                conn_full = connection_occupancy.get(conn_key, 0) >= (conn.max_link_capacity or 1)

                if zone_full or conn_full:
                    d.in_queue = True
                    continue

                d.in_queue = False
                zone_occupancy[d.current_hub.name] -= 1
                connection_occupancy[conn_key] = connection_occupancy.get(conn_key, 0) + 1

                zone_cost = ZONE_COST.get(next_hub.zone_type or "normal", 1)

                if zone_cost == 1:
                    zone_occupancy[next_hub.name] = zone_occupancy.get(next_hub.name, 0) + 1
                    connection_occupancy[conn_key] -= 1
                    d.current_hub = next_hub
                    d.path_index += 1
                    turn_moves.append(f"D{d.id}-{next_hub.name}")
                    if next_hub.name == self.config.end.name:
                        d.finished = True
                else:
                    zone_occupancy[next_hub.name] = zone_occupancy.get(next_hub.name, 0) + 1
                    d.transit_turns_left = zone_cost
                    d.transit_target = next_hub
                    d.transit_conn_key = conn_key
                    turn_moves.append(f"D{d.id}-{conn_key}")

            turn_log.append(" ".join(turn_moves))

        return turn_log
