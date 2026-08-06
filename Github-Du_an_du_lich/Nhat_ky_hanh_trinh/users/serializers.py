from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ['user']  # Loại trừ quan hệ user để tránh lặp dữ liệu khi nested

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def validate_email(self, value):
        # Kiểm tra trùng email (vì ta dùng email làm username)
        if User.objects.filter(username=value).exists() or User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email này đã được sử dụng đăng ký tài khoản.")
        return value

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        
        # Tạo user với username là email để tương thích hệ thống auth mặc định của Django
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        
        # Tạo UserProfile trống đi kèm cho tài khoản mới
        UserProfile.objects.create(user=user)
        
        return user

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'profile']
