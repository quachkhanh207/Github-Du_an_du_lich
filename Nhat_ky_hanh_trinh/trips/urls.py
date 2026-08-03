from django.urls import path
from trips import views

urlpatterns = [
    path('trips/', views.trips_list_create, name='trips_list_create'),
    path('trips/<uuid:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trips/<uuid:trip_id>/photos/', views.add_photo, name='add_photo'),
    path('trips/statistics/', views.get_statistics, name='get_statistics'),
]
