from datetime import datetime, timedelta

from .exceptions import StationFullError
from .models import Bike, BikeNetwork, Dock, Rider, Station


def main() -> None:
    station_a = Station(
        "Station A",
        [Dock(1, Bike("B-01")), Dock(2, Bike("B-02")), Dock(3)],
    )
    station_b = Station(
        "Station B",
        [Dock(1)],  # boshida 1 ta bo'sh joy bor
    )
    station_c = Station(
        "Station C",
        [Dock(1), Dock(2), Dock(3)],  # 3 ta bo'sh joy bor
    )

    network = BikeNetwork([station_a, station_b, station_c])
    t0 = datetime(2026, 11, 21, 10, 0, 0)

    # 1. Ikkinchi foydalanuvchi B-01 ni olib, Station B ga qaytaradi -> Station B to'ladi
    rider_other = Rider("Aziz")
    network.take_bike(rider_other, "Station A", t0)
    network.return_bike(rider_other, "Station B", t0 + timedelta(minutes=10))

    # 2. Asosiy foydalanuvchi B-02 ni oladi va to'la Station B ga qaytarmoqchi bo'ladi
    rider = Rider("Islomjon")
    network.take_bike(rider, "Station A", t0)

    try:
        network.return_bike(rider, "Station B", t0 + timedelta(minutes=18))
    except StationFullError as err:
        print(f"Xato: {err}")
        if err.redirect_station:
            print(f"Tavsiya etilgan stansiya: {err.redirect_station.name}")

    # 3. Endi bo'sh joyi bor Station C ga qaytaramiz (18 daqiqa -> 500 sum)
    receipt = network.return_bike(rider, "Station C", t0 + timedelta(minutes=18))
    print("Chek:", receipt)


if __name__ == "__main__":
    main()
