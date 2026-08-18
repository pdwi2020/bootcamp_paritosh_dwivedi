"""Command-line entry point for the stakeholder presentation build."""

from pathlib import Path

from src.presentation import build_presentation


def main() -> None:
    """Build the deck from the project containing this script."""

    project_root = Path(__file__).resolve().parent
    print(build_presentation(project_root))


if __name__ == "__main__":
    main()
