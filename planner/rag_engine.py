import os
import re
import json
import sqlite3
import math
import random
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "travel_knowledge.db"

def remove_vn_accents(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize('NFD', str(s))
    s = re.sub(r'[\u0300-\u036f]', '', s)
    s = s.replace('đ', 'd').replace('Đ', 'D')
    return s.lower().replace('_', ' ').strip()

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    except:
        return 999.0

# =========================================================================
# CSDL CÁC CỤM ĐỊA LÝ DU LỊCH ĐA PHONG CÁCH
# =========================================================================

CITY_GEO_CLUSTERS = {
    "hà nội": [
        {
            "cluster_id": "hn_tayho",
            "cluster_name": "Cụm Tây Hồ & Trúc Bạch Thơ Mộng",
            "cluster_type": "chill_lake_food",
            "center": [21.048, 105.836],
            "morning_anchors": [
                {"id": "hn_tran_quoc", "name": "Chùa Trấn Quốc (Hồ Tây)", "category": "spiritual_culture", "lat": 21.0478, "lon": 105.8365, "style": "chill", "description": "Ngôi chùa cổ nhất Thăng Long hơn 1500 năm tuổi tọa lạc trên hòn đảo xanh giữa Hồ Tây."},
                {"id": "hn_quan_thanh", "name": "Đền Quán Thánh", "category": "spiritual_culture", "lat": 21.0435, "lon": 105.8378, "style": "heritage", "description": "Một trong Thăng Long Tứ Trấn uy nghiêm với pho tượng Huyền Thiên Trấn Vũ bằng đồng đen 4 tấn."}
            ],
            "afternoon_anchors": [
                {"id": "hn_phu_tay_ho", "name": "Phủ Tây Hồ", "category": "spiritual_culture", "lat": 21.0668, "lon": 105.8285, "style": "heritage", "description": "Nơi thờ Thánh Mẫu Liễu Hạnh linh thiêng trên bán đảo nhô ra lòng Hồ Tây lộng gió."},
                {"id": "hn_ho_tay_sunset", "name": "Đường Thanh Niên & Bến Thuyền Hồ Tây", "category": "tourism_heritage", "lat": 21.0450, "lon": 105.8380, "style": "photo_chill", "description": "Cung đường lãng mạn ngăn đôi Hồ Tây và Hồ Trúc Bạch, điểm ngắm hoàng hôn đẹp nhất Hà Nội."}
            ],
            "food_satellites_street": [
                {"id": "hn_banh_tom_ho_tay", "name": "Bánh Tôm Hồ Tây (Thanh Niên)", "category": "dining_coffee", "lat": 21.0465, "lon": 105.8372, "description": "Đặc sản bánh tôm vàng ruộm giòn tan ăn kèm nước chấm chua ngọt trứ danh."},
                {"id": "hn_pho_cuon_huong_mai", "name": "Phở Cuốn Hương Mai (Ngũ Xã)", "category": "dining_coffee", "lat": 21.0440, "lon": 105.8395, "description": "Làng ẩm thực Ngũ Xã với món phở cuốn thịt bò rau thơm và phở chiên phồng béo ngậy."}
            ],
            "food_satellites_luxury": [
                {"id": "hn_sen_tay_ho", "name": "Buffet Quốc Tế Sen Tây Hồ", "category": "dining_coffee", "lat": 21.0710, "lon": 105.8210, "description": "Thiên đường ẩm thực Á - Âu cao cấp ven hồ Tây với hơn 150 món ăn thượng hạng."},
                {"id": "hn_dong_son_drum", "name": "Nhà Hàng Trống Đồng Tây Hồ", "category": "dining_coffee", "lat": 21.0520, "lon": 105.8350, "description": "Không gian ẩm thực cung đình sang trọng view trọn mặt hồ."}
            ],
            "cafe_satellites": [
                {"id": "hn_santorini_ho_tay", "name": "Santorini Lounge Cafe Hồ Tây", "category": "dining_coffee", "lat": 21.0550, "lon": 105.8320, "style": "photo", "description": "Quán cafe view trọn lòng hồ Tây lộng gió, điểm săn hoàng hôn cực phẩm."},
                {"id": "hn_cong_truc_bach", "name": "Cộng Cà Phê Trúc Bạch", "category": "dining_coffee", "lat": 21.0445, "lon": 105.8410, "style": "chill", "description": "Nhâm nhi ly cafe cốt dừa ngắm mặt hồ Trúc Bạch êm đềm."}
            ],
            "night_satellites": [
                {"id": "hn_pho_am_thuc_ngu_xa", "name": "Khu Ẩm Thực Đêm Ngũ Xã - Trúc Bạch", "category": "leisure_shopping", "lat": 21.0438, "lon": 105.8398, "description": "Phố đi bộ ẩm thực thưởng thức lẩu ếch, phở cuốn và chè sen long nhãn."}
            ]
        },
        {
            "cluster_id": "hn_hoankiem",
            "cluster_name": "Cụm Hoàn Kiếm & Trái Tim Phố Cổ",
            "cluster_type": "food_photo_heritage",
            "center": [21.030, 105.852],
            "morning_anchors": [
                {"id": "hn_ho_guom", "name": "Hồ Gươm (Hồ Hoàn Kiếm) & Đền Ngọc Sơn", "category": "tourism_heritage", "lat": 21.0308, "lon": 105.8524, "style": "heritage_photo", "description": "Trái tim của Thủ đô, check-in Cầu Thê Húc đỏ son, Tháp Rùa và Đền Ngọc Sơn linh thiêng."},
                {"id": "hn_nha_tho_lon", "name": "Nhà thờ Lớn Hà Nội", "category": "tourism_heritage", "lat": 21.0288, "lon": 105.8495, "style": "photo", "description": "Kiến trúc Gothic Pháp tráng lệ cổ kính giữa lòng phố cổ, điểm check-in không thể bỏ lỡ."}
            ],
            "afternoon_anchors": [
                {"id": "hn_hoa_lo", "name": "Di tích Nhà tù Hỏa Lò", "category": "tourism_heritage", "lat": 21.0253, "lon": 105.8465, "style": "heritage", "description": "Địa danh lịch sử xúc động ghi dấu tinh thần kiên cường của các chiến sĩ cách mạng."},
                {"id": "hn_nha_hat_lon", "name": "Nhà hát Lớn Hà Nội (Hanoi Opera House)", "category": "tourism_heritage", "lat": 21.0245, "lon": 105.8576, "style": "photo_luxury", "description": "Kiến trúc Tân cổ điển Pháp lộng lẫy và Quảng trường Cách mạng Tháng Tám."}
            ],
            "food_satellites_street": [
                {"id": "hn_bun_dau_hang_khay", "name": "Bún Đậu Mắm Tôm Hàng Khay", "category": "dining_coffee", "lat": 21.0298, "lon": 105.8512, "description": "Mẹt bún đậu giòn rụm, chả cốm thơm dẻo trong ngõ nhỏ đặc trưng phố cổ."},
                {"id": "hn_nom_bo_kho", "name": "Nộm Bò Khô Long Vi Dung (Hồ Gươm)", "category": "dining_coffee", "lat": 21.0322, "lon": 105.8535, "description": "Quán nộm bò khô trứ danh phố Đinh Tiên Hoàng view nhìn thẳng ra Hồ Gươm."},
                {"id": "hn_pho_thin", "name": "Phở Thìn Lò Đúc", "category": "dining_coffee", "lat": 21.0180, "lon": 105.8570, "description": "Bát phở bò tái lăn ngập hành hoa xào đậm đà lửa lớn trứ danh Hà Thành."}
            ],
            "food_satellites_luxury": [
                {"id": "hn_luc_thuy_lounge", "name": "Nhà Hàng Lục Thủy (Bên Hồ Gươm)", "category": "dining_coffee", "lat": 21.0290, "lon": 105.8530, "description": "Nhà hàng ẩm thực Việt tinh tế với tầm nhìn Panorama trực diện Tháp Rùa Hồ Gươm."},
                {"id": "hn_club_opera", "name": "Club De L'Opera Restaurant", "category": "dining_coffee", "lat": 21.0250, "lon": 105.8560, "description": "Không gian Pháp cổ điển sang trọng bên Nhà hát Lớn."}
            ],
            "cafe_satellites": [
                {"id": "hn_cafe_lam", "name": "Cà Phê Lâm (Nguyễn Hữu Huân)", "category": "dining_coffee", "lat": 21.0352, "lon": 105.8548, "style": "chill", "description": "Quán cafe tranh lâu đời đậm chất nghệ sĩ Hà Nội xưa."},
                {"id": "hn_trang_tien", "name": "Kem Tràng Tiền Truyền Thống", "category": "dining_coffee", "lat": 21.0258, "lon": 105.8550, "style": "photo_food", "description": "Thưởng thức que kem cốm, ốc quế dừa Tràng Tiền ngọt mát bên Hồ Gươm."}
            ],
            "night_satellites": [
                {"id": "hn_ta_hien", "name": "Phố Bia Tạ Hiện & Lương Ngọc Quyến", "category": "leisure_shopping", "lat": 21.0348, "lon": 105.8519, "description": "Ngã tư quốc tế sầm uất với bia hơi, nem chua rán và không khí đêm sôi động."}
            ]
        },
        {
            "cluster_id": "hn_badinh",
            "cluster_name": "Cụm Ba Đình & Di Sản Hoàng Thành",
            "cluster_type": "heritage_culture",
            "center": [21.036, 105.834],
            "morning_anchors": [
                {"id": "hn_lang_bac", "name": "Lăng Bác (Lăng Chủ tịch Hồ Chí Minh)", "category": "tourism_heritage", "lat": 21.0368, "lon": 105.8344, "style": "heritage", "description": "Quảng trường Ba Đình lịch sử, viếng Lăng Bác, tham quan Nhà sàn và Chùa Một Cột."},
                {"id": "hn_hoang_thanh", "name": "Hoàng Thành Thăng Long", "category": "tourism_heritage", "lat": 21.0350, "lon": 105.8402, "style": "heritage", "description": "Di sản văn hóa thế giới với Điện Kính Thiên, Đoan Môn và di chỉ khảo cổ 1300 năm tuổi."}
            ],
            "afternoon_anchors": [
                {"id": "hn_van_mieu", "name": "Văn Miếu - Quốc Tử Giám", "category": "tourism_heritage", "lat": 21.0293, "lon": 105.8355, "style": "heritage", "description": "Trường đại học đầu tiên của Việt Nam với 82 bia Tiến sĩ và kiến trúc Khuê Văn Các cổ kính."},
                {"id": "hn_cot_co", "name": "Cột Cờ Hà Nội & Bảo tàng Lịch sử Quân sự", "category": "tourism_heritage", "lat": 21.0325, "lon": 105.8398, "style": "heritage", "description": "Kỳ đài lịch sử biểu tượng của Thủ đô ngàn năm văn hiến."}
            ],
            "food_satellites_street": [
                {"id": "hn_pho_bat_dan", "name": "Phở Gia Truyền Bát Đàn", "category": "dining_coffee", "lat": 21.0345, "lon": 105.8482, "description": "Bát phở bò nước dùng trong vắt, ngọt thanh gia truyền nức tiếng phố cổ."},
                {"id": "hn_bun_cha_obama", "name": "Bún Chả Hương Liên (Obama)", "category": "dining_coffee", "lat": 21.0189, "lon": 105.8540, "description": "Quán bún chả gia truyền nổi tiếng từng đón cựu Tổng thống Mỹ Barack Obama."}
            ],
            "food_satellites_luxury": [
                {"id": "hn_cha_ca_la_vong", "name": "Chả Cá Lã Vọng Gia Truyền", "category": "dining_coffee", "lat": 21.0358, "lon": 105.8489, "description": "Đặc sản chả cá lăng nướng than hoa ăn kèm bún, lạc rang, thì là và mắm tôm thượng hạng."},
                {"id": "hn_tam_vi", "name": "Nhà Hàng Tầm Vị (Michelin 1 Sao)", "category": "dining_coffee", "lat": 21.0280, "lon": 105.8370, "description": "Mâm cơm gia đình Bắc Bộ chuẩn vị truyền thống đạt giải thưởng Michelin danh giá."}
            ],
            "cafe_satellites": [
                {"id": "hn_cafe_giang", "name": "Cà Phê Giảng (Cà phê Trứng)", "category": "dining_coffee", "lat": 21.0349, "lon": 105.8533, "style": "photo_food", "description": "Cái nôi của món cà phê trứng béo ngậy huyền thoại Hà Nội từ năm 1946."},
                {"id": "hn_cafe_dinh", "name": "Cà Phê Đinh", "category": "dining_coffee", "lat": 21.0315, "lon": 105.8530, "style": "chill", "description": "Quán cafe ban công cổ kính ngắm trọn vẹn nhịp sống phố cổ Hà Nội."}
            ],
            "night_satellites": [
                {"id": "hn_pho_di_bo", "name": "Phố Đi Bộ & Chợ Đêm Phố Cổ", "category": "leisure_shopping", "lat": 21.0335, "lon": 105.8525, "description": "Thưởng thức ẩm thực đường phố, kem Tràng Tiền và âm nhạc đường phố cuối tuần."}
            ]
        },
        {
            "cluster_id": "hn_caugiay",
            "cluster_name": "Cụm Cầu Giấy & Văn Hóa Đương Đại",
            "cluster_type": "modern_lifestyle",
            "center": [21.037, 105.795],
            "morning_anchors": [
                {"id": "hn_dan_toc_hoc", "name": "Bảo tàng Dân tộc học Việt Nam", "category": "tourism_heritage", "lat": 21.0405, "lon": 105.7985, "style": "heritage_family", "description": "Khám phá bản sắc 54 dân tộc anh em với khu nhà rông, nhà sàn và vườn kiến trúc dân gian rộng lớn."},
                {"id": "hn_bao_tang_hn", "name": "Bảo tàng Hà Nội (Phạm Hùng)", "category": "tourism_heritage", "lat": 21.0100, "lon": 105.7863, "style": "photo_modern", "description": "Kiến trúc kim tự tháp ngược độc đáo bậc nhất Thủ đô, không gian trưng bày hiện đại."}
            ],
            "afternoon_anchors": [
                {"id": "hn_cong_vien_cau_giay", "name": "Công viên Cầu Giấy & Keangnam Sky72", "category": "tourism_heritage", "lat": 21.0270, "lon": 105.7900, "style": "photo_chill", "description": "Ngắm toàn cảnh thành phố Hà Nội hiện đại từ đài quan sát trên cao."}
            ],
            "food_satellites_street": [
                {"id": "hn_com_nieu_kombo", "name": "Cơm Niêu Singapore Kombo (Cầu Giấy)", "category": "dining_coffee", "lat": 21.0360, "lon": 105.7940, "description": "Cơm niêu cháy giòn rụm sốt tiêu đen bò nướng thơm lừng."},
                {"id": "hn_vit_29", "name": "Vịt Quay 29 Cầu Giấy", "category": "dining_coffee", "lat": 21.0340, "lon": 105.7970, "description": "Đặc sản lẩu vịt om sấu và vịt quay giòn da đậm đà gia vị."}
            ],
            "food_satellites_luxury": [
                {"id": "hn_lau_nam_ashima", "name": "Lẩu Nấm Ashima (Hoàng Đạo Thúy)", "category": "dining_coffee", "lat": 21.0080, "lon": 105.8030, "description": "Thưởng thức lẩu nấm thiên nhiên thanh đạm bổ dưỡng trong không gian sang trọng."},
                {"id": "hn_jw_marriott_dining", "name": "JW Café - JW Marriott Hotel", "category": "dining_coffee", "lat": 21.0120, "lon": 105.7830, "description": "Tiệc buffet hải sản và ẩm thực quốc tế 5 sao đẳng cấp thế giới."}
            ],
            "cafe_satellites": [
                {"id": "hn_the_coffee_house_cg", "name": "The Coffee House Cầu Giấy", "category": "dining_coffee", "lat": 21.0350, "lon": 105.7930, "style": "modern", "description": "Không gian cafe hiện đại, thoáng mát phục vụ trà đào cam sả và cà phê sữa đá."}
            ],
            "night_satellites": [
                {"id": "hn_the_garden_mall", "name": "Trung tâm thương mại The Garden & Phố ẩm thực Mễ Trì", "category": "leisure_shopping", "lat": 21.0150, "lon": 105.7780, "description": "Khu phố ẩm thực Hàn Quốc và mua sắm hiện đại bậc nhất khu Tây Hà Nội."}
            ]
        }
    ],
    "đà nẵng": [
        {
            "cluster_id": "dn_sontra_mykhe",
            "cluster_name": "Cụm Bán Đảo Sơn Trà & Bãi Biển Mỹ Khê",
            "cluster_type": "beach_chill",
            "center": [16.080, 108.260],
            "morning_anchors": [
                {"id": "dn_son_tra", "name": "Bán đảo Sơn Trà & Chùa Linh Ứng", "category": "spiritual_culture", "lat": 16.104, "lon": 108.277, "style": "spiritual_photo", "description": "Chiêm bái tượng Phật Bà Quan Âm cao 67m hướng ra biển Đông và ngắm toàn cảnh vịnh Đà Nẵng."},
                {"id": "dn_dinh_ban_co", "name": "Đỉnh Bàn Cờ & Cây Đa Ngàn Năm", "category": "tourism_heritage", "lat": 16.120, "lon": 108.285, "style": "adventure", "description": "Nóc nhà bán đảo Sơn Trà săn mây và ngắm đàn voọc chà vá chân nâu quý hiếm."}
            ],
            "afternoon_anchors": [
                {"id": "dn_my_khe", "name": "Bãi biển Mỹ Khê & Công viên Biển Đông", "category": "tourism_heritage", "lat": 16.060, "lon": 108.246, "style": "beach_chill", "description": "Một trong những bãi biển quyến rũ nhất hành tinh với cát trắng mịn và làn nước trong xanh."}
            ],
            "food_satellites_street": [
                {"id": "dn_nam_danh", "name": "Hải sản Năm Đảnh (Sơn Trà)", "category": "dining_coffee", "lat": 16.095, "lon": 108.255, "description": "Quán hải sản ngon - bổ - rẻ trứ danh trong ngõ nhỏ Sơn Trà."},
                {"id": "dn_banh_xeo", "name": "Bánh Xèo Tôm Nhảy Cô Ba", "category": "dining_coffee", "lat": 16.065, "lon": 108.215, "description": "Bánh xèo giòn rụm với tôm đất tươi nhảy tanh tách ăn kèm rau rừng."}
            ],
            "food_satellites_luxury": [
                {"id": "dn_be_man", "name": "Hải sản Bé Mặn (Võ Nguyên Giáp)", "category": "dining_coffee", "lat": 16.067, "lon": 108.246, "description": "Quán hải sản tươi sống cao cấp đông đúc bậc nhất ven biển Võ Nguyên Giáp."},
                {"id": "dn_la_maison_1888", "name": "La Maison 1888 (InterContinental Đà Nẵng)", "category": "dining_coffee", "lat": 16.1210, "lon": 108.3100, "description": "Nhà hàng Pháp 3 sao Michelin đẳng cấp số 1 miền Trung."}
            ],
            "cafe_satellites": [
                {"id": "dn_marina", "name": "Sơn Trà Marina Cafe", "category": "dining_coffee", "lat": 16.112, "lon": 108.282, "style": "photo_sunset", "description": "Quán cafe phong cách Santorini bên bờ biển Sơn Trà, điểm ngắm hoàng hôn đỉnh cao."},
                {"id": "dn_wonderlust", "name": "Wonderlust Cafe & Bakery", "category": "dining_coffee", "lat": 16.067, "lon": 108.220, "style": "modern", "description": "Không gian cafe kính trong suốt ngập tràn ánh sáng và bánh ngọt tươi."}
            ],
            "night_satellites": [
                {"id": "dn_cho_dem_sontra", "name": "Chợ Đêm Sơn Trà & Phố đi bộ", "category": "leisure_shopping", "lat": 16.062, "lon": 108.232, "description": "Khu chợ đêm sầm uất với hàng trăm gian hàng ẩm thực đường phố và quà lưu niệm."}
            ]
        },
        {
            "cluster_id": "dn_bana",
            "cluster_name": "Cụm Bà Nà Hills & Núi Chúa",
            "cluster_type": "mountain_entertainment",
            "center": [15.998, 107.996],
            "morning_anchors": [
                {"id": "dn_ba_na", "name": "Bà Nà Hills & Cầu Vàng", "category": "tourism_heritage", "lat": 15.998, "lon": 107.996, "style": "photo_iconic", "description": "Khu du lịch trên đỉnh núi Chúa với biểu tượng Cầu Vàng bàn tay khổng lồ và Làng Pháp cổ kính."}
            ],
            "afternoon_anchors": [
                {"id": "dn_fantasy", "name": "Fantasy Park & Lâu đài Mặt Trăng", "category": "tourism_heritage", "lat": 15.997, "lon": 107.995, "style": "entertainment", "description": "Công viên giải trí trong nhà lớn nhất Việt Nam với rạp phim 4D/5D và lâu đài kỳ ảo."}
            ],
            "food_satellites_street": [
                {"id": "dn_buffet_bana", "name": "Buffet Làng Pháp Arapang (Bà Nà)", "category": "dining_coffee", "lat": 15.999, "lon": 107.997, "description": "Thưởng thức tiệc buffet Á - Âu với hơn 70 món ngon giữa không gian kiến trúc Pháp."}
            ],
            "food_satellites_luxury": [
                {"id": "dn_kavkaz_restaurant", "name": "Nhà Hàng Kavkaz Vườn Nga (Bà Nà)", "category": "dining_coffee", "lat": 15.9985, "lon": 107.9965, "description": "Thịt cừu nướng xiên kiểu Nga và bia tươi hảo hạng trên đỉnh núi Chúa."}
            ],
            "cafe_satellites": [
                {"id": "dn_doumer_cafe", "name": "Cafe Doumer Vườn Hoa Le Jardin D'Amour", "category": "dining_coffee", "lat": 15.996, "lon": 107.998, "style": "photo", "description": "Thưởng thức cafe giữa vườn hoa cẩm tú cầu rực rỡ sắc màu."}
            ],
            "night_satellites": [
                {"id": "dn_cau_rong", "name": "Cầu Rồng & Du Thuyền Sông Hàn", "category": "leisure_shopping", "lat": 16.061, "lon": 108.227, "description": "Biểu tượng kiến trúc hiện đại của Đà Nẵng, xem Rồng phun lửa và nước vào tối cuối tuần."}
            ]
        },
        {
            "cluster_id": "dn_songhan_nguhanh",
            "cluster_name": "Cụm Sông Hàn, Di Sản Chăm & Ngũ Hành Sơn",
            "cluster_type": "city_culture_food",
            "center": [16.040, 108.240],
            "morning_anchors": [
                {"id": "dn_cham", "name": "Bảo tàng Điêu khắc Chăm", "category": "tourism_heritage", "lat": 16.059, "lon": 108.223, "style": "heritage", "description": "Bảo tàng lưu giữ bộ sưu tập nghệ thuật điêu khắc Champa quy mô lớn nhất thế giới."},
                {"id": "dn_cau_tinh_yeu", "name": "Cầu Tình Yêu & Tượng Cá Chép Hóa Rồng", "category": "tourism_heritage", "lat": 16.062, "lon": 108.230, "style": "photo", "description": "Điểm check-in lãng mạn bên bờ đông sông Hàn với cây cầu khóa tình yêu."}
            ],
            "afternoon_anchors": [
                {"id": "dn_ngu_hanh", "name": "Ngũ Hành Sơn & Động Huyền Không", "category": "spiritual_culture", "lat": 16.004, "lon": 108.263, "style": "heritage_spiritual", "description": "Quần thể 5 ngọn núi đá vôi kỳ vĩ với hệ thống hang động và chùa cổ linh thiêng."},
                {"id": "dn_non_nuoc", "name": "Làng đá mỹ nghệ Non Nước", "category": "tourism_heritage", "lat": 16.008, "lon": 108.258, "style": "craft", "description": "Làng nghề điêu khắc đá truyền thống hơn 300 năm tuổi dưới chân Ngũ Hành Sơn."}
            ],
            "food_satellites_street": [
                {"id": "dn_bep_trang", "name": "Mì Quảng Ếch Bếp Trang", "category": "dining_coffee", "lat": 16.068, "lon": 108.223, "description": "Thưởng thức món Mì Quảng ếch om niêu đất gia truyền đậm đà chuẩn vị xứ Quảng."},
                {"id": "dn_bun_cha_ca", "name": "Bún Chả Cá 109 Nguyễn Chí Thanh", "category": "dining_coffee", "lat": 16.073, "lon": 108.218, "description": "Tô bún chả cá thơm ngọt nước dùng hầm từ bí đỏ và chả cá thu dai giòn."}
            ],
            "food_satellites_luxury": [
                {"id": "dn_quan_tran", "name": "Bánh tráng cuốn thịt heo Quán Trần", "category": "dining_coffee", "lat": 16.071, "lon": 108.219, "description": "Đặc sản thịt heo hai đầu da cuốn bánh tráng Đại Lộc chấm mắm nêm đậm đà trong không gian máy lạnh sang trọng."},
                {"id": "dn_waterfront_danang", "name": "Waterfront Danang Restaurant & Bar", "category": "dining_coffee", "lat": 16.0650, "lon": 108.2240, "description": "Nhà hàng Âu sang trọng ven sông Bạch Đằng ngắm trọn cảnh cầu Rồng."}
            ],
            "cafe_satellites": [
                {"id": "dn_cong_cf", "name": "Cộng Cà Phê Bạch Đằng", "category": "dining_coffee", "lat": 16.069, "lon": 108.225, "style": "chill", "description": "Nhâm nhi cà phê cốt dừa ngắm dòng sông Hàn thơ mộng và các cây cầu biểu tượng."}
            ],
            "night_satellites": [
                {"id": "dn_sky36", "name": "Sky36 Bar Đà Nẵng", "category": "leisure_shopping", "lat": 16.078, "lon": 108.224, "description": "Sky bar cao nhất Đà Nẵng ngắm trọn vẹn toàn cảnh thành phố lung linh về đêm."}
            ]
        }
    ],
    "sa pa": [
        {
            "cluster_id": "sp_fansipan",
            "cluster_name": "Cụm Đỉnh Fansipan & Bản Cát Cát",
            "cluster_type": "mountain_iconic",
            "center": [22.315, 103.805],
            "morning_anchors": [
                {"id": "sp_fansipan", "name": "Đỉnh Fansipan - Nóc Nhà Đông Dương", "category": "tourism_heritage", "lat": 22.303, "lon": 103.775, "style": "photo_iconic", "description": "Chinh phục đỉnh cao 3.143m bằng cáp treo 3 dây kỷ lục thế giới, săn mây bồng bềnh tuyệt mỹ."}
            ],
            "afternoon_anchors": [
                {"id": "sp_cat_cat", "name": "Bản Cát Cát & Thác Tiên Sa", "category": "tourism_heritage", "lat": 22.328, "lon": 103.834, "style": "culture_photo", "description": "Ngôi làng cổ của người H'Mông với cọn nước khổng lồ, ruộng bậc thang và suối Hoa thơ mộng."}
            ],
            "food_satellites_street": [
                {"id": "sp_a_phu", "name": "Nhà hàng A Phủ Sa Pa", "category": "dining_coffee", "lat": 22.334, "lon": 103.841, "description": "Đặc sản gà đen Tây Bắc nướng mật ong rừng, lợn bản cắp nách và ngọn su su xào tỏi."}
            ],
            "food_satellites_luxury": [
                {"id": "sp_chapa_restaurant", "name": "Chapa Gourmet Restaurant Sa Pa", "category": "dining_coffee", "lat": 22.3360, "lon": 103.8400, "description": "Ẩm thực Pháp - Tây Bắc cao cấp kết hợp rượu vang Pháp trong không gian ấm cúng."}
            ],
            "cafe_satellites": [
                {"id": "sp_viettrekking", "name": "Viettrekking Coffee & Restaurant", "category": "dining_coffee", "lat": 22.332, "lon": 103.842, "style": "photo_sunset", "description": "Quán cafe view ngắm đoàn tàu hỏa leo núi Mường Hoa băng qua thung lũng mây."}
            ],
            "night_satellites": [
                {"id": "sp_cho_dem", "name": "Chợ Đêm Sa Pa & Phố nướng", "category": "leisure_shopping", "lat": 22.336, "lon": 103.843, "description": "Khu phố nướng bốc khói nghi ngút với thịt xiên, cơm lam, ngô nướng và thắng cố truyền thống."}
            ]
        },
        {
            "cluster_id": "sp_oquyho",
            "cluster_name": "Cụm Đèo Ô Quy Hồ, Cổng Trời & Thác Bạc",
            "cluster_type": "nature_sunset",
            "center": [22.355, 103.774],
            "morning_anchors": [
                {"id": "sp_thac_bac", "name": "Thác Bạc & Trại Cá Hồi Sa Pa", "category": "tourism_heritage", "lat": 22.360, "lon": 103.780, "style": "nature", "description": "Dòng thác trắng xóa đổ từ độ cao 200m giữa đại ngàn Hoàng Liên Sơn."}
            ],
            "afternoon_anchors": [
                {"id": "sp_o_quy_ho", "name": "Đèo Ô Quy Hồ & Cổng Trời Sa Pa", "category": "tourism_heritage", "lat": 22.355, "lon": 103.774, "style": "photo_sunset", "description": "Một trong tứ đại đỉnh đèo Việt Nam, nơi ngắm hoàng hôn và biển mây hùng vĩ bậc nhất Tây Bắc."}
            ],
            "food_satellites_street": [
                {"id": "sp_song_nhi", "name": "Lẩu Cá Hồi & Cá Tầm Song Nhi", "category": "dining_coffee", "lat": 22.350, "lon": 103.790, "description": "Thưởng thức nồi lẩu cá hồi, cá tầm nước lạnh tươi ngọt giữa thời tiết se lạnh của Sa Pa."}
            ],
            "food_satellites_luxury": [
                {"id": "sp_fansipan_terrace", "name": "Fansipan Terrace Restaurant & Lounge", "category": "dining_coffee", "lat": 22.330, "lon": 103.840, "description": "Nhà hàng sân thượng cao cấp ngắm trọn vẹn dãy Hoàng Liên Sơn hùng vĩ."}
            ],
            "cafe_satellites": [
                {"id": "sp_o_quy_ho_cafe", "name": "Cafe Cổng Trời Ô Quy Hồ", "category": "dining_coffee", "lat": 22.356, "lon": 103.775, "style": "photo_sunset", "description": "Nhâm nhi ly cacao nóng ngắm biển mây cuồn cuộn dưới thung lũng."}
            ],
            "night_satellites": [
                {"id": "sp_nha_tho_dem", "name": "Quảng Trường & Nhà Thờ Đá Sa Pa Về Đêm", "category": "leisure_shopping", "lat": 22.335, "lon": 103.842, "description": "Tham gia chợ tình Sa Pa cuối tuần và ngắm nhà thờ đá lung linh ánh đèn."}
            ]
        }
    ]
}

def is_food_poi(poi: dict) -> bool:
    name = (poi.get("name") or "").lower()
    cat = (poi.get("category") or "").lower()
    sub_cat = (poi.get("sub_category") or "").lower()
    cuisine = (poi.get("cuisine") or "").lower()
    
    not_food = ["lăng", "chùa", "đền", "tháp", "bảo tàng", "hồ gươm", "văn miếu", "hoàng thành", "nhà tù", "công viên", "núi", "đèo", "bãi biển", "cầu rồng", "cầu tình yêu", "cáp treo", "nhà thờ", "trường đại học", "bệnh viện", "công an", "vườn thực vật"]
    if any(kw in name for kw in not_food):
        return False
        
    if cat in ["dining_coffee", "ẩm thực"] or sub_cat in ["restaurant", "fast_food", "food_court"]:
        if any(c in name for c in ["cà phê", "cafe", "coffee", "trà sữa"]) and not any(f in name for f in ["quán", "cơm", "bún", "phở", "bánh", "lẩu", "nướng"]):
            return False
        return True
        
    food_kws = ["quán", "nhà hàng", "bún", "phở", "cơm", "lẩu", "nướng", "hải sản", "restaurant", "nem", "bánh tráng", "buffet", "bò", "gà", "chả", "mì", "ẩm thực", "bếp", "bánh xèo"]
    return any(kw in name for kw in food_kws) or bool(cuisine)

def is_cafe_poi(poi: dict) -> bool:
    name = (poi.get("name") or "").lower()
    cat = (poi.get("category") or "").lower()
    sub_cat = (poi.get("sub_category") or "").lower()
    
    not_cafe = ["lăng", "chùa", "đền", "tháp", "bảo tàng", "hồ gươm", "văn miếu", "hoàng thành", "nhà tù", "công viên", "núi", "đèo", "cầu rồng", "nhà thờ", "trường đại học", "vườn thực vật"]
    if any(kw in name for kw in not_cafe):
        return False
        
    return any(kw in name for kw in ["cà phê", "cafe", "coffee", "tea", "trà đá", "trà chanh", "giảng", "marina", "wonderlust", "cộng", "túi mơ to", "viettrekking"]) or (cat == "dining_coffee" and sub_cat == "coffee")

def is_night_poi(poi: dict) -> bool:
    name = (poi.get("name") or "").lower()
    return any(k in name for k in ["chợ đêm", "phố đi bộ", "tạ hiện", "sky36", "bar", "pub", "lounge", "du thuyền", "cầu rồng", "phố nướng"])

def get_theme_img(poi: dict) -> str:
    cat = (poi.get("category") or "").lower()
    name = (poi.get("name") or "").lower()
    
    if any(k in name for k in ["lăng bác", "hồ gươm", "văn miếu", "chùa", "đền", "tháp", "nhà thờ", "hoàng thành", "bà nà", "fansipan"]):
        return "https://images.unsplash.com/photo-1548625361-125026723b72?auto=format&fit=crop&w=600&q=80"
    if any(k in name for k in ["cà phê", "cafe", "coffee", "trà", "tea"]):
        return "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=600&q=80"
    if any(k in name for k in ["phở", "bún", "cơm", "bánh", "lẩu", "nướng", "hải sản", "quán", "mì"]):
        return "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80"
    if any(k in name for k in ["biển", "núi", "đèo", "bãi"]):
        return "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80"
    return "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=600&q=80"

class RagEngine:
    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path
        self.knowledge = {}

    def load_index(self):
        print(f"[RAG] Using SQLite Vector Knowledge Base: {DB_PATH}")

    def _query_sqlite(self, query_str: str, limit: int = 20) -> list:
        if not DB_PATH.exists():
            return []
        pois = []
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            clean_q = re.sub(r'[^\w\s]', ' ', query_str).strip()
            
            if clean_q:
                fts_sql = """
                    SELECT pois.id, pois.name, pois.category, pois.sub_category, pois.address, 
                           pois.lat, pois.lon, pois.description, pois.cuisine, pois.open_hours
                    FROM pois_fts
                    JOIN pois ON pois_fts.rowid = pois.id
                    WHERE pois_fts MATCH ?
                    ORDER BY 
                        CASE WHEN pois.name LIKE ? THEN 1 ELSE 2 END,
                        CASE WHEN pois.category = 'tourism_heritage' THEN 1 
                             WHEN pois.category = 'spiritual_culture' THEN 2
                             WHEN pois.category = 'dining_coffee' THEN 3
                             ELSE 4 END,
                        rank
                    LIMIT ?
                """
                words = clean_q.split()
                fts_expr = " OR ".join(f'"{w}"*' for w in words if len(w) > 1)
                rows = c.execute(fts_sql, (fts_expr, f"%{clean_q}%", limit)).fetchall()
                if not rows:
                    rows = c.execute(fts_sql, (f'"{clean_q}"', f"%{clean_q}%", limit)).fetchall()
            else:
                rows = c.execute("SELECT id, name, category, sub_category, address, lat, lon, description, cuisine, open_hours FROM pois ORDER BY CASE WHEN category IN ('tourism_heritage', 'spiritual_culture', 'dining_coffee') THEN 1 ELSE 2 END LIMIT ?", (limit,)).fetchall()
                
            pois = [dict(r) for r in rows]
            conn.close()
        except Exception as e:
            print(f"[RAG] DB Query error: {e}")
        return pois

    def get_pois_for_destination(self, dest: str, limit: int = 100) -> list:
        norm_clean = remove_vn_accents(dest).replace(' ', '')
        
        for city_key, clusters in CITY_GEO_CLUSTERS.items():
            k_clean = remove_vn_accents(city_key).replace(' ', '')
            if k_clean in norm_clean or norm_clean in k_clean:
                all_cluster_pois = []
                for c in clusters:
                    all_cluster_pois.extend(c.get("morning_anchors", []))
                    all_cluster_pois.extend(c.get("afternoon_anchors", []))
                    all_cluster_pois.extend(c.get("food_satellites_street", []))
                    all_cluster_pois.extend(c.get("food_satellites_luxury", []))
                    all_cluster_pois.extend(c.get("cafe_satellites", []))
                    all_cluster_pois.extend(c.get("night_satellites", []))
                return all_cluster_pois.copy()

        norm_dest = remove_vn_accents(dest)
        if "ha noi" in norm_dest or "hanoi" in norm_dest or not norm_dest:
            db_pois = self._query_sqlite(dest, limit=limit)
            if len(db_pois) >= 5:
                return db_pois
            return self._query_sqlite("", limit=limit)

        db_pois = self._query_sqlite(dest, limit=limit)
        if len(db_pois) >= 3:
            return db_pois

        return []

    def get_structured_itinerary(self, trip_data: dict) -> dict:
        dest_raw = trip_data.get("destination", "Hà Nội")
        budget = trip_data.get("budget", "5000000")
        companion = trip_data.get("companion", "Cặp đôi")
        group_size = trip_data.get("group_size", "2 người")
        vehicle = trip_data.get("vehicle", "Xe máy")
        accommodation = trip_data.get("accommodation", "Khách sạn 3-4 sao")
        specific_hotel = trip_data.get("specific_hotel", "")
        dining_style = trip_data.get("dining_style", "Hài hòa")
        trip_objective = trip_data.get("trip_objective", "") or trip_data.get("style", "") or trip_data.get("pacing", "Khám phá")
        start_date_str = trip_data.get("start_date", "")
        must_visit_raw = trip_data.get("must_visit", "") or trip_data.get("requirements", "")
        
        try:
            num_days = int(trip_data.get("num_days", 3))
        except:
            num_days = 3
            
        norm_clean = remove_vn_accents(dest_raw).replace(' ', '')
        
        city_clusters = None
        for city_key, clusters in CITY_GEO_CLUSTERS.items():
            k_clean = remove_vn_accents(city_key).replace(' ', '')
            if k_clean in norm_clean or norm_clean in k_clean:
                city_clusters = clusters
                break
                
        if not city_clusters:
            city_clusters = CITY_GEO_CLUSTERS["hà nội"]
            
        must_visit_items = [w.strip().lower() for w in must_visit_raw.split(",") if w.strip()]
        hotel_norm = remove_vn_accents(specific_hotel)
        obj_norm = remove_vn_accents(trip_objective)
        
        # =========================================================================
        # 1. ĐÁNH GIÁ ĐỘ ƯU TIÊN VÀ XẾP HẠNG CỤM ĐỊA LÝ (MULTI-ATTRIBUTE RANKING)
        # =========================================================================
        ranked_clusters = []
        for cluster in city_clusters:
            score = 0
            c_id = cluster["cluster_id"]
            
            # Tiêu chí A: Khớp với Điểm bắt buộc (Must-Visit) -> Điểm cộng cực đại
            all_anchors = cluster["morning_anchors"] + cluster["afternoon_anchors"]
            for anchor in all_anchors:
                a_name = anchor["name"].lower()
                for mv in must_visit_items:
                    if mv in a_name or any(w in a_name for w in mv.split() if len(w) > 2):
                        score += 50
                        
            # Tiêu chí B: Khớp với Vị trí Khách sạn người dùng đã chọn / nhập
            if hotel_norm:
                if any(kw in hotel_norm for kw in ["tay ho", "truc bach", "yen phu", "ho tay", "intercontinental", "pan pacific", "sheraton", "tu hoa", "xuan dieu"]) and "tayho" in c_id:
                    score += 65
                elif any(kw in hotel_norm for kw in ["hoan kiem", "pho co", "hang ", "dinh tien hoang", "ly thai to", "trang tien", "metropole", "apricot", "oriental", "somerset", "la siesta", "classic"]) and "hoankiem" in c_id:
                    score += 65
                elif any(kw in hotel_norm for kw in ["ba dinh", "doi can", "giang vo", "kim ma", "lieu giai", "lotte", "golden lake", "dolce", "daewoo"]) and "badinh" in c_id:
                    score += 65
                elif any(kw in hotel_norm for kw in ["cau giay", "my dinh", "nam tu liem", "pham hung", "keangnam", "duy tan", "marriott", "jw marriott", "novotel", "grand plaza"]) and ("caugiay" in c_id or "badinh" in c_id):
                    score += 60
                elif any(kw in hotel_norm for kw in ["my khe", "son tra", "vo nguyen giap", "bien", "davue"]) and "sontra" in c_id:
                    score += 65
                elif any(kw in hotel_norm for kw in ["song han", "hai chau", "bach dang", "ngu hanh", "sanouva"]) and "songhan" in c_id:
                    score += 65
                elif any(kw in hotel_norm for kw in ["ba na", "nui chua"]) and "bana" in c_id:
                    score += 65
                elif any(kw in hotel_norm for kw in ["fansipan", "cat cat", "muong hoa"]) and "fansipan" in c_id:
                    score += 65
                elif any(kw in hotel_norm for kw in ["o quy ho", "thac bac", "cong troi"]) and "oquyho" in c_id:
                    score += 65

            # Tiêu chí C: Khớp với Phong cách / Mục tiêu chuyến đi (Trip Objective)
            if any(k in obj_norm for k in ["am thuc", "food", "an uong"]):
                if "hoankiem" in c_id or "sontra" in c_id or "songhan" in c_id or "tayho" in c_id:
                    score += 25
            elif any(k in obj_norm for k in ["chill", "nghi duong", "thu thai", "cafe"]):
                if "tayho" in c_id or "sontra" in c_id or "oquyho" in c_id:
                    score += 25
            elif any(k in obj_norm for k in ["song ao", "photo", "checkin", "check in"]):
                if "hoankiem" in c_id or "bana" in c_id or "fansipan" in c_id or "sontra" in c_id:
                    score += 25
            elif any(k in obj_norm for k in ["di san", "lich su", "van hoa"]):
                if "badinh" in c_id or "songhan" in c_id:
                    score += 25

            # Thêm ngẫu nhiên nhẹ để đa dạng hóa lộ trình khi tạo lại
            score += random.uniform(0.1, 4.0)

            ranked_clusters.append((score, cluster))

        # Sắp xếp các cụm theo điểm số cá nhân hóa
        ranked_clusters.sort(key=lambda x: x[0], reverse=True)
        selected_clusters = [c[1] for c in ranked_clusters]
        
        while len(selected_clusters) < num_days:
            selected_clusters.extend(city_clusters)
        selected_clusters = selected_clusters[:num_days]
        
        # Ngày khởi hành
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            except:
                start_date = datetime.now() + timedelta(days=5)
        else:
            start_date = datetime.now() + timedelta(days=5)
            
        vn_day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        global_visited_ids = set()
        days_out = []
        
        # Nhận diện Gu ẩm thực & Ngân sách
        is_luxury_dining = ("sang trọng" in dining_style.lower()) or ("cao cấp" in dining_style.lower())
        try:
            b_val = float(re.sub(r'[^\d]', '', str(budget)))
        except:
            b_val = 5000000
        if b_val >= 10000000:
            is_luxury_dining = True
            
        for day_idx, cluster in enumerate(selected_clusters):
            curr_date = start_date + timedelta(days=day_idx)
            date_str = curr_date.strftime("%d/%m")
            day_name = vn_day_names[curr_date.weekday()]
            
            # 1. Điểm tham quan sáng (Morning Anchor)
            m_anchor = None
            for a in cluster["morning_anchors"]:
                if a["id"] not in global_visited_ids:
                    if any(mv in a["name"].lower() for mv in must_visit_items):
                        m_anchor = a
                        break
            if not m_anchor:
                unvisited_morning = [a for a in cluster["morning_anchors"] if a["id"] not in global_visited_ids]
                m_anchor = random.choice(unvisited_morning) if unvisited_morning else cluster["morning_anchors"][0]
            global_visited_ids.add(m_anchor["id"])
            
            # 2. Điểm tham quan chiều (Afternoon Anchor)
            af_anchor = None
            unvisited_af = [a for a in cluster["afternoon_anchors"] if a["id"] not in global_visited_ids]
            if unvisited_af:
                af_anchor = random.choice(unvisited_af)
            else:
                af_anchor = cluster["afternoon_anchors"][0]
            global_visited_ids.add(af_anchor["id"])
            
            # 3. Quán Cà phê sáng (Thích ứng theo Phong cách)
            all_cafes = cluster.get("cafe_satellites", [])
            if any(k in obj_norm for k in ["chill", "nghi duong"]):
                filtered_cafes = [c for c in all_cafes if "chill" in c.get("style", "")] or all_cafes
            elif any(k in obj_norm for k in ["song ao", "photo"]):
                filtered_cafes = [c for c in all_cafes if "photo" in c.get("style", "")] or all_cafes
            else:
                filtered_cafes = all_cafes
                
            cafe_satellites = sorted(filtered_cafes, key=lambda c: haversine_km(c["lat"], c["lon"], m_anchor["lat"], m_anchor["lon"]))
            # Chọn ngẫu nhiên trong top 2 cafe gần nhất để đa dạng hóa
            top_cafes = cafe_satellites[:min(2, len(cafe_satellites))]
            cafe_poi = random.choice(top_cafes) if top_cafes else cafe_satellites[0]
            
            # 4. Quán ăn trưa đặc sản
            if is_luxury_dining and cluster.get("food_satellites_luxury"):
                food_pool = cluster["food_satellites_luxury"]
            else:
                food_pool = cluster.get("food_satellites_street", []) or cluster.get("food_satellites", [])
                
            food_satellites = sorted(food_pool, key=lambda f: haversine_km(f["lat"], f["lon"], m_anchor["lat"], m_anchor["lon"]))
            top_lunch = food_satellites[:min(2, len(food_satellites))]
            lunch_poi = random.choice(top_lunch) if top_lunch else food_satellites[0]
            
            # 5. Bữa tối & Phố đêm (Kề cận Afternoon Anchor)
            night_satellites = cluster.get("night_satellites", [])
            if night_satellites:
                dinner_poi = night_satellites[0]
            elif is_luxury_dining and cluster.get("food_satellites_luxury"):
                dinner_poi = cluster["food_satellites_luxury"][-1]
            else:
                dinner_poi = food_satellites[-1]
                
            dist_1 = 0.0
            dist_2 = round(haversine_km(cafe_poi["lat"], cafe_poi["lon"], m_anchor["lat"], m_anchor["lon"]), 1)
            dist_3 = round(haversine_km(m_anchor["lat"], m_anchor["lon"], lunch_poi["lat"], lunch_poi["lon"]), 1)
            dist_4 = round(haversine_km(lunch_poi["lat"], lunch_poi["lon"], af_anchor["lat"], af_anchor["lon"]), 1)
            dist_5 = round(haversine_km(af_anchor["lat"], af_anchor["lon"], dinner_poi["lat"], dinner_poi["lon"]), 1)
            
            def get_trans_badge(dist):
                if dist <= 0.6:
                    return f"🚶 Đi bộ thong thả ~{int(dist*1000)}m ({max(3, int(dist*12))} phút)"
                elif dist <= 1.5:
                    return f"🚶/🛵 Đi bộ ~{dist}km hoặc 2p {vehicle}"
                else:
                    return f"🛵 {vehicle} ~{dist}km ({max(5, int(dist*3))} phút)"
            
            acts = [
                {
                    "time": "08:00",
                    "title": f"☕ Cà phê sáng: {cafe_poi['name']}",
                    "desc": cafe_poi["description"],
                    "lat": cafe_poi["lat"],
                    "lng": cafe_poi["lon"],
                    "img": get_theme_img(cafe_poi),
                    "distance_from_prev": dist_1,
                    "transport_badge": ""
                },
                {
                    "time": "09:30",
                    "title": f"🏛️ Tham quan & Check-in: {m_anchor['name']}",
                    "desc": m_anchor["description"],
                    "lat": m_anchor["lat"],
                    "lng": m_anchor["lon"],
                    "img": get_theme_img(m_anchor),
                    "distance_from_prev": dist_2,
                    "transport_badge": get_trans_badge(dist_2)
                },
                {
                    "time": "12:00",
                    "title": f"🍜 Bữa trưa đặc sản: {lunch_poi['name']}",
                    "desc": lunch_poi["description"],
                    "lat": lunch_poi["lat"],
                    "lng": lunch_poi["lon"],
                    "img": get_theme_img(lunch_poi),
                    "distance_from_prev": dist_3,
                    "transport_badge": get_trans_badge(dist_3)
                },
                {
                    "time": "14:30",
                    "title": f"📸 Trải nghiệm & Di sản: {af_anchor['name']}",
                    "desc": af_anchor["description"],
                    "lat": af_anchor["lat"],
                    "lng": af_anchor["lon"],
                    "img": get_theme_img(af_anchor),
                    "distance_from_prev": dist_4,
                    "transport_badge": get_trans_badge(dist_4)
                },
                {
                    "time": "19:00",
                    "title": f"🍲 Bữa tối & Phố đêm: {dinner_poi['name']}",
                    "desc": dinner_poi["description"],
                    "lat": dinner_poi["lat"],
                    "lng": dinner_poi["lon"],
                    "img": get_theme_img(dinner_poi),
                    "distance_from_prev": dist_5,
                    "transport_badge": get_trans_badge(dist_5)
                }
            ]
            
            total_day_km = round(dist_1 + dist_2 + dist_3 + dist_4 + dist_5, 1)
            
            days_out.append({
                "dayNum": day_idx + 1,
                "title": f"Ngày {day_idx + 1} ({day_name} {date_str}): {cluster['cluster_name']}",
                "total_km": total_day_km,
                "activities": acts
            })

        # Tra cứu thông tin khách sạn thực tế có tọa độ GPS để vẽ lên bản đồ (Nếu có chọn khách sạn)
        is_no_hotel = any(k in accommodation.lower() for k in ["chưa chọn", "đi trong ngày", "khong"]) or any(k in specific_hotel.lower() for k in ["chưa chọn", "đi trong ngày"])
        
        hotel_info = None
        if not is_no_hotel and (specific_hotel or accommodation):
            import sqlite3
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                target_hotel_query = specific_hotel or accommodation
                # 1. Tìm chính xác theo tên khách sạn hoặc thành phố
                row = c.execute(
                    "SELECT * FROM hotels WHERE (city LIKE ? OR ? LIKE '%' || city || '%') AND (name LIKE ? OR ? LIKE '%' || name || '%')", 
                    (f"%{dest_raw}%", dest_raw, f"%{target_hotel_query}%", target_hotel_query)
                ).fetchone()
                # 2. Tìm theo từ khóa đầu tiên của specific_hotel
                if not row and specific_hotel:
                    keyword = specific_hotel.split()[0] if specific_hotel.split() else ""
                    if keyword:
                        row = c.execute(
                            "SELECT * FROM hotels WHERE (city LIKE ? OR ? LIKE '%' || city || '%') AND name LIKE ?", 
                            (f"%{dest_raw}%", dest_raw, f"%{keyword}%")
                        ).fetchone()
                # 3. Mặc định lấy khách sạn nổi tiếng đầu tiên của thành phố đó NẾU CÓ CHỌN LOẠI HÌNH KHÁCH SẠN CỤ THỂ
                if not row and specific_hotel:
                    row = c.execute(
                        "SELECT * FROM hotels WHERE (city LIKE ? OR ? LIKE '%' || city || '%') LIMIT 1", 
                        (f"%{dest_raw}%", dest_raw)
                    ).fetchone()
                if row:
                    hotel_info = dict(row)
                conn.close()
            except Exception as e:
                pass

        # Phụ đề cá nhân hóa
        if is_no_hotel:
            hotel_str = "Tự do / Đi trong ngày"
        elif hotel_info:
            hotel_str = f"Nghỉ tại {hotel_info['name']}"
        else:
            hotel_str = f"Nghỉ tại {specific_hotel or accommodation}"

        style_str = f" • Phong cách: {trip_objective}" if trip_objective and trip_objective not in ["Khám phá", "Cân bằng"] else ""
        subtitle = f"Thiết kế riêng cho {companion} ({group_size}) • Di chuyển bằng {vehicle} • {hotel_str}{style_str}"

        # Phân bổ chi phí
        cost_str = f"{int(b_val):,} VNĐ / người".replace(",", ".")
        hotel_cost = int(b_val * 0.4)
        food_cost = int(b_val * 0.35)
        ticket_cost = int(b_val * 0.25)
        cost_details = f"{accommodation} ({num_days-1} đêm): {hotel_cost:,}k • Ẩm thực ({num_days}N): {food_cost:,}k • Vé & Xe: {ticket_cost:,}k".replace(",", ".")

        center_coords = selected_clusters[0]["center"]

        return {
            "destination": dest_raw,
            "title": f"Lịch Trình • {dest_raw} ({num_days}N{num_days-1}Đ)",
            "subtitle": subtitle,
            "cost": cost_str,
            "costDetails": cost_details,
            "center": center_coords,
            "hotel": hotel_info,
            "days": days_out
        }
