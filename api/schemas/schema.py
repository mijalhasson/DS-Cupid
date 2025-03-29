from pydantic import BaseModel
from typing import List, Optional

class SupplierRoomInfo(BaseModel):
    supplierRoomId: str
    supplierRoomName: str

class ReferenceRoomInfo(BaseModel):
    roomId: str
    roomName: str

class SupplierCatalog(BaseModel):
    supplierId: str
    supplierRoomInfo: List[SupplierRoomInfo]

class ReferenceCatalog(BaseModel):
    propertyId: str
    propertyName: Optional[str] = None
    referenceRoomInfo: Optional[List[ReferenceRoomInfo]] = None

class RoomData(BaseModel):
    referenceCatalog: ReferenceCatalog
    inputCatalog: List[SupplierCatalog] 

class BulkRoomMatchRequest(BaseModel):
    bulk_matches: List[RoomData]
