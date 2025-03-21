from rest_framework import views,status,generics
from .serializers import Loginserializers,RegistrationSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response



from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = Loginserializers

    def post(self, request):
        serializer = self.serializer_class(data=request.data)  # Corrected keyword argument
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            response_data = {
                'status': 'success',
                'token': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': {
                    'id': user.id,
                    'phone_number': user.phone_number,
                    'password': user.password,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_role': user.user_role,
                }
            }

            if user.user_role == 'teacher':
                try:
                    teacher = user.teacher
                    response_data['teacher'] = {
                        'id': user.id
                    }
                except:
                    pass

            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Return serializer errors if invalid

class Registerview(generics.CreateAPIView):
    serializer_class=RegistrationSerializer
    permission_classes =[AllowAny]

    def create(self,request,*args,**kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({"message": "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi", "user": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
