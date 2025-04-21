from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages

class SubscriptionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Login va to'lovga oid sahifalar blokirovka qilinmasligi kerak
        exempt_paths = [
            # reverse('login'),
            reverse('admin:index'),
            '/subscription/payment/',
            '/subscription/plans/',
        ]
        
        # Foydalanuvchi tizimga kirgan va branch bilan bog'langan bo'lsa tekshirish
        if (request.user.is_authenticated and 
            request.user.user_role in ['owner', 'admin', 'teacher'] and
            not any(request.path.startswith(path) for path in exempt_paths)):
            
            # Foydalanuvchi qaysi o'quv markazga bog'langanligini tekshirish
            branches = request.user.branch.all()
            
            # Agar birorta ham aktiv obunali o'quv markaz bo'lmasa, to'lov sahifasiga yo'naltirish
            active_branch_exists = any(branch.has_active_subscription() for branch in branches)
            
            if not active_branch_exists and not request.user.is_superuser:
                messages.error(request, "O'quv markaz obunasi faol emas. Iltimos, to'lovni amalga oshiring.")
                return redirect('subscription_payment')
        
        response = self.get_response(request)
        return response