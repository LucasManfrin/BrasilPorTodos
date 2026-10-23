"""Reviewed fiscal auxiliary series: public readers use their dedicated reports."""

from app.integrations.treasury_composition import COMPOSITION_SERIES
from app.integrations.treasury_interest import INTEREST_SERIES

AUXILIARY_CODES = tuple(COMPOSITION_SERIES) + tuple(INTEREST_SERIES)
