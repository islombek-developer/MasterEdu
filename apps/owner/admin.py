from django.contrib import admin
from .models import Branch,BranchReport,BranchSettings,BranchSubscription,SubscriptionPayment,SubscriptionPlan

admin.site.register(Branch)
admin.site.register(BranchReport)
admin.site.register(BranchSettings)
admin.site.register(BranchSubscription)
admin.site.register(SubscriptionPayment)
admin.site.register(SubscriptionPlan)