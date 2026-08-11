import sys


def link_parser(line: str | None, line_nb: int | None) -> int | None:
    """Parse and validate the link capacity metadata."""
    if line is None or line_nb is None:
        return None
    if "max_link_capacity" in line:
        max_link_capacity = line.split("max_link_capacity=")[1].split()[0]
        try:
            if int(max_link_capacity) <= 0:
                print(
                    (
                        "WATCH OUT!!\n"
                        f"Error in line {line_nb}: invalid "
                        f"max_link_capacity '{max_link_capacity}'"
                    ),
                    file=sys.stderr,
                )
                sys.exit(1)
        except ValueError:
            print(
                (
                    "WATCH OUT!!\n"
                    f"Error in line {line_nb}: invalid "
                    f"max_link_capacity '{max_link_capacity}'"
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        return int(max_link_capacity)
    return None


def hub_parser(
    line: str | None,
    line_nb: int | None,
) -> tuple[str | None, int | None, str | None]:
    """Parse and validate hub metadata from a config line."""
    if line is None or line_nb is None:
        return (None, None, None)

    color_value: str | None = None
    max_drones_value: int | None = None
    zone_value: str | None = None
    meta_prefixes = ("color=", "max_drones=", "zone=")
    zone_prefixes = ("normal", "restricted", "blocked", "priority")
    if "color=" in line:
        color = line.split("color=")[1].split()[0]
        color_value = color.replace(']', '')
    if "max_drones=" in line:
        max_drones = line.split("max_drones=")[1].split()[0].split("]")[0]
        if int(max_drones) <= 0:
            print(
                (
                    "WATCH OUT!!\n"
                    f"Error in line {line_nb}: invalid "
                    f"max_drones '{max_drones}'"
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        max_drones_value = int(max_drones)
    if "zone=" in line:
        zone_type = line.split("zone=")[1].split()[0].split("]")[0]
        if zone_type not in zone_prefixes:
            print(
                (
                    "WATCH OUT!!\n"
                    f"Error in line {line_nb}: invalid zone type "
                    f"'{zone_type}'"
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        zone_value = zone_type
    elif not any(prefix in line for prefix in meta_prefixes):
        print(
            (
                "WATCH OUT!!\n"
                f"Error in line {line_nb}: invalid meta data '{line}'"
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    return (color_value, max_drones_value, zone_value)
