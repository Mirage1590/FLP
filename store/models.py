from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)

class Shoe(models.Model):
    BRAND_CHOICES = [
        ('Nike', 'Nike'),
        ('Adidas', 'Adidas'),
        ('Reebok', 'Reebok'),
        ('Converse', 'Converse'),
        ('Puma', 'Puma'),
        ('Jordan', 'Jordan'),
        # เพิ่มแบรนด์อื่น ๆ ตามความต้องการ
    ]

    GENDER_CHOICES = [
        ('Men', 'Men'),
        ('Women', 'Women'),
        ('Unisex', 'Unisex'),
    ]

    TYPE_CHOICES = [
        ('Basketball', 'Basketball'),
        ('Running', 'Running'),
        ('Casual', 'Casual'),
        ('Lifestyle', 'Lifestyle'),
        ('Accessories', 'Accessories'),
    ]

    MATERIAL_CHOICES = [
        ('Leather', 'Leather'),
        ('Canvas', 'Canvas'),
        ('Primeknit', 'Primeknit'),
        ('Mesh', 'Mesh'),
        # เพิ่มวัสดุอื่น ๆ ตามต้องการ
    ]

    # ฟิลด์ต่าง ๆ ในโมเดล
    brand = models.CharField(max_length=100, choices=BRAND_CHOICES)
    model = models.CharField(max_length=100)
    shoe_type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.brand} {self.model} - {self.price} USD"