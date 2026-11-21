from datetime import datetime, timedelta
import pytest

from src.exceptions import (
    DockOccupiedError,
    NoActiveRideError,
    NoBikeError,
    RideActiveError,
    StationFullError,
)
from src.models import Bike, BikeNetwork, Dock, Rider, Station


def test_fee_tiers_and_cap() -> None:
    st = Station("S1", [Dock(1, Bike("B1"))])
    rider = Rider("Ali")
    t0 = datetime(2026, 11, 21, 12, 0, 0)
    ride = Ride_helper_bike_ride(st, rider, t0)

    assert ride.calculate_fee(t0 + timedelta(minutes=15)) == 0
    assert ride.calculate_fee(t0 + timedelta(minutes=15, seconds=1)) == 500
    assert ride.calculate_fee(t0 + timedelta(minutes=20)) == 500
    assert ride.calculate_fee(t0 + timedelta(minutes=20, seconds=1)) == 1000
    assert ride.calculate_fee(t0 + timedelta(hours=10)) == 20000


def Ride_helper_bike_ride(station: Station, rider: Rider, start_time: datetime):
    from src.models import Ride
    bike = station.docks[0].take_bike()
    return Ride(bike, rider, station, start_time)


def test_invalid_end_time() -> None:
    st = Station("S1", [Dock(1, Bike("B1"))])
    rider = Rider("Ali")
    t0 = datetime(2026, 11, 21, 12, 0, 0)
    ride = Ride_helper_bike_ride(st, rider, t0)

    with pytest.raises(ValueError):
        ride.calculate_fee(t0 - timedelta(seconds=1))


def test_station_full_redirects_by_free_docks_then_name() -> None:
    s_origin = Station("Origin", [Dock(1, Bike("B1")), Dock(2)])
    s_full = Station("FullSt", [Dock(1, Bike("B2"))])
    s_alpha = Station("AlphaSt", [Dock(1), Dock(2)])
    s_beta = Station("BetaSt", [Dock(1), Dock(2)])

    net = BikeNetwork([s_origin, s_full, s_alpha, s_beta])
    t0 = datetime(2026, 11, 21, 10, 0, 0)

    r1 = Rider("R1")
    net.take_bike(r1, "Origin", t0)

    with pytest.raises(StationFullError) as exc_info:
        net.return_bike(r1, "FullSt", t0 + timedelta(minutes=5))

    assert exc_info.value.redirect_station is s_alpha
    assert r1.active_ride is not None


def test_read_only_properties_and_errors() -> None:
    bike = Bike("B1")
    with pytest.raises(AttributeError):
        bike.status = "BROKEN"  # type: ignore[misc]

    dock = Dock(1, bike)
    with pytest.raises(DockOccupiedError):
        dock.put_bike(Bike("B2"))

    rider = Rider("Ali")
    with pytest.raises(NoActiveRideError):
        BikeNetwork([]).return_bike(rider, "Any", datetime(2026, 11, 21, 10, 0, 0))

    empty_st = Station("Empty", [Dock(1)])
    net = BikeNetwork([empty_st])
    with pytest.raises(NoBikeError):
        net.take_bike(rider, "Empty", datetime(2026, 11, 21, 10, 0, 0))

    full_bike_st = Station("HasBike", [Dock(1, Bike("B3"))])
    net2 = BikeNetwork([full_bike_st])
    net2.take_bike(rider, "HasBike", datetime(2026, 11, 21, 10, 0, 0))
    with pytest.raises(RideActiveError):
        net2.take_bike(rider, "HasBike", datetime(2026, 11, 21, 10, 1, 0))
