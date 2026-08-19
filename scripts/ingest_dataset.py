"""
beenavi/scripts/ingest_dataset.py
Đọc 17.148 file markdown từ md_dataset.zip, trích xuất thông tin có cấu trúc
và nạp vào ChromaDB Persistent Vector Database (data/chroma_db).
Đồng thời tạo data/locations_index.json để phục vụ tìm kiếm nhanh.
"""
import os
import sys
import zipfile
import re
import json
import time
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thư mục gốc dự án beenavi
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = REPO_ROOT / "data"
MD_DATASET_DIR = DATA_DIR / "md_dataset"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
LOCATIONS_INDEX_PATH = DATA_DIR / "locations_index.json"
ZIP_PATH = REPO_ROOT.parent / "md_dataset.zip"


def extract_zip_if_needed():
    """Giải nén md_dataset.zip nếu chưa giải nén"""
    if MD_DATASET_DIR.exists() and len(list(MD_DATASET_DIR.glob("*.md"))) > 1000:
        print(f"[Dataset] Đã tồn tại thư mục md_dataset tại: {MD_DATASET_DIR}")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ZIP_PATH.exists():
        # Kiểm tra thêm trong REPO_ROOT
        alt_zip = REPO_ROOT / "md_dataset.zip"
        if alt_zip.exists():
            zip_file_to_use = alt_zip
        else:
            raise FileNotFoundError(f"Không tìm thấy file md_dataset.zip tại {ZIP_PATH} hoặc {alt_zip}")
    else:
        zip_file_to_use = ZIP_PATH

    print(f"[Dataset] Đang giải nén {zip_file_to_use} -> {DATA_DIR}...")
    start_t = time.time()
    with zipfile.ZipFile(zip_file_to_use, "r") as z:
        z.extractall(DATA_DIR)
    print(f"[Dataset] Giải nén hoàn tất sau {time.time() - start_t:.1f}s!")


def parse_markdown_file(file_path: Path) -> dict | None:
    """Parse 1 file .md thành dictionary cấu trúc"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # Tên địa điểm từ thẻ H1 đầu tiên
    name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else file_path.stem

    def get_field(field_name: str) -> str:
        m = re.search(rf"-\s+\*\*{field_name}:\*\*\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            return "" if val.lower() in ["none", "null", ""] else val
        return ""

    category = get_field("Danh mục") or "Khám phá"
    sub_category = get_field("Danh mục con") or ""
    lat_str = get_field("Latitude")
    lon_str = get_field("Longitude")
    address = get_field("Địa chỉ") or ""
    cuisine = get_field("Ẩm thực") or ""
    description = get_field("Mô tả") or ""
    open_hours = get_field("Giờ mở cửa") or ""
    wheelchair = get_field("Hỗ trợ xe lăn") or ""

    try:
        lat = float(lat_str) if lat_str else 0.0
        lon = float(lon_str) if lon_str else 0.0
    except ValueError:
        lat, lon = 0.0, 0.0

    # Tạo document text phục vụ Vector Embedding
    doc_parts = [f"Địa điểm: {name}"]
    if category:
        doc_parts.append(f"Danh mục: {category}" + (f" ({sub_category})" if sub_category else ""))
    if address:
        doc_parts.append(f"Địa chỉ: {address}")
    if cuisine:
        doc_parts.append(f"Đặc sản ẩm thực: {cuisine}")
    if description:
        doc_parts.append(f"Mô tả: {description}")
    if open_hours:
        doc_parts.append(f"Giờ mở cửa: {open_hours}")

    doc_text = " | ".join(doc_parts)

    return {
        "id": f"poi_{file_path.stem}",
        "name": name,
        "category": category,
        "sub_category": sub_category,
        "lat": lat,
        "lon": lon,
        "address": address,
        "cuisine": cuisine,
        "description": description,
        "open_hours": open_hours,
        "wheelchair": wheelchair,
        "doc_text": doc_text,
    }


def ingest_to_chromadb():
    """Đọc toàn bộ file .md và nạp vào ChromaDB + locations_index.json"""
    extract_zip_if_needed()

    md_files = sorted(list(MD_DATASET_DIR.glob("*.md")))
    total_files = len(md_files)
    print(f"[Ingest] Tìm thấy tổng cộng {total_files} file markdown.")

    import chromadb
    from chromadb.config import Settings

    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    # Tạo hoặc nạp collection
    collection = client.get_or_create_collection(
        name="vietnam_pois",
        metadata={"hnsw:space": "cosine"}
    )

    print(f"[Ingest] Đang parse và embedding vào ChromaDB...")
    start_time = time.time()

    all_pois_for_index = []
    batch_ids = []
    batch_docs = []
    batch_metadatas = []
    BATCH_SIZE = 500
    inserted_count = 0

    for i, md_file in enumerate(md_files, 1):
        poi = parse_markdown_file(md_file)
        if not poi or not poi["name"]:
            continue

        # Lưu danh sách nhẹ phục vụ locations_index.json
        all_pois_for_index.append({
            "name": poi["name"],
            "lat": poi["lat"],
            "lon": poi["lon"],
            "category": poi["category"],
            "info": f"{poi['name']}; {poi['category']}; {poi['address'] or poi['description']}"
        })

        batch_ids.append(poi["id"])
        batch_docs.append(poi["doc_text"])
        batch_metadatas.append({
            "name": poi["name"],
            "category": poi["category"],
            "sub_category": poi["sub_category"],
            "lat": poi["lat"],
            "lon": poi["lon"],
            "address": poi["address"],
            "cuisine": poi["cuisine"],
        })

        if len(batch_ids) >= BATCH_SIZE:
            collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metadatas
            )
            inserted_count += len(batch_ids)
            print(f"  -> Đã nạp {inserted_count}/{total_files} POIs ({(inserted_count/total_files)*100:.1f}%)...")
            batch_ids, batch_docs, batch_metadatas = [], [], []

    # Nạp batch cuối cùng
    if batch_ids:
        collection.upsert(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metadatas
        )
        inserted_count += len(batch_ids)

    # Lưu locations_index.json
    with open(LOCATIONS_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(all_pois_for_index, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print(f"\n✅ [Thành công] Đã nạp {inserted_count} địa điểm vào ChromaDB trong {elapsed:.1f} giây!")
    print(f"   - ChromaDB Path: {CHROMA_DB_DIR}")
    print(f"   - Cache Index  : {LOCATIONS_INDEX_PATH}")


if __name__ == "__main__":
    ingest_to_chromadb()
