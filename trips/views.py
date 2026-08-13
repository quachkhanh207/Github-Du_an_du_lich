from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from trips.models import Trip, Itinerary, Photo, ChecklistItem
from datetime import datetime
from django.core.cache import cache

# Import mã nguồn của Khánh
import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from khanh.api_services import get_location_coordinates, get_realtime_weather
from khanh.rule_engine import BeeNaviRuleEngine

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def trips_list_create(request):
    if request.method == 'POST':
        data = request.data
        destination = data.get('destination')
        departure_location = data.get('departure_location')
        start_date_str = data.get('start_date')
        number_of_days = data.get('number_of_days', 1)
        budget_limit = data.get('budget_limit', 0.0)
        days = data.get('days', [])
        reminder_enabled = data.get('reminder_enabled', False)
        reminder_settings = data.get('reminder_settings', {})
        vehicle = data.get('vehicle', 'Xe máy')
        trip_type = data.get('trip_type', 'Phượt')

        if not destination or not start_date_str:
            return Response({"detail": "Điểm đến và ngày khởi hành là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except Exception:
            start_date = datetime.now()

        # Liên kết với người dùng đang đăng nhập nếu có
        user = request.user if request.user.is_authenticated else None

        trip = Trip.objects.create(
            user=user,
            destination=destination,
            departure_location=departure_location,
            start_date=start_date,
            number_of_days=number_of_days,
            budget_limit=budget_limit,
            vehicle=vehicle,
            trip_type=trip_type,
            reminder_enabled=reminder_enabled,
            reminder_settings=reminder_settings
        )

        itinerary = Itinerary.objects.create(
            trip=trip,
            days=days
        )

        # 1. Gọi API định vị & thời tiết thực tế từ code của Khánh
        try:
            dest_coords = get_location_coordinates(destination)
            if dest_coords:
                weather = get_realtime_weather(dest_coords["lat"], dest_coords["lon"])
                weather_tag = weather.get("weather_tag", "Nắng")
            else:
                weather_tag = "Nắng"
        except Exception:
            weather_tag = "Nắng"

        # 2. Chạy Rule Engine của Khánh để sinh đồ dùng động từ dataset_checklist.txt
        try:
            dataset_abs = str(repo_root / "khanh" / "dataset_checklist.txt")
            engine = BeeNaviRuleEngine(dataset_path=dataset_abs)
            seeded_items = engine.filter_checklist(
                weather_tag=weather_tag,
                vehicle=vehicle,
                trip_type=trip_type,
                days=number_of_days
            )
            
            default_items = []
            for item in seeded_items:
                default_items.append({
                    "item_name": item["name"],
                    "category": item["category"],
                    "quantity": item["quantity"],
                    "priority": item["priority"]
                })
        except Exception as e:
            # Fallback nếu Rule Engine lỗi
            default_items = [
                {"item_name": "CCCD / Hộ chiếu", "category": "Giấy tờ cá nhân", "quantity": 1, "priority": "Bắt buộc"},
                {"item_name": "Vé tàu xe / Vé máy bay", "category": "Giấy tờ cá nhân", "quantity": 1, "priority": "Bắt buộc"},
                {"item_name": "Tiền mặt & Thẻ ngân hàng", "category": "Giấy tờ cá nhân", "quantity": 1, "priority": "Bắt buộc"},
                {"item_name": "Điện thoại & Cáp sạc", "category": "Thiết bị công nghệ", "quantity": 1, "priority": "Bắt buộc"},
                {"item_name": "Sạc dự phòng", "category": "Thiết bị công nghệ", "quantity": 1, "priority": "Bắt buộc"},
                {"item_name": "Bàn chải & Kem đánh răng", "category": "Đồ dùng cá nhân", "quantity": 1, "priority": "Bắt buộc"},
                {"item_name": f"Quần áo du lịch ({number_of_days} bộ)", "category": "Trang phục", "quantity": number_of_days, "priority": "Bắt buộc"}
            ]
        
        # 3. Rule Engine theo Hồ sơ Cá nhân hóa của User (User Profile Rules - Đã khởi tạo từ trước)
        if user:
            try:
                # Lấy profile đã tạo từ app users
                profile = user.profile
                
                # Check Dị ứng thực phẩm -> nhắc mang thuốc dị ứng
                if profile.food_allergies:
                    allergies_str = ", ".join(profile.food_allergies)
                    default_items.append({
                        "item_name": f"Thuốc dị ứng đặc trị (Lưu ý dị ứng: {allergies_str})", 
                        "category": "Y tế & Mỹ phẩm",
                        "quantity": 1,
                        "priority": "Bắt buộc"
                    })
                    
                # Check Yêu cầu đặc biệt
                if profile.special_requirements:
                    if "Lối đi xe lăn" in profile.special_requirements:
                        default_items.append({
                            "item_name": "Thiết bị hỗ trợ di chuyển & Hồ sơ khám y khoa", 
                            "category": "Y tế & Mỹ phẩm",
                            "quantity": 1,
                            "priority": "Bắt buộc"
                        })
                    if "Ăn chay" in profile.special_requirements:
                        default_items.append({
                            "item_name": "Đồ ăn nhẹ chay đóng hộp (đề phòng)", 
                            "category": "Ăn uống & Thực phẩm",
                            "quantity": 2,
                            "priority": "Khuyến khích"
                        })
                    
                # Check Sở thích ngách
                if profile.niche_interests:
                    if any(x in profile.niche_interests for x in ["Chụp ảnh film", "Chụp ảnh"]):
                        default_items.append({
                            "item_name": "Máy ảnh & Cuộn film / Sạc pin máy ảnh", 
                            "category": "Thiết bị công nghệ",
                            "quantity": 1,
                            "priority": "Khuyến khích"
                        })
                    if "Cắm trại" in profile.niche_interests:
                        default_items.append({
                            "item_name": "Đèn pin & Dụng cụ đa năng dã ngoại", 
                            "category": "Camping & Trekking",
                            "quantity": 1,
                            "priority": "Khuyến khích"
                        })
                        
                # Check Phong cách du lịch
                if profile.travel_style and "Mạo hiểm" in profile.travel_style:
                    default_items.append({
                        "item_name": "Bộ sơ cứu y tế cá nhân (First-aid kit)", 
                        "category": "Y tế & Mỹ phẩm",
                        "quantity": 1,
                        "priority": "Bắt buộc"
                    })
            except Exception:
                pass

        checklist_objs = [
            ChecklistItem(
                trip=trip, 
                item_name=item["item_name"], 
                category=item["category"],
                quantity=item.get("quantity", 1),
                priority=item.get("priority", "Bắt buộc")
            )
            for item in default_items
        ]
        ChecklistItem.objects.bulk_create(checklist_objs)

        return Response({
            "trip_id": str(trip.id),
            "destination": trip.destination,
            "departure_location": trip.departure_location,
            "start_date": trip.start_date.isoformat(),
            "number_of_days": trip.number_of_days,
            "budget_limit": trip.budget_limit,
            "vehicle": trip.vehicle,
            "trip_type": trip.trip_type,
            "reminder_enabled": trip.reminder_enabled,
            "reminder_settings": trip.reminder_settings,
            "days": itinerary.days
        }, status=status.HTTP_201_CREATED)


    elif request.method == 'GET':
        # Lọc chuyến đi: Nếu có user đăng nhập thì chỉ lấy của user đó, ngược lại lấy toàn bộ
        if request.user.is_authenticated:
            trips = Trip.objects.filter(user=request.user).order_by('-created_at')
        else:
            trips = Trip.objects.all().order_by('-created_at')
        trips_list = []
        for trip in trips:
            photo_count = Photo.objects.filter(trip=trip).count()
            trips_list.append({
                "id": str(trip.id),
                "destination": trip.destination,
                "departure_location": trip.departure_location,
                "start_date": trip.start_date.isoformat() if trip.start_date else "",
                "number_of_days": trip.number_of_days,
                "budget_limit": trip.budget_limit,
                "status": trip.status,
                "reminder_enabled": trip.reminder_enabled,
                "reminder_settings": trip.reminder_settings,
                "photo_count": photo_count,
                "created_at": trip.created_at.isoformat()
            })
        return Response(trips_list)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([AllowAny])
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    if request.method in ['PUT', 'PATCH']:
        data = request.data
        if 'reminder_enabled' in data:
            trip.reminder_enabled = data['reminder_enabled']
        if 'reminder_settings' in data:
            trip.reminder_settings = data['reminder_settings']
        if 'budget_limit' in data:
            trip.budget_limit = data['budget_limit']
        if 'status' in data:
            trip.status = data['status']
        trip.save()
    
    try:
        itinerary = Itinerary.objects.get(trip=trip)
        days = itinerary.days
    except Itinerary.DoesNotExist:
        days = []
        
    photos = Photo.objects.filter(trip=trip)
    photos_list = [{
        "id": str(p.id),
        "image_url": p.image_url,
        "caption": p.caption,
        "location_tag": p.location_tag,
        "created_at": p.created_at.isoformat()
    } for p in photos]
    
    checklist_items = ChecklistItem.objects.filter(trip=trip).order_by('id')
    checklist_list = [{
        "id": item.id,
        "item_name": item.item_name,
        "category": item.category,
        "quantity": item.quantity,
        "priority": item.priority,
        "is_completed": item.is_completed,
        "created_at": item.created_at.isoformat()
    } for item in checklist_items]
    
    return Response({
        "id": str(trip.id),
        "destination": trip.destination,
        "departure_location": trip.departure_location,
        "start_date": trip.start_date.isoformat() if trip.start_date else "",
        "number_of_days": trip.number_of_days,
        "budget_limit": trip.budget_limit,
        "status": trip.status,
        "vehicle": trip.vehicle,
        "trip_type": trip.trip_type,
        "reminder_enabled": trip.reminder_enabled,
        "reminder_settings": trip.reminder_settings,
        "days": days,
        "photos": photos_list,
        "checklist": checklist_list
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def add_photo(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    image_url = request.data.get('image_url')
    caption = request.data.get('caption')
    location_tag = request.data.get('location_tag')
    
    if not image_url:
        return Response({"detail": "URL hình ảnh là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)
        
    url_lower = image_url.lower()
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
    if not any(url_lower.endswith(ext) for ext in valid_extensions):
        return Response({"detail": "Định dạng URL hình ảnh không hợp lệ (chỉ nhận JPG, PNG, WEBP)"}, status=status.HTTP_400_BAD_REQUEST)
        
    if Photo.objects.filter(trip=trip).count() >= 100:
        return Response({"detail": "Mỗi chuyến đi chỉ được lưu trữ tối đa 100 bức ảnh kỉ niệm"}, status=status.HTTP_400_BAD_REQUEST)
        
    photo = Photo.objects.create(
        trip=trip,
        image_url=image_url,
        caption=caption,
        location_tag=location_tag
    )
    
    return Response({
        "id": str(photo.id),
        "trip_id": str(trip.id),
        "image_url": photo.image_url,
        "caption": photo.caption,
        "location_tag": photo.location_tag,
        "created_at": photo.created_at.isoformat()
    }, status=status.HTTP_201_CREATED)

def _analyze_user_travel_dna(trips_qs):
    # Điểm mặc định cơ bản bắt đầu từ 10 để tránh hiển thị 0%
    scores = {
        "nature": 10,
        "culture": 10,
        "adventure": 10,
        "relaxation": 10,
        "city": 10,
        "food": 10,
        "shopping": 10
    }
    
    # Lưu trữ bằng chứng để phục vụ giải thích "Why This Score"
    evidence = {
        "nature": [],
        "culture": [],
        "adventure": [],
        "relaxation": [],
        "city": [],
        "food": [],
        "shopping": []
    }
    
    # Phân nhóm chi tiêu
    spending = {
        "lodging": 0.0,
        "transport": 0.0,
        "food": 0.0,
        "activities": 0.0,
        "shopping": 0.0
    }
    
    total_trips = trips_qs.count()
    if total_trips == 0:
        return scores, evidence, spending, 0
        
    # Sắp xếp các chuyến đi từ cũ đến mới để áp dụng trọng số thời gian (chuyến đi mới có trọng số cao hơn)
    trips_sorted = list(trips_qs.order_by('created_at'))
    
    for idx, trip in enumerate(trips_sorted):
        # Trọng số thời gian: chuyến đi gần nhất có hệ số lớn hơn
        time_weight = (idx + 1) / len(trips_sorted)
        
        # 1. Phân tích loại hình chuyến đi (trip_type)
        t_type = trip.trip_type.lower() if trip.trip_type else ""
        if 'camping' in t_type or 'trekking' in t_type:
            scores["nature"] += int(30 * time_weight)
            scores["adventure"] += int(20 * time_weight)
            evidence["nature"].append(f"Chuyến đi dã ngoại '{trip.destination}' ({trip.trip_type})")
            evidence["adventure"].append(f"Khám phá trekking tại '{trip.destination}'")
        elif 'nghỉ dưỡng' in t_type or 'resort' in t_type or 'relax' in t_type:
            scores["relaxation"] += int(35 * time_weight)
            evidence["relaxation"].append(f"Nghỉ dưỡng thư thái tại '{trip.destination}'")
        elif 'phượt' in t_type or 'adventure' in t_type:
            scores["adventure"] += int(35 * time_weight)
            evidence["adventure"].append(f"Phượt khám phá cung đường '{trip.destination}'")
        elif 'đô thị' in t_type or 'city' in t_type:
            scores["city"] += int(30 * time_weight)
            evidence["city"].append(f"Khám phá đô thị nhộn nhịp '{trip.destination}'")

        # 2. Phân tích lộ trình chi tiết từng ngày
        try:
            itinerary = Itinerary.objects.get(trip=trip)
            days = itinerary.days or []
        except Itinerary.DoesNotExist:
            days = []
            
        for day in days:
            schedule = day.get('schedule', [])
            for item in schedule:
                poi_name = item.get('poi_name', '').lower()
                cat = item.get('category', '').lower()
                budget_tier = item.get('budget_tier', 'Tiêu chuẩn')
                
                # Ước tính chi phí theo mức chi tiêu của địa điểm
                cost = 0.0
                if budget_tier == 'Tiêu chuẩn':
                    cost = 300000.0
                elif budget_tier == 'Tiết kiệm':
                    cost = 100000.0
                elif budget_tier == 'Cao cấp' or budget_tier == 'Sang trọng':
                    cost = 1500000.0
                    
                # Phân loại theo category hoặc từ khóa
                if cat == 'food' or any(k in poi_name for k in ['ăn', 'uống', 'lẩu', 'phở', 'mì', 'cơm', 'hải sản', 'cafe', 'quán']):
                    spending["food"] += cost
                    scores["food"] += int(5 * time_weight)
                    if len(evidence["food"]) < 4:
                        evidence["food"].append(f"Thưởng thức '{item.get('poi_name')}' tại {trip.destination}")
                elif cat == 'sightseeing' or cat == 'activity':
                    # Kiểm tra đặc trưng Thiên nhiên
                    if any(k in poi_name for k in ['thác', 'hồ', 'đồi chè', 'núi', 'rừng', 'vườn hoa', 'suối', 'bãi biển', 'hang', 'sông', 'vịnh']):
                        scores["nature"] += int(8 * time_weight)
                        if len(evidence["nature"]) < 4:
                            evidence["nature"].append(f"Ghé thăm cảnh đẹp tự nhiên '{item.get('poi_name')}'")
                    # Kiểm tra đặc trưng Văn hóa
                    if any(k in poi_name for k in ['chùa', 'dinh', 'lăng', 'bảo tàng', 'di tích', 'phố cổ', 'nhà thờ', 'văn miếu', 'đền', 'hội an']):
                        scores["culture"] += int(10 * time_weight)
                        if len(evidence["culture"]) < 4:
                            evidence["culture"].append(f"Tìm hiểu lịch sử/văn hóa tại '{item.get('poi_name')}'")
                    # Kiểm tra đặc trưng Phiêu lưu
                    if any(k in poi_name for k in ['trượt', 'leo núi', 'phượt', 'safari', 'khám phá', 'trekking', 'vượt thác']):
                        scores["adventure"] += int(10 * time_weight)
                        if len(evidence["adventure"]) < 4:
                            evidence["adventure"].append(f"Trải nghiệm cảm giác mạnh tại '{item.get('poi_name')}'")
                    # Kiểm tra đặc trưng Nghỉ dưỡng
                    if any(k in poi_name for k in ['tắm biển', 'massage', 'spa', 'hoàng hôn', 'resort', 'nghỉ ngơi', 'bể bơi']):
                        scores["relaxation"] += int(8 * time_weight)
                        if len(evidence["relaxation"]) < 4:
                            evidence["relaxation"].append(f"Thư giãn giải trí ở '{item.get('poi_name')}'")
                    # Kiểm tra đặc trưng Thành phố
                    if any(k in poi_name for k in ['quảng trường', 'bưu điện', 'landmark', 'phố đi bộ', 'nhà hát', 'trung tâm', 'chung cư']):
                        scores["city"] += int(8 * time_weight)
                        if len(evidence["city"]) < 4:
                            evidence["city"].append(f"Dạo quanh địa danh đô thị '{item.get('poi_name')}'")
                            
                    spending["activities"] += cost
                else:
                    spending["activities"] += cost
                    
                # Điểm mua sắm
                if any(k in poi_name for k in ['chợ', 'mua sắm', 'siêu thị', 'lưu niệm', 'shop', 'trung tâm thương mại']):
                    scores["shopping"] += int(12 * time_weight)
                    spending["shopping"] += cost
                    if len(evidence["shopping"]) < 4:
                        evidence["shopping"].append(f"Ghé thăm khu mua sắm '{item.get('poi_name')}'")

        # Ước lượng chi phí đi lại & lưu trú của từng chuyến đi
        vehicle_lower = trip.vehicle.lower() if trip.vehicle else ""
        transport_cost = 200000.0 * trip.number_of_days
        if 'máy bay' in vehicle_lower:
            transport_cost = 2500000.0
        elif 'ô tô' in vehicle_lower or 'tự lái' in vehicle_lower:
            transport_cost = 1000000.0 + (300000.0 * trip.number_of_days)
        spending["transport"] += transport_cost
        
        lodging_cost = max(200000.0, (trip.budget_limit * 0.3) / max(1, trip.number_of_days)) * trip.number_of_days
        spending["lodging"] += lodging_cost

    # Đảm bảo điểm số nằm trong khoảng [0, 100]
    for key in scores:
        scores[key] = min(100, max(0, scores[key]))
        
    # Tính độ tin cậy
    confidence_score = min(100, total_trips * 20)
    
    return scores, evidence, spending, confidence_score

def _generate_ai_insights(scores, spending):
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_dim, top_score = sorted_dims[0]
    
    insights = []
    
    style_desc = {
        "nature": "hòa mình vào thiên nhiên ('Nature Lover'). Bạn thường ưu tiên các chuyến đi cắm trại dã ngoại, đi bộ leo núi băng rừng hoặc ngắm cảnh sông suối.",
        "culture": "tìm hiểu văn hóa cổ kính ('Culture Explorer'). Bạn thích viếng thăm các di tích lịch sử, đình chùa rêu phong và tìm hiểu đời sống địa phương hoài niệm.",
        "adventure": "khát khao phiêu lưu mạo hiểm ('Adventure Seeker'). Bạn yêu thích cảm giác tự do trên các cung đường phượt xe máy, trải nghiệm vượt thác leo núi và thể thao ngoài trời.",
        "relaxation": "nghỉ dưỡng thư giãn trọn vẹn ('Relaxation Enthusiast'). Bạn thích dành thời gian sưởi nắng, nghe sóng biển rì rào và xua tan mệt mỏi ở các resort yên bình.",
        "city": "khám phá nhịp sống thành thị sôi động ('Urban Wanderer'). Bạn thích dạo bước trên phố đi bộ, tham quan các tòa nhà chọc trời và check-in Landmark hoành tráng.",
        "food": "khám phá bản đồ ẩm thực độc đáo ('Foodie' chính hiệu). Hành trình của bạn luôn xoay quanh việc tìm kiếm và thưởng thức các món ăn ngon như mì Quảng, hải sản, phở và cà phê trứng.",
        "shopping": "mua sắm và sưu tầm quà lưu niệm ('Shopping Collector'). Bạn thích dạo quanh các khu chợ đêm náo nhiệt để lựa chọn những vật phẩm đặc sản làm quà."
    }
    
    primary_text = style_desc.get(top_dim, "khám phá du lịch đa dạng.")
    insights.append(f"🌟 **Đặc trưng du lịch:** Bạn sở hữu phong cách {primary_text}")
    
    highest_spent_cat = max(spending.items(), key=lambda x: x[1])[0] if sum(spending.values()) > 0 else None
    
    spending_desc = {
        "lodging": "Bạn coi trọng sự nghỉ ngơi thoải mái và có xu hướng đầu tư ngân sách lớn vào chất lượng lưu trú khách sạn/resort.",
        "transport": "Chi phí di chuyển bằng máy bay hoặc ô tô tự lái chiếm tỷ lệ vượt trội trong tổng cơ cấu chi tiêu du lịch của bạn.",
        "food": "Bạn sẵn sàng chi tiêu mạnh tay để trải nghiệm các nhà hàng đặc sản và các quán ăn nổi tiếng.",
        "activities": "Bạn ưu tiên chi trả cho các hoạt động vui chơi giải trí, vé tham quan và các tour khám phá trải nghiệm.",
        "shopping": "Mua sắm quà lưu niệm và đặc sản địa phương là mục tiêu chi tiêu chủ đạo của bạn."
    }
    
    if highest_spent_cat:
        insights.append(f"💰 **Hành vi chi tiêu:** {spending_desc[highest_spent_cat]}")
    else:
        insights.append("💰 **Hành vi chi tiêu:** Bạn quản lý tài chính cân bằng giữa các hạng mục dịch vụ du lịch.")
        
    suggestion_desc = {
        "nature": "Gợi ý chuyến đi tiếp theo: Hãy thử làm một chuyến trekking đỉnh Tà Xùa săn mây hoặc cắm trại ở Vườn quốc gia Cúc Phương.",
        "culture": "Gợi ý chuyến đi tiếp theo: Cố đô Huế cổ kính hoặc Phố cổ Hội An sẽ là những điểm đến tuyệt vời để bạn thỏa sức khám phá văn hóa.",
        "adventure": "Gợi ý chuyến đi tiếp theo: Thử sức với chuyến phượt Hà Giang hùng vĩ bằng xe máy hoặc khám phá các hang động hoang sơ tại Quảng Bình.",
        "relaxation": "Gợi ý chuyến đi tiếp theo: Phú Quốc hoặc Nha Trang nắng vàng biển xanh là lựa chọn lý tưởng để bạn sạc lại năng lượng.",
        "city": "Gợi ý chuyến đi tiếp theo: Khám phá sự năng động của Singapore hoặc dạo quanh các công trình kiến trúc lịch sử ở Sài Gòn.",
        "food": "Gợi ý chuyến đi tiếp theo: Làm một chuyến Food Tour Hải Phòng ăn bánh đa cua hoặc càn quét chợ đêm ẩm thực Đà Nẵng.",
        "shopping": "Gợi ý chuyến đi tiếp theo: Các khu chợ nổi miền Tây sầm uất hoặc các trung tâm mua sắm ở Bangkok sẽ làm bạn thích thú."
    }
    
    insights.append(f"💡 **AI Suggestion:** {suggestion_desc.get(top_dim, 'Khám phá thế giới rộng lớn!')}")
    
    return insights

@api_view(['GET'])
@permission_classes([AllowAny])
def get_statistics(request):
    if request.user.is_authenticated:
        trips_qs = Trip.objects.filter(user=request.user)
        photos_qs = Photo.objects.filter(trip__user=request.user)
    else:
        trips_qs = Trip.objects.filter(user__isnull=True)
        photos_qs = Photo.objects.filter(trip__user__isnull=True)
        
    total_trips = trips_qs.count()
    total_photos = photos_qs.count()
    total_days = sum(t.number_of_days for t in trips_qs)
    total_budget = sum(t.budget_limit for t in trips_qs)
    
    unique_locations = set()
    for trip in trips_qs:
        try:
            itinerary = Itinerary.objects.get(trip=trip)
            days = itinerary.days or []
            for day in days:
                schedule = day.get('schedule', [])
                for item in schedule:
                    poi_name = item.get('poi_name')
                    if poi_name:
                        unique_locations.add(poi_name.strip())
        except Itinerary.DoesNotExist:
            pass
                    
    return Response({
        "total_trips": total_trips,
        "total_photos": total_photos,
        "total_locations": len(unique_locations),
        "total_days": total_days,
        "total_budget": total_budget
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_travel_dna(request):
    if request.user.is_authenticated:
        trips_qs = Trip.objects.filter(user=request.user)
    else:
        trips_qs = Trip.objects.filter(user__isnull=True)
        
    scores, evidence, spending, confidence = _analyze_user_travel_dna(trips_qs)
    
    # Caching insights
    user_id_str = str(request.user.id) if request.user.is_authenticated else "guest"
    cache_key = f"travel_dna_insights_{user_id_str}"
    ai_insights = cache.get(cache_key)
    
    if not ai_insights:
        ai_insights = _generate_ai_insights(scores, spending)
        cache.set(cache_key, ai_insights, timeout=1800)  # cache 30 phút
        
    return Response({
        "scores": scores,
        "spending": spending,
        "confidence_score": confidence,
        "ai_insights": ai_insights
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def explain_travel_dna(request):
    if request.user.is_authenticated:
        trips_qs = Trip.objects.filter(user=request.user)
    else:
        trips_qs = Trip.objects.filter(user__isnull=True)
        
    dimension = request.query_params.get("dimension")
    if not dimension:
        return Response({"detail": "Tham số 'dimension' là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)
        
    scores, evidence, spending, confidence = _analyze_user_travel_dna(trips_qs)
    
    labels = {
        "nature": "Thiên nhiên",
        "culture": "Văn hóa",
        "adventure": "Phiêu lưu",
        "relaxation": "Nghỉ dưỡng",
        "city": "Thành phố",
        "food": "Ẩm thực",
        "shopping": "Mua sắm"
    }
    
    dimension_lower = dimension.lower()
    if dimension_lower not in evidence:
        return Response({"detail": f"Không hỗ trợ phân tích đặc trưng '{dimension}'"}, status=status.HTTP_400_BAD_REQUEST)
        
    dim_evidence = evidence.get(dimension_lower, [])
    score = scores.get(dimension_lower, 0)
    
    if len(dim_evidence) == 0:
        explanation = f"Chỉ số {labels[dimension_lower]} của bạn đạt {score}% vì hệ thống chưa ghi nhận hoạt động cụ thể nào thuộc nhóm này trong lịch sử của bạn."
    else:
        explanation = f"Chỉ số {labels[dimension_lower]} của bạn đạt {score}% dựa trên phân tích {len(dim_evidence)} hoạt động/check-in của bạn."
        
    return Response({
        "dimension": dimension_lower,
        "dimension_label": labels.get(dimension_lower, dimension),
        "score": score,
        "explanation": explanation,
        "evidence_list": dim_evidence
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def checklist_list_create(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    if request.method == 'POST':
        item_name = request.data.get('item_name')
        category = request.data.get('category', 'Cá nhân')
        quantity = request.data.get('quantity', 1)
        priority = request.data.get('priority', 'Bắt buộc')
        
        if not item_name:
            return Response({"detail": "Tên vật dụng là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)
            
        item = ChecklistItem.objects.create(
            trip=trip,
            item_name=item_name,
            category=category,
            quantity=quantity,
            priority=priority
        )
        return Response({
            "id": item.id,
            "trip_id": str(trip.id),
            "item_name": item.item_name,
            "category": item.category,
            "quantity": item.quantity,
            "priority": item.priority,
            "is_completed": item.is_completed,
            "created_at": item.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)
        
    elif request.method == 'GET':
        checklist_items = ChecklistItem.objects.filter(trip=trip).order_by('id')
        checklist_list = [{
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "quantity": item.quantity,
            "priority": item.priority,
            "is_completed": item.is_completed,
            "created_at": item.created_at.isoformat()
        } for item in checklist_items]
        return Response(checklist_list)

@api_view(['PATCH', 'DELETE'])
@permission_classes([AllowAny])
def checklist_item_detail(request, trip_id, item_id):
    trip = get_object_or_404(Trip, id=trip_id)
    item = get_object_or_404(ChecklistItem, id=item_id, trip=trip)
    
    if request.method == 'PATCH':
        data = request.data
        if 'is_completed' in data:
            item.is_completed = data['is_completed']
        if 'item_name' in data:
            item.item_name = data['item_name']
        if 'category' in data:
            item.category = data['category']
        if 'quantity' in data:
            item.quantity = data['quantity']
        if 'priority' in data:
            item.priority = data['priority']
        item.save()
        return Response({
            "id": item.id,
            "trip_id": str(trip.id),
            "item_name": item.item_name,
            "category": item.category,
            "quantity": item.quantity,
            "priority": item.priority,
            "is_completed": item.is_completed,
            "created_at": item.created_at.isoformat()
        })
        
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([AllowAny])
def share_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    try:
        itinerary = Itinerary.objects.get(trip=trip)
        days = itinerary.days
    except Itinerary.DoesNotExist:
        days = []
        
    photos = Photo.objects.filter(trip=trip)
    photos_list = [{
        "image_url": p.image_url,
        "caption": p.caption,
        "location_tag": p.location_tag
    } for p in photos]
    
    checklist_items = ChecklistItem.objects.filter(trip=trip).order_by('id')
    checklist_list = [{
        "id": item.id,
        "item_name": item.item_name,
        "category": item.category,
        "quantity": item.quantity,
        "priority": item.priority,
        "is_completed": item.is_completed
    } for item in checklist_items]
    
    return Response({
        "id": str(trip.id),
        "destination": trip.destination,
        "departure_location": trip.departure_location,
        "start_date": trip.start_date.isoformat() if trip.start_date else "",
        "number_of_days": trip.number_of_days,
        "status": trip.status,
        "vehicle": trip.vehicle,
        "trip_type": trip.trip_type,
        "days": days,
        "photos": photos_list,
        "checklist": checklist_list
    })

@api_view(['PATCH'])
@permission_classes([AllowAny])
def share_checklist_item(request, trip_id, item_id):
    trip = get_object_or_404(Trip, id=trip_id)
    item = get_object_or_404(ChecklistItem, id=item_id, trip=trip)
    
    data = request.data
    if 'is_completed' in data:
        item.is_completed = data['is_completed']
        item.save()
        
    return Response({
        "id": item.id,
        "trip_id": str(trip.id),
        "item_name": item.item_name,
        "category": item.category,
        "quantity": item.quantity,
        "priority": item.priority,
        "is_completed": item.is_completed
    })
