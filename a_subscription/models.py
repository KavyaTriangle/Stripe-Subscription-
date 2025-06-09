from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from django.utils import timezone


class Subscription(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    customer_id = models.CharField(max_length=255)
    subscription_id = models.CharField(max_length=255 , unique=True)
    product_name = models.CharField(max_length=255)
    price = models.IntegerField()
    interval = models.CharField(max_length=255, default="month")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null = True,blank=True)
    cancelled_at = models.DateTimeField(null = True,blank=True)


    @property
    def is_active(self):
        if self.end_date:
            if now() < self.end_date:
                return True
            else:
                return False
            
        else:
            return True
        

    @property
    def tier(self):
        # Normalize the product name to lowercase and replace spaces/underscores
        normalized_name = self.product_name.strip().lower().replace(" ", "_")
        
        tier_mapping = {
            'basic_plan': 1,
            'pro_plan': 2,
            'premium_plan': 3,
        }
        
        return tier_mapping.get(normalized_name, None)

    
    def __str__(self):
        return f"{self.user.username} - {self.product_name} - Active: {self.is_active}"
    
    @property
    def next_billing_date(self):    
        if self.is_active:
            if self.interval == 'month':
                next_billing_date = self.start_date + relativedelta(months=1)
            elif self.interval == 'year':
                next_billing_date = self.start_date + relativedelta(years=1)
            else:
                next_billing_date = self.start_date + relativedelta(days=7)       
        else:
            next_billing_date = None
        return next_billing_date    