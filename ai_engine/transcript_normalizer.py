import re
from typing import Dict, Any

class TranscriptNormalizer:
    """
    Bộ chuẩn hóa văn bản âm thanh thô (Raw Transcript) từ STT (Speech-to-Text).
    Giúp sửa lỗi nhận diện sai, chuẩn hóa định dạng số/ngày/tiền, và làm sạch câu
    để Intent Router phân loại chính xác.
    """
    
    # 1. Sửa lỗi hiển nhiên (Typo / Lỗi đồng âm STT)
    TYPO_CORRECTIONS = {
        r"\b(sapa|sa pa)\b": "Sa Pa",
        r"\b(nha trang)\b": "Nha Trang",
        r"\b(đà lạt)\b": "Đà Lạt",
        r"\b(phú quốc)\b": "Phú Quốc",
        r"\b(đà nẵng)\b": "Đà Nẵng",
        r"\b(hà nội)\b": "Hà Nội",
        r"\b(hồ chí minh|tp hcm|sài gòn)\b": "TP Hồ Chí Minh",
        r"\b(hội an)\b": "Hội An",
        
        # Sửa các lỗi STT thường gặp
        r"\b(trơi)\b": "chơi",
        r"\b(zị|vậy)\b": "vậy",
        r"\b(nhể|nhỉ)\b": "nhỉ",
    }
    
    # 2. Chuẩn hóa Tiền tệ (Entity Normalization)
    MONEY_CORRECTIONS = [
        # X triệu y trăm / ngàn -> X.Y00.000 VNĐ
        (r"(\d+)\s*triệu\s*rưỡi", lambda m: f"{m.group(1)}.500.000 VNĐ"),
        (r"(\d+)\s*triệu\s*mốt", lambda m: f"{m.group(1)}.100.000 VNĐ"),
        (r"(\d+)\s*triệu\s*(\d+)(?:\s*trăm)?(?:\s*nghìn|\s*ngàn)?", lambda m: f"{m.group(1)}.{m.group(2).ljust(3, '0')}.000 VNĐ"),
        (r"(\d+)\s*triệu", lambda m: f"{m.group(1)}.000.000 VNĐ"),
        
        # X trăm ngàn -> X00.000 VNĐ
        (r"(\d+)\s*trăm\s*(nghìn|ngàn)", lambda m: f"{m.group(1)}00.000 VNĐ"),
        (r"(\d+)\s*(nghìn|ngàn|k)\b", lambda m: f"{m.group(1)}.000 VNĐ"),
        
        # Thay từ bằng số nếu lẻ tẻ
        (r"\bmột\s*triệu\b", "1.000.000 VNĐ"),
        (r"\bhai\s*triệu\b", "2.000.000 VNĐ"),
        (r"\bba\s*triệu\b", "3.000.000 VNĐ"),
        (r"\bbốn\s*triệu\b", "4.000.000 VNĐ"),
        (r"\bnăm\s*triệu\b", "5.000.000 VNĐ"),
        (r"\bmười\s*triệu\b", "10.000.000 VNĐ"),
        
        # X trăm k
        (r"\bmột\s*trăm\s*(ngàn|nghìn|k)\b", "100.000 VNĐ"),
        (r"\bhai\s*trăm\s*(ngàn|nghìn|k)\b", "200.000 VNĐ"),
        (r"\bba\s*trăm\s*(ngàn|nghìn|k)\b", "300.000 VNĐ"),
        (r"\bnăm\s*trăm\s*(ngàn|nghìn|k)\b", "500.000 VNĐ"),
    ]
    
    # 3. Loại bỏ câu chưa hoàn chỉnh ở đuôi
    INCOMPLETE_TAILS = [
        r"\s+à\s+mà\s+thôi$",
        r"\s+ừm\s+thì$",
        r"\s+ờ\s+thì$",
        r"\s+hay\s+là$",
    ]

    @classmethod
    def normalize(cls, raw_text: str) -> Dict[str, Any]:
        """
        Thực hiện chuẩn hóa ngữ cảnh từ text thô STT.
        Trả về dict chứa raw_text và normalized_text.
        """
        if not raw_text or not raw_text.strip():
            return {"raw": raw_text, "normalized": raw_text}
            
        norm_text = raw_text.lower().strip()
        
        # 1. Loại bỏ các đuôi lấp lửng vô nghĩa
        for tail in cls.INCOMPLETE_TAILS:
            norm_text = re.sub(tail, "", norm_text)
            
        # 2. Sửa lỗi chính tả/vị trí đồng âm hiển nhiên
        for pattern, replacement in cls.TYPO_CORRECTIONS.items():
            norm_text = re.sub(pattern, replacement, norm_text)
            
        # 3. Chuẩn hóa Tiền tệ / Số học
        for pattern, replacement in cls.MONEY_CORRECTIONS:
            if callable(replacement):
                norm_text = re.sub(pattern, replacement, norm_text)
            else:
                norm_text = re.sub(pattern, replacement, norm_text)
                
        # Làm gọn khoảng trắng
        norm_text = re.sub(r"\s+", " ", norm_text).strip()
        
        # Trả về câu đã viết hoa chữ cái đầu
        if norm_text:
            norm_text = norm_text[0].upper() + norm_text[1:]
            
        return {
            "raw": raw_text,
            "normalized": norm_text
        }
