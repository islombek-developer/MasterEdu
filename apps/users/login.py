from rest_framework import views,status,generics
from .serializers import Loginserializers,RegistrationSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response



class LoginAPIView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = Loginserializers

    def post(self,request):
        serializers = self.serializer_class(dats = request.data)
        if serializers.is_valid():
            user = serializers.validated_data['user']
            refresh = RefreshToken.for_user(user)

            response_data = {
                'status':'success',
                'token':{
                    'refresh':str(refresh),
                    'access':str(refresh.access_token),
                },

                'user':{
                    'id':user.id,
                    'username':user.username,
                    'password':user.password,
                    'first_name':user.first_name,
                    'last_name':user.last_name,
                    'user_role':user.user_role,

                }
            }
            if user.user_role == 'teacher':
                
                try:
                    teacher=user.teacher
                    response_data['teacher'] = {
                        'id':user.id
                    }
                except:
                    pass

            return Response(response_data,status=status.HTTP_200_OK)
        return Response(response_data,status=status.HTTP_400_BAD_REQUEST)
            

