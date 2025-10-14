"""CodeCarbon integration for tracking platform emissions."""
import os
from contextlib import contextmanager

from codecarbon import EmissionsTracker
from loguru import logger


class UCIPCarbonTracker:
    """Track carbon emissions of the UCIP platform itself."""

    def __init__(
        self,
        project_name: str = "UCIP",
        output_dir: str = "./emissions",
        enabled: bool = True,
    ):
        """Initialize carbon tracker.
        
        Args:
            project_name: Project name
            output_dir: Directory for emissions logs
            enabled: Whether tracking is enabled
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.enabled = enabled and os.getenv("CODECARBON_ENABLED", "true").lower() == "true"
        
        if self.enabled:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"CodeCarbon tracking enabled for {project_name}")
        else:
            logger.info("CodeCarbon tracking disabled")

    @contextmanager
    def track(self, task_name: str = "default"):
        """Context manager for tracking emissions.
        
        Args:
            task_name: Name of the task being tracked
        """
        if not self.enabled:
            yield
            return
        
        tracker = EmissionsTracker(
            project_name=f"{self.project_name}-{task_name}",
            output_dir=self.output_dir,
            log_level="warning"
        )
        
        tracker.start()
        logger.info(f"Started tracking emissions for task: {task_name}")
        
        try:
            yield tracker
        finally:
            emissions = tracker.stop()
            if emissions:
                logger.info(
                    f"Task '{task_name}' emissions: {emissions:.6f} kg CO2eq"
                )

    def get_total_emissions(self) -> float:
        """Get total platform emissions.
        
        Returns:
            Total emissions in kg CO2eq
        """
        # Read emissions from log file
        import pandas as pd
        
        emissions_file = os.path.join(self.output_dir, "emissions.csv")
        
        if os.path.exists(emissions_file):
            df = pd.read_csv(emissions_file)
            total = df['emissions'].sum()
            logger.info(f"Total platform emissions: {total:.6f} kg CO2eq")
            return total
        
        return 0.0


# Global tracker instance
tracker = UCIPCarbonTracker()


def main():
    """Example usage."""
    # Track a model training task
    with tracker.track("model_training"):
        # Simulate work
        import time
        import numpy as np
        
        for i in range(10):
            _ = np.random.rand(1000, 1000) @ np.random.rand(1000, 1000)
            time.sleep(0.1)
    
    # Get total emissions
    total = tracker.get_total_emissions()
    logger.info(f"Total emissions: {total:.6f} kg CO2eq")


if __name__ == "__main__":
    main()

