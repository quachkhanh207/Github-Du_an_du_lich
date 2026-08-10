import uuid
from django.db import models
from django.contrib.auth.models import User

class Trip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    destination = models.CharField(max_length=255)
    departure_location = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateTimeField()
    number_of_days = models.IntegerField()
    budget_limit = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, default="active") # active, completed, archived
    vehicle = models.CharField(max_length=100, default="Xe máy")
    trip_type = models.CharField(max_length=100, default="Phượt")
    reminder_enabled = models.BooleanField(default=False)
    reminder_settings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.destination} ({self.start_date.date() if self.start_date else ''})"

class Itinerary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='itinerary')
    created_at = models.DateTimeField(auto_now_add=True)
    days = models.JSONField(default=list)

    def __str__(self):
        return f"Lịch trình {self.trip.destination}"

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='photos')
    image_url = models.URLField(max_length=1024)
    caption = models.CharField(max_length=200, null=True, blank=True)
    location_tag = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo {self.id} - Trip: {self.trip.destination}"

class ChecklistItem(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='checklist_items')
    item_name = models.CharField(max_length=250)
    category = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    priority = models.CharField(max_length=50, default="Bắt buộc")
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} - {'Done' if self.is_completed else 'Pending'}"

