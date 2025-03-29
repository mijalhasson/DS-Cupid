import pytest
import pandas as pd
from api.core.service import (
    get_matched_rooms,
    get_unmatched_rooms,
    map_rooms,
    reference_room_match,
    match_hotel_rooms,
    normalize_room_name,
)


def test_get_matched_rooms():
    df1 = pd.DataFrame({"processed_room_name": ["Deluxe King", "Standard Twin"]})
    df2 = pd.DataFrame({"processed_room_name": ["Deluxe King Room", "Twin Standard"]})
    result = get_matched_rooms(df1, df2)
    assert len(result) == 2
    assert result.iloc[0]["match_score"] >= 80


def test_get_unmatched_rooms():
    df = pd.DataFrame({"room_id": [1, 2, 3], "processed_room_name": ["A", "B", "C"]})
    df_matched = pd.DataFrame({"room_id": [1, 2], "processed_room_name": ["A", "B"]})
    result = get_unmatched_rooms(df, df_matched, "processed_room_name")
    assert len(result) == 1
    assert result.iloc[0]["processed_room_name"] == "C"


def test_map_rooms_matched():
    df1 = pd.DataFrame(
        {
            "reference_name": ["My Hotel"],
            "reference_id": ["123"],
            "reference_room_id": ["10"],
            "reference_room_name": ["Deluxe room"],
            "processed_room_name": ["deluxe room"],
        }
    )

    df2 = pd.DataFrame(
        {
            "processed_room_name": ["deluxe room"],
            "supplier_name": ["SUPLIER A"],
            "supplier_room_id": ["0001"],
            "supplier_room_name": ["Deluxe Room"],
        }
    )

    matched, df1_unmatched, df2_unmatched = map_rooms(df1, df2)
    assert len(matched) == 1
    assert len(df1_unmatched) == 0
    assert len(df2_unmatched) == 0


def test_map_rooms_unmatched():
    df1 = pd.DataFrame(
        {
            "reference_name": ["My Hotel"],
            "reference_id": ["123"],
            "reference_room_id": ["10"],
            "reference_room_name": ["Superior room"],
            "processed_room_name": ["superior room"],
        }
    )

    df2 = pd.DataFrame(
        {
            "processed_room_name": ["deluxe room"],
            "supplier_name": ["SUPLIER A"],
            "supplier_room_id": ["0001"],
            "supplier_room_name": ["Deluxe Room"],
        }
    )

    matched, df1_unmatched, df2_unmatched = map_rooms(df1, df2)
    assert len(matched) == 0
    assert len(df1_unmatched) == 1
    assert len(df2_unmatched) == 1


def test_normalize_room_name():
    names = ["Deluxe Room!!!", " Suite  "]
    expected = ["deluxe room", "suite"]
    assert normalize_room_name(names) == expected


def test_reference_room_match():
    df1 = pd.DataFrame(
        {
            "hotel_id": ["13929222"],
            "lp_id": ["123"],
            "room_id": ["01"],
            "room_name": ["Deluxe room 001"],
            "processed_room_name": ["deluxe room"],
        }
    )
    df2 = pd.DataFrame(
        {
            "supplier_name": ["suplier1", "suplier1"],
            "supplier_room_id": ["1001", "1002"],
            "supplier_room_name": ["Deluxe Room", "Luxury Suite"],
            "processed_room_name": ["deluxe room", "luxury suite"],
            "supplier_room_id": ["S1", "S2"],
        }
    )
    matched, unmatched = reference_room_match("123", df1, df2)
    assert len(matched) == 1
    assert len(unmatched) == 1


def test_match_hotel_rooms():
    # Mocked data as Python objects (parsed from JSON)
    class Room:
        def __init__(self, roomId, roomName):
            self.roomId = roomId
            self.roomName = roomName

    class SupplierRoom:
        def __init__(self, supplierRoomId, supplierRoomName):
            self.supplierRoomId = supplierRoomId
            self.supplierRoomName = supplierRoomName

    class MockRoomData:
        class ReferenceCatalog:
            propertyId = "lp98f3b"
            propertyName = "Hola"
            referenceRoomInfo = [
                Room("1", "Classic Room - Olympic Queen Bed - ROOM ONLY"),
                Room("2", "Classic Room "),
                Room("3", "Superior Room "),
            ]

        class InputCatalog:
            supplierId = "supplier 1"
            supplierRoomInfo = [
                SupplierRoom("2", "Classic Room - Olympic Queen Bed - ROOM ONLY"),
                SupplierRoom("3", "Comfort House 6 bedroom Ocean View"),
                SupplierRoom("5", "SUPERIOR ROOM ADA - ROOM ONLY"),
                SupplierRoom("10", "Superior Room - Olympic Queen Bed - ROOM ONLY"),
                SupplierRoom("6", "Superior City View - Olympic Queen Bed - ROOM ONLY"),
                SupplierRoom("7", "Balcony Room - Olympic Queen Bed - ROOM ONLY"),
            ]

        referenceCatalog = ReferenceCatalog()
        inputCatalog = [InputCatalog()]

    rooms_data = MockRoomData()

    result = match_hotel_rooms(rooms_data)
    assert "mappedRooms" in result
    assert len(result["mappedRooms"]) > 0
    assert len(result["unmappedRooms"]) > 0


if __name__ == "__main__":
    pytest.main()
