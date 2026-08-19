from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile
from users.serializers import UserRegisterSerializer, UserProfileSerializer, UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Tự động tạo token sau khi đăng ký thành công để đăng nhập luôn
        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)
        
        return Response({
            "detail": "Đăng ký tài khoản thành công.",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user_serializer.data
        }, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({"detail": "Vui lòng điền đầy đủ cả email và mật khẩu."}, status=status.HTTP_400_BAD_REQUEST)
        
    # Xác thực bằng email (vì username = email)
    user = authenticate(username=email, password=password)
    
    if user is None:
        return Response({"detail": "Email hoặc mật khẩu không chính xác."}, status=status.HTTP_401_UNAUTHORIZED)
        
    if not user.is_active:
        return Response({"detail": "Tài khoản này đã bị khóa."}, status=status.HTTP_403_FORBIDDEN)
        
    # Tạo Token JWT
    refresh = RefreshToken.for_user(user)
    user_serializer = UserSerializer(user)
    
    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": user_serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    # Đảm bảo Profile đã tồn tại (phòng trường hợp tạo thủ công ngoài luồng đăng ký)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
        
    elif request.method == 'PUT':
        # Cho phép cập nhật từng phần (partial=True)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
