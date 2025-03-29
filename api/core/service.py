# Load SpaCy NLP model
from rapidfuzz import process, fuzz
import re
from api.schemas.schema import RoomData
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required resources
nltk.download("stopwords")
nltk.download("wordnet")

# Initialize stopwords and lemmatizer
stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


def get_matched_rooms(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    output_columns: list[str] = [],
    room_col: str = "processed_room_name",
    similarity_threshold: int = 80,
):
    """
    Merge room data for a given hotel id from two DataFrames using fuzzy matching.
    Ensures unique room descriptions before merging and retains match scores.
    """
    # Copy data to avoid modifying original DataFrames
    subset1 = df1.copy()
    subset2 = df2.copy()

    # Deduplicate room names before matching
    unique_rooms1 = subset1[[room_col]].drop_duplicates()
    unique_rooms2 = subset2[[room_col]].drop_duplicates()

    # Create a mapping from df2 to df1 using fuzzy matching
    matched_rooms = {}
    match_scores = {}
    for room2 in unique_rooms2[room_col]:
        match, score, _ = process.extractOne(
            room2, unique_rooms1[room_col].tolist(), scorer=fuzz.token_sort_ratio
        )
        if score >= similarity_threshold:
            matched_rooms[room2] = match
            match_scores[room2] = score

    # Apply fuzzy match mapping and filter based on threshold
    subset2["matched_room"] = subset2[room_col].map(matched_rooms)
    subset2["match_score"] = subset2[room_col].map(match_scores)
    subset2 = subset2.dropna(
        subset=["matched_room"]
    )  # Remove rows that did not meet threshold

    # Merge matched rooms with subset1 and keep the score column
    final_merged = subset1.merge(
        subset2[[room_col, "matched_room", "match_score"] + output_columns],
        left_on=room_col,
        right_on="matched_room",
        how="inner",  # Only keep matches
        suffixes=("_df1", "_df2"),
    )

    return final_merged


def get_unmatched_rooms(df: pd.DataFrame, df_matched: pd.DataFrame, room_col: str):
    return df[~df[room_col].isin(df_matched[room_col])].copy()


def map_rooms(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    room_col: str = "processed_room_name",
    similarity_threshold: int = 80,
):
    df_matched = get_matched_rooms(
        df1,
        df2,
        ["supplier_name", "supplier_room_id", "supplier_room_name"],
        room_col,
        similarity_threshold,
    )
    df1_unmatched = get_unmatched_rooms(df1, df_matched, "reference_room_id")
    df2_unmatched = get_unmatched_rooms(df2, df_matched, "supplier_room_id")

    return df_matched, df1_unmatched, df2_unmatched


def reference_room_match(
    lp_id: str,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    room_col: str = "processed_room_name",
    similarity_threshold: int = 80,
):
    """
    Merge room data for a given hotel id (lp_id) from two DataFrames using fuzzy matching.
    Prevents duplication by ensuring unique room descriptions before merging.
    """
    # Filter for the given hotel
    subset1 = df1[df1["lp_id"] == lp_id].copy()

    df_matched = get_matched_rooms(
        subset1,
        df2,
        ["supplier_room_id", "supplier_room_name"],
        room_col,
        similarity_threshold,
    )
    df_unmatched = get_unmatched_rooms(df2, df_matched, "supplier_room_id")

    return df_matched, df_unmatched


def match_hotel_rooms(rooms_data: RoomData):
    print(rooms_data)
    id_reference = rooms_data.referenceCatalog.propertyId

    reference_rooms = []
    for room in rooms_data.referenceCatalog.referenceRoomInfo:
        reference_rooms.append(
            {
                "reference_name": rooms_data.referenceCatalog.propertyName,
                "reference_id": rooms_data.referenceCatalog.propertyId,
                "reference_room_id": room.roomId,
                "reference_room_name": room.roomName,
            }
        )
    # Create DataFrame from the flattened supplier room info
    df_reference = pd.DataFrame(reference_rooms)

    # Extract supplier room info from inputCatalog
    supplier_rooms = []
    for input_catalog in rooms_data.inputCatalog:
        for room in input_catalog.supplierRoomInfo:
            supplier_rooms.append(
                {
                    "supplier_name": input_catalog.supplierId,
                    "supplier_room_id": room.supplierRoomId,
                    "supplier_room_name": room.supplierRoomName,
                }
            )

    # Create DataFrame from the flattened supplier room info
    df_input = pd.DataFrame(supplier_rooms)

    # Normalize room names
    df_reference["processed_room_name"] = normalize_room_name(
        df_reference["reference_room_name"]
    )
    df_input["processed_room_name"] = normalize_room_name(
        df_input["supplier_room_name"]
    )
    df_matched, df_reference_unmatched, df_input_unmatched = map_rooms(
        df_reference, df_input
    )

    # Group by reference_room_id to handle multiple reference rooms
    grouped = df_matched.groupby("reference_room_id")

    mapped_rooms_splitted = []

    for reference_room_id, group in grouped:
        mapped_rooms = group[
            ["supplier_name", "supplier_room_id", "supplier_room_name", "match_score"]
        ].to_dict(orient="records")
        reference_details = {
            "referenceName": group.iloc[0]["reference_name"],
            "referenceId": group.iloc[0]["reference_id"],
            "referenceRoomId": group.iloc[0]["reference_room_id"],
            "referenceRoomName": group.iloc[0]["reference_room_name"],
            "mappedRooms": mapped_rooms,
        }
        mapped_rooms_splitted.append(reference_details)

    return {
        "referenceCatalog": id_reference,
        "mappedRooms": mapped_rooms_splitted,
        "unmappedReferenceRooms": df_reference_unmatched.to_dict(orient="records"),
        "unmappedRooms": df_input_unmatched.to_dict(orient="records"),
    }


def normalize_room_name(room_names: list[str]):
    def preprocess_text(text):
        """Efficiently preprocess text: lowercase, remove numbers/punctuation/stopwords, and lemmatize."""
        if isinstance(text, list):  # If input is a list, process each item
            return [preprocess_text(t) for t in text]

        # Convert to lowercase
        text = text.lower()

        # Remove numbers
        text = re.sub(r"\d+", "", text)

        # Remove punctuation (excluding words and spaces)
        text = re.sub(r"[^\w\s]", "", text)

        # Remove extra whitespaces
        text = text.strip()

        # Tokenize (split into words)
        words = text.split()

        # Remove stopwords and apply lemmatization
        words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]

        # Rejoin words into a single string
        return " ".join(words)

    processed_room_name_list = []
    for room in room_names:
        processed_room = preprocess_text(room)
        processed_room_name_list.append(processed_room)

    return processed_room_name_list
