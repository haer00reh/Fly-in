"""Parser utilities for interpreting configuration files."""

import sys

from pydantic import BaseModel, FilePath


class Parser(BaseModel):
    """Parse and validate simulator configuration text."""

    path: FilePath
    config_as_text: str = ""
    config_table: dict[int, str] = {}

    def extract(self) -> None:
        """Read the configuration file into memory."""
        with open(self.path, "r") as file:
            self.config_as_text = file.read()

    def error_teller(self, additional_message: str, line_nb: int) -> None:
        """Report a parser error and exit the process."""
        if line_nb > 0:
            print(
                f"WATCH OUT!!\nError on line {line_nb}: {additional_message}",
                file=sys.stderr,
            )
        else:
            print(f"WATCH OUT!!\nError: {additional_message}", file=sys.stderr)
        sys.exit(1)

    def garbage_remover(self) -> None:
        """Remove comments and empty lines from the parsed config."""
        prefixes = (
            "nb_drones:",
            "start_hub:",
            "end_hub:",
            "hub:",
            "connection:",
        )
        for key, line in list(self.config_table.items()):
            if line.startswith('#'):
                self.config_table.pop(key)
        for key, value in self.config_table.items():
            self.config_table[key] = value.partition("#")[0].rstrip()

        for key, line in list(self.config_table.items()):
            if not line.strip():
                self.config_table.pop(key)
        for line in self.config_table.values():
            if not line.startswith("nb_drones:"):
                self.error_teller("first line must be nb_drones:", 1)
            else:
                break

        for key, line in self.config_table.items():
            if not line.startswith(prefixes) and line in {" ", "\t", "\n"}:
                self.error_teller(f"invalid prefix '{line}'", key)

    def initializer(self) -> None:
        """Initialize the config table from the raw config text."""
        self.config_table = {}
        for line_nb, line in enumerate(
            self.config_as_text.splitlines(),
            start=1,
        ):
            line = line.strip()
            value = line
            self.config_table[line_nb] = value
        self.garbage_remover()

    def do_your_job(self) -> None:
        """Parse and inspect the configuration file."""
        try:
            self.extract()
            if not self.inspect():
                sys.exit(1)
        except Exception as exc:
            print(
                f"WATCH OUT!!\nthere was an error that occurred: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)

    def inspect(self) -> bool:
        """Validate that all required config prefixes are present."""
        prefixes = [
            "nb_drones:",
            "start_hub:",
            "end_hub:",
            "hub:",
            "connection:",
        ]
        start_count = 0
        end_count = 0
        nb_drones_count = 0
        self.initializer()
        for key, line in self.config_table.items():
            if line.startswith("start_hub:"):
                start_count += 1
            elif line.startswith("end_hub:"):
                end_count += 1
            elif line.startswith("nb_drones:"):
                nb_drones_count += 1

            if line.startswith("start_hub:") and start_count > 1:
                self.error_teller(
                    "found another start_hub, there must be exactly one "
                    "start_hub",
                    key,
                )
            elif line.startswith("end_hub:") and end_count > 1:
                self.error_teller(
                    "found another end_hub, there must be exactly one "
                    "end_hub",
                    key,
                )
            elif line.startswith("nb_drones:") and nb_drones_count > 1:
                self.error_teller(
                    "found another nb_drones, there must be exactly one "
                    "nb_drones",
                    key,
                )

        for line in self.config_table.values():
            if line.startswith(tuple(prefixes)):
                prefixes.remove(line.split(":", 1)[0] + ":")
        if not prefixes:
            return True
        self.error_teller(f"Missing prefixes: {prefixes}", 0)
        return False
