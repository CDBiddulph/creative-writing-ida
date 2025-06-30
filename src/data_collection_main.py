"""Entry point for the data collection system."""

from pathlib import Path
from .data_collection.config import parse_data_collection_args
from .data_collection.experiment import Experiment


def main() -> None:
    """
    Run a data collection experiment to generate improved examples.

    Parses command line arguments, creates and runs an experiment,
    and outputs the final command to use the generated examples.
    """
    config = parse_data_collection_args()
    base_dir = Path("experiments")
    experiment = Experiment(config, base_dir)
    experiment.run()


if __name__ == "__main__":
    main()
