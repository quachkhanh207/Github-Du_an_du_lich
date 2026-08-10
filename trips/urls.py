from django.urls import path
from trips import views

urlpatterns = [
    path('trips/', views.trips_list_create, name='trips_list_create'),
    path('trips/<uuid:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trips/<uuid:trip_id>/photos/', views.add_photo, name='add_photo'),
    path('trips/statistics/', views.get_statistics, name='get_statistics'),
    path('trips/<uuid:trip_id>/checklist/', views.checklist_list_create, name='checklist_list_create'),
    path('trips/<uuid:trip_id>/checklist/<int:item_id>/', views.checklist_item_detail, name='checklist_item_detail'),
    path('trips/<uuid:trip_id>/share/', views.share_trip, name='share_trip'),
    path('trips/<uuid:trip_id>/share/checklist/<int:item_id>/', views.share_checklist_item, name='share_checklist_item'),
]
