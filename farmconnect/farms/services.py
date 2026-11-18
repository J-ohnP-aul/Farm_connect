"""Grid-snap helper — SDD §5.3, database-design.md §4.1.

Rounds each coordinate to settings.GRID_SNAP_DECIMALS (2 dp ≈ 1.1 km cells),
so the public pin sits within ~800 m of the farm, always inside its cell.
"""

from decimal import ROUND_HALF_EVEN, Decimal

from django.conf import settings
from django.contrib.gis.geos import Point


def grid_snap(point):
    """Return a copy of `point` with coordinates rounded to the snap grid."""
    quantum = Decimal(1).scaleb(-settings.GRID_SNAP_DECIMALS)
    lon = Decimal(str(point.x)).quantize(quantum, rounding=ROUND_HALF_EVEN)
    lat = Decimal(str(point.y)).quantize(quantum, rounding=ROUND_HALF_EVEN)
    return Point(float(lon), float(lat), srid=4326)
