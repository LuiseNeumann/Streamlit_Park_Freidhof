import math
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class WorkforceCalculator:
    """Handles calculations for workforce and equipment needs."""
    
    @staticmethod
    def calculate_required_workers(area_ha: float) -> int:
        """
        Calculate required workers based on area in hectares.
        
        Args:
            area_ha: Area in hectares
            
        Returns:
            Number of required workers (minimum 1)
        """
        try:
            area_m2 = area_ha * 10000
            minutes = area_m2 * Config.AREA_TO_MINUTES_FACTOR
            hours = minutes / 60
            days = hours / Config.WORKING_HOURS_PER_DAY
            workers = days / Config.WORKING_DAYS_PER_YEAR
            
            result = max(1, math.ceil(workers))
            logger.debug(f"Calculated {result} workers for {area_ha} ha")
            return result
            
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Error calculating workers for area {area_ha}: {e}")
            return 1
    
    @staticmethod
    def calculate_required_bikes(workers: int) -> int:
        """
        Calculate required bikes based on number of workers.
        
        Args:
            workers: Number of workers
            
        Returns:
            Number of required bikes
        """
        try:
            bikes = math.ceil(workers / Config.WORKERS_PER_BIKE)
            logger.debug(f"Calculated {bikes} bikes for {workers} workers")
            return bikes
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Error calculating bikes for {workers} workers: {e}")
            return 1
        
    @staticmethod
    def calculate_static_bikes() -> int:
        """
        static number of bikes for every camp
        """
        try:
            bikes = math.ceil(4 / 2)
            logger.debug(f"Calculated {bikes}")
            return bikes
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Error calculating static bikes: {e}")
            return 1