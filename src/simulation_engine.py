import heapq

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

    def path_finder(self) -> dict[int, tuple[list[hub], int]]:
        self.build_adjacency()
        results: dict[int, tuple[list[hub], int]] = {}

        for d in self.config.drones:
            path, cost = self.dijkstra_once(d.start_hub, d.end_hub)
            results[d.id] = (path, cost)

        return results

    def turn_scheduler(self):
        pass
