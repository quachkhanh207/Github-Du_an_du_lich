import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import diary_service


print("======================================================")
print("     KIỂM TRA HỆ THỐNG UNIFIED FASTAPI + SQLITE")
print("======================================================")

# 1. Kiểm tra thống kê
stats = diary_service.get_user_statistics()
print(f"\n1. Thống kê chung:")
print(f"   - Tổng chuyến đi : {stats['total_trips']}")
print(f"   - Tổng ảnh kỷ niệm: {stats['total_photos']}")
print(f"   - Điểm đến duy nhất: {stats['unique_destinations']}")

# 2. Kiểm tra danh sách chuyến đi
trips = diary_service.get_user_trips()
print(f"\n2. Danh sách chuyến đi trong CSDL ({len(trips)} chuyến):")
for t in trips:
    print(f"   📍 [{t['id'][:8]}] {t['title']} ({t['number_of_days']} ngày) - Phương tiện: {t['vehicle']}")

# 3. Kiểm tra tin nhắn chat
history = diary_service.get_chat_history()
print(f"\n3. Lịch sử hội thoại Chatbot ({len(history)} tin nhắn):")
for m in history[:4]:
    print(f"   💬 [{m['role']}]: {m['content'][:60]}...")

print("\n✅ Kiểm tra hệ thống hoàn tất.")
