from __future__ import annotations

from datetime import datetime
from .exceptions import (
    DockOccupiedError,
    NoActiveRideError,
    NoBikeError,
    RideActiveError,
    StationFullError,
)


class Bike:
    """Velosiped: ID va holat (@property orqali himoyalangan)."""

    def __init__(self, bike_id: str) -> None:
        self._bike_id = bike_id
        self._status = "AVAILABLE"

    @property
    def bike_id(self) -> str:
        return self._bike_id

    @property
    def status(self) -> str:
        return self._status

    def mark_in_use(self) -> None:
        self._status = "IN_USE"

    def mark_available(self) -> None:
        self._status = "AVAILABLE"


class Dock:
    """Stansiya ichidagi bitta joy."""

    def __init__(self, dock_id: int, bike: Bike | None = None) -> None:
        self._dock_id = dock_id
        self._bike: Bike | None = bike

    @property
    def dock_id(self) -> int:
        return self._dock_id

    @property
    def bike(self) -> Bike | None:
        return self._bike

    @property
    def is_free(self) -> bool:
        return self._bike is None

    def put_bike(self, bike: Bike) -> None:
        if self._bike is not None:
            raise DockOccupiedError(f"Dock {self._dock_id} is already occupied.")
        bike.mark_available()
        self._bike = bike

    def take_bike(self) -> Bike:
        if self._bike is None:
            raise NoBikeError(f"Dock {self._dock_id} has no bike.")
        bike = self._bike
        self._bike = None
        bike.mark_in_use()
        return bike


class Station:
    """Stansiya: nomi va docklar ro'yxati."""

    def __init__(self, name: str, docks: list[Dock]) -> None:
        self._name = name
        self._docks = list(docks)

    @property
    def name(self) -> str:
        return self._name

    @property
    def docks(self) -> tuple[Dock, ...]:
        return tuple(self._docks)

    def free_docks_count(self) -> int:
        return sum(1 for d in self._docks if d.is_free)


class Ride:
    """Safar: vaqt va narx (int so'mda) hisoblaydi."""

    def __init__(
        self,
        bike: Bike,
        rider: Rider,
        origin: Station,
        start_time: datetime,
    ) -> None:
        self._bike = bike
        self._rider = rider
        self._origin = origin
        self._start_time = start_time

    @property
    def bike(self) -> Bike:
        return self._bike

    @property
    def rider(self) -> Rider:
        return self._rider

    @property
    def origin(self) -> Station:
        return self._origin

    @property
    def start_time(self) -> datetime:
        return self._start_time

    def calculate_fee(self, end_time: datetime) -> int:
        if end_time < self._start_time:
            raise ValueError("end_time cannot be earlier than start_time.")

        seconds = (end_time - self._start_time).total_seconds()
        if seconds <= 15 * 60:
            return 0

        extra_seconds = seconds - 15 * 60
        steps = int((extra_seconds + 300 - 1) // 300)
        fee = steps * 500
        return min(fee, 20000)


class Rider:
    """Foydalanuvchi."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._active_ride: Ride | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def active_ride(self) -> Ride | None:
        return self._active_ride

    def set_active_ride(self, ride: Ride | None) -> None:
        self._active_ride = ride


class ReceiptPrinter:
    """Safar chekini formatlaydi."""

    def format_receipt(
        self,
        ride: Ride,
        destination: Station,
        end_time: datetime,
        fee: int,
    ) -> str:
        minutes = int((end_time - ride.start_time).total_seconds() // 60)
        return (
            f"{ride.origin.name} -> {destination.name}, "
            f"{minutes} min, {fee} sum"
        )


class BikeNetwork:
    """Stansiyalar, safarlar va qayta yo'naltirishni boshqaradi."""

    def __init__(
        self,
        stations: list[Station],
        printer: ReceiptPrinter | None = None,
    ) -> None:
        self._stations = list(stations)
        self._printer = printer or ReceiptPrinter()

    def _get_station(self, station_name: str) -> Station:
        for st in self._stations:
            if st.name == station_name:
                return st
        raise ValueError(f"Station not found: {station_name}")

    def _find_redirect_station(self, exclude_name: str) -> Station | None:
        candidates = [
            st for st in self._stations
            if st.name != exclude_name and st.free_docks_count() > 0
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda st: (-st.free_docks_count(), st.name))
        return candidates[0]

    def take_bike(
        self,
        rider: Rider,
        station_name: str,
        start_time: datetime,
    ) -> Ride:
        if rider.active_ride is not None:
            raise RideActiveError("Rider already has an active ride.")

        station = self._get_station(station_name)
        for dock in station.docks:
            if not dock.is_free:
                bike = dock.take_bike()
                ride = Ride(bike, rider, station, start_time)
                rider.set_active_ride(ride)
                return ride

        raise NoBikeError(f"No available bike at station {station.name}.")

    def return_bike(
        self,
        rider: Rider,
        station_name: str,
        end_time: datetime,
    ) -> str:
        ride = rider.active_ride
        if ride is None:
            raise NoActiveRideError("Rider has no active ride.")

        if end_time < ride.start_time:
            raise ValueError("end_time cannot be earlier than start_time.")

        station = self._get_station(station_name)
        free_dock = next((d for d in station.docks if d.is_free), None)
        if free_dock is None:
            redirect = self._find_redirect_station(station.name)
            raise StationFullError(
                f"Station {station.name} is full.",
                redirect_station=redirect,
            )

        free_dock.put_bike(ride.bike)
        fee = ride.calculate_fee(end_time)
        rider.set_active_ride(None)
        return self._printer.format_receipt(ride, station, end_time, fee)
