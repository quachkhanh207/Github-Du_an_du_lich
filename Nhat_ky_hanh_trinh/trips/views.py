from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from trips.models import Trip, Itinerary, Photo
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

        if not destination or not start_date_str:
            return Response({"detail": "Điểm đến và ngày khởi hành là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except Exception:
            start_date = datetime.now()

        trip = Trip.objects.create(
            destination=destination,
            departure_location=departure_location,
            start_date=start_date,
            number_of_days=number_of_days,
            budget_limit=budget_limit
        )

        itinerary = Itinerary.objects.create(
            trip=trip,
            days=days
        )

        return Response({
            "trip_id": str(trip.id),
            "destination": trip.destination,
            "departure_location": trip.departure_location,
            "start_date": trip.start_date.isoformat(),
            "number_of_days": trip.number_of_days,
            "budget_limit": trip.budget_limit,
            "days": itinerary.days
        }, status=status.HTTP_201_CREATED)

    elif request.method == 'GET':
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
                "photo_count": photo_count,
                "created_at": trip.created_at.isoformat()
            })
        return Response(trips_list)


@api_view(['GET'])
@permission_classes([AllowAny])
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
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
    
    return Response({
        "id": str(trip.id),
        "destination": trip.destination,
        "departure_location": trip.departure_location,
        "start_date": trip.start_date.isoformat() if trip.start_date else "",
        "number_of_days": trip.number_of_days,
        "budget_limit": trip.budget_limit,
        "status": trip.status,
        "days": days,
        "photos": photos_list
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
