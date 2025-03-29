from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import pandas as pd
from api.schemas.schema import RoomData, BulkRoomMatchRequest
from api.core.service import reference_room_match, normalize_room_name, match_hotel_rooms

df_reference = pd.read_csv("data/processed/reference_rooms.csv")

app = FastAPI()

@app.post("/ref_room_match")
async def ref_room_match(request_body: RoomData):
    try:
        id_reference = request_body.referenceCatalog.propertyId

        if id_reference not in list(df_reference['lp_id']):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid Request",
                    "message": "The propertyID provided is not in the reference system."
                }
            )

        # Extract supplier room info from inputCatalog
        supplier_rooms = []
        for input_catalog in request_body.inputCatalog:
            for room in input_catalog.supplierRoomInfo:
                supplier_rooms.append({
                    "supplier_name": input_catalog.supplierId,
                    "supplier_room_id": room.supplierRoomId,
                    "supplier_room_name": room.supplierRoomName
                })

        # Create DataFrame from the flattened supplier room info
        df_input = pd.DataFrame(supplier_rooms)

        # Normalize room names
        df_input['processed_room_name'] = normalize_room_name(df_input["supplier_room_name"])

        df_matched, df_unmatched = reference_room_match(id_reference, df_reference, df_input)

        # Group by reference_room_id to handle multiple reference rooms
        grouped = df_matched.groupby("room_id")

        mapped_rooms_splitted = []

        for supplier_room_id, group in grouped:
            mapped_rooms = group[["supplier_room_id", "supplier_room_name", "match_score"]].to_dict(orient='records')
            reference_details = {
                "hotel_id": group.iloc[0]["hotel_id"].item(),
                "lp_id": group.iloc[0]["lp_id"],
                "reference_room_id": group.iloc[0]["room_id"].item(),
                "reference_room_name": group.iloc[0]["room_name"],
                "mappedRooms": mapped_rooms
            }
            mapped_rooms_splitted.append(reference_details)

        # Return DataFrames or processed data
        return {
            "referenceCatalog": id_reference,
            "mappedRooms": mapped_rooms_splitted,
            "unmappedRooms": df_unmatched.to_dict(orient='records'),
        }

    except Exception as e:
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Server Error",
                    "message": e
                }
            )

# Room Match
@app.post("/room_match")
async def room_match(request_body: RoomData):
    try:
        return match_hotel_rooms(request_body)
    
    except Exception as e:
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Server Error",
                    "message": e
                }
            )

# Bulk Room Match
@app.post("/bulk_room_match")
async def bulk_room_match(request_body: BulkRoomMatchRequest):
    try:
        room_mapping = []
        for rooms_data in request_body.bulk_matches:
            room_map =  match_hotel_rooms(rooms_data)
            room_mapping.append(room_map)
        return room_mapping
    
    except Exception as e:
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Server Error",
                    "message": e
                }
            )


# uvicorn myapp:app --reload
