class BikeNetworkError(Exception):
    """Base error for bike network."""


class DockOccupiedError(BikeNetworkError):
    """Raised when trying to put a bike into a dock that already has a bike."""


class RideActiveError(BikeNetworkError):
    """Raised when a rider tries to take a bike while already on a ride."""


class NoBikeError(BikeNetworkError):
    """Raised when a station has no available bike to take."""


class NoActiveRideError(BikeNetworkError):
    """Raised when a rider tries to return a bike without an active ride."""


class StationFullError(BikeNetworkError):
    """Raised when a station has no free dock on return."""

    def __init__(self, message: str, redirect_station=None) -> None:
        super().__init__(message)
        self.redirect_station = redirect_station
