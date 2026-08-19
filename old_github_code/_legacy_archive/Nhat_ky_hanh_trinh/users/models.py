import uuid
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Thông tin cơ bản
    full_name = models.CharField(max_length=255, null=True, blank=True)
    nickname = models.CharField(max_length=100, null=True, blank=True)
    birth_year = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    
    # Sở thích & Cá nhân hóa du lịch (Sử dụng JSONField để linh hoạt lưu mảng)
    travel_style = models.JSONField(default=list, blank=True) # e.g. ["Khám phá", "Văn hóa"]
    default_budget_tier = models.CharField(max_length=50, default="Thoải mái") # Tiết kiệm, Thoải mái, Sang trọng
    frequent_companion = models.CharField(max_length=100, null=True, blank=True) # Đi một mình, Với người yêu...
    food_allergies = models.JSONField(default=list, blank=True) # e.g. ["Hải sản"]
    special_requirements = models.JSONField(default=list, blank=True) # e.g. ["Ăn chay"]
    niche_interests = models.JSONField(default=list, blank=True) # e.g. ["Chụp ảnh film"]
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email} ({self.nickname or self.full_name or 'No Name'})"
