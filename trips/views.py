from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from trips.models import Trip, Itinerary, Photo, ChecklistItem
from datetime import datetime

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
            reminder_enabled=reminder_enabled,
            reminder_settings=reminder_settings
        )

        itinerary = Itinerary.objects.create(
            trip=trip,
            days=days
        )

        # Khởi tạo Checklist mẫu mặc định cốt lõi
        default_items = [
            {"item_name": "CCCD / Hộ chiếu", "category": "Giấy tờ"},
            {"item_name": "Vé tàu xe / Vé máy bay", "category": "Giấy tờ"},
            {"item_name": "Tiền mặt & Thẻ ngân hàng", "category": "Giấy tờ"},
            {"item_name": "Điện thoại & Cáp sạc", "category": "Thiết bị"},
            {"item_name": "Sạc dự phòng", "category": "Thiết bị"},
            {"item_name": "Bàn chải & Kem đánh răng", "category": "Cá nhân"},
            {"item_name": f"Quần áo du lịch ({number_of_days} bộ)", "category": "Cá nhân"}
        ]
        
        # 1. Rule Engine theo Điểm đến & Thời tiết giả định (Destination/Weather Rules)
        dest_lower = destination.lower()
        mountain_keywords = [
            "hà giang", "ha giang", "đà lạt", "da lat", "sa pa", "sapa", 
            "mộc châu", "moc chau", "bắc kạn", "bac kan", "cao bằng", "cao bang", "sơn la", "son la"
        ]
        beach_keywords = [
            "đà nẵng", "da nang", "phú quốc", "phu quoc", "nha trang", 
            "vũng tàu", "vung tau", "mũi né", "mui ne", "hạ long", "ha long", "côn đảo", "con dao"
        ]
        
        if any(x in dest_lower for x in mountain_keywords):
            default_items.append({"item_name": "Áo khoác ấm & Khăn choàng", "category": "Trang phục"})
            default_items.append({"item_name": "Giày leo núi / Giày thể thao bám tốt", "category": "Trang phục"})
            default_items.append({"item_name": "Thuốc bôi chống côn trùng cắn", "category": "Y tế"})
        elif any(x in dest_lower for x in beach_keywords):
            default_items.append({"item_name": "Đồ bơi & Kính râm", "category": "Trang phục"})
            default_items.append({"item_name": "Kem chống nắng bảo vệ da", "category": "Y tế"})
            default_items.append({"item_name": "Dép lê đi biển / Sandal", "category": "Trang phục"})
            
        # 2. Rule Engine theo Hồ sơ Cá nhân hóa của User (User Profile Rules - Khởi tạo từ trước)
        if user:
            try:
                # Lấy profile đã tạo từ app users
                profile = user.profile
                
                # Check Dị ứng thực phẩm -> nhắc mang thuốc dị ứng
                if profile.food_allergies:
                    allergies_str = ", ".join(profile.food_allergies)
                    default_items.append({
                        "item_name": f"Thuốc dị ứng đặc trị (Lưu ý dị ứng: {allergies_str})", 
                        "category": "Y tế"
                    })
                    
                # Check Yêu cầu đặc biệt
                if profile.special_requirements:
                    if "Lối đi xe lăn" in profile.special_requirements:
                        default_items.append({
                            "item_name": "Thiết bị hỗ trợ di chuyển & Hồ sơ khám y khoa", 
                            "category": "Y tế"
                        })
                    if "Ăn chay" in profile.special_requirements:
                        default_items.append({
                            "item_name": "Đồ ăn nhẹ chay đóng hộp (đề phòng)", 
                            "category": "Cá nhân"
                        })
                    
                # Check Sở thích ngách
                if profile.niche_interests:
                    if any(x in profile.niche_interests for x in ["Chụp ảnh film", "Chụp ảnh"]):
                        default_items.append({
                            "item_name": "Máy ảnh & Cuộn film / Sạc pin máy ảnh", 
                            "category": "Thiết bị"
                        })
                    if "Cắm trại" in profile.niche_interests:
                        default_items.append({
                            "item_name": "Đèn pin & Dụng cụ đa năng dã ngoại", 
                            "category": "Thiết bị"
                        })
                        
                # Check Phong cách du lịch
                if profile.travel_style and "Mạo hiểm" in profile.travel_style:
                    default_items.append({
                        "item_name": "Bộ sơ cứu y tế cá nhân (First-aid kit)", 
                        "category": "Y tế"
                    })
            except Exception:
                pass

        checklist_objs = [
            ChecklistItem(trip=trip, item_name=item["item_name"], category=item["category"])
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

@api_view(['GET'])
@permission_classes([AllowAny])
def get_statistics(request):
    total_trips = Trip.objects.count()
    total_photos = Photo.objects.count()
    
    unique_locations = set()
    itineraries = Itinerary.objects.all()
    for itin in itineraries:
        days = itin.days or []
        for day in days:
            schedule = day.get('schedule', [])
            for item in schedule:
                poi_name = item.get('poi_name')
                if poi_name:
                    unique_locations.add(poi_name.strip())
                    
    return Response({
        "total_trips": total_trips,
        "total_photos": total_photos,
        "total_locations": len(unique_locations)
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def checklist_list_create(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    if request.method == 'POST':
        item_name = request.data.get('item_name')
        category = request.data.get('category', 'Cá nhân')
        
        if not item_name:
            return Response({"detail": "Tên vật dụng là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)
            
        item = ChecklistItem.objects.create(
            trip=trip,
            item_name=item_name,
            category=category
        )
        return Response({
            "id": item.id,
            "trip_id": str(trip.id),
            "item_name": item.item_name,
            "category": item.category,
            "is_completed": item.is_completed,
            "created_at": item.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)
        
    elif request.method == 'GET':
        checklist_items = ChecklistItem.objects.filter(trip=trip).order_by('id')
        checklist_list = [{
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
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
        item.save()
        return Response({
            "id": item.id,
            "trip_id": str(trip.id),
            "item_name": item.item_name,
            "category": item.category,
            "is_completed": item.is_completed,
            "created_at": item.created_at.isoformat()
        })
        
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
