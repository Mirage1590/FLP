from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)  # ✅ บันทึกเวลาที่แก้ไขล่าสุด

    def __str__(self):
        return self.user.username  # แสดงชื่อผู้ใช้เป็นชื่อของ Profile

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

class Shoe(models.Model):
    BRAND_CHOICES = [
        ('Nike', 'Nike'),
        ('Adidas', 'Adidas'),
        ('Reebok', 'Reebok'),
        ('Converse', 'Converse'),
        ('Puma', 'Puma'),
        ('Jordan', 'Jordan'),
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
    ]

    id = models.AutoField(primary_key=True)
    brand = models.CharField(max_length=100, choices=BRAND_CHOICES)
    model = models.CharField(max_length=100)
    shoe_type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(max_length=200, blank=True)
    likes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.brand} {self.model} - {self.price} USD ({self.likes} Likes)"

class ShoeLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shoe = models.ForeignKey('Shoe', on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "shoe")  # ป้องกันกด Like ซ้ำ

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart Item {self.shoe.model} for {self.user.username}"

    def total_price(self):
        return self.quantity * self.price


class Coupon(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')]
    )
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def mark_as_used(self):
        """ ฟังก์ชันสำหรับเปลี่ยนสถานะคูปองเป็น 'used' """
        if self.status != 'used':
            self.status = 'used'
            self.save()

    def update_status(self):
        """ อัปเดตสถานะของคูปองให้เป็น Expired ถ้าเลยวันหมดอายุแล้ว """
        if self.expiry_date and self.expiry_date < timezone.now():
            if self.status != "expired":
                self.status = "expired"
                self.save(update_fields=["status"])
        else:
            if self.status != "active":
                self.status = "active"
                self.save(update_fields=["status"])

    def save(self, *args, **kwargs):
        """ ตรวจสอบและอัปเดตสถานะก่อนบันทึก """
        self.update_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.get_status_display()}"


class UserCoupon(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    saved = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def use_coupon(self):
        self.status = 'used'
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.coupon.code} - {'Used' if self.status == 'used' else 'Saved'}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('prompt_pay', 'Prompt Pay'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_address = models.CharField(max_length=255, blank=True, null=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, blank=True, null=True ,default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, blank=True, null=True)

    def calculate_final_price(self):
        total = sum(item.total_price() for item in self.items.all())
        return total

    def apply_coupon(self, coupon):
        """ ใช้คูปองกับออเดอร์ """
        if coupon and coupon.is_active and coupon.expiry_date >= now():
            if coupon.minimum_spend and self.total_price < coupon.minimum_spend:
                return False  # ถ้ายอดสั่งซื้อไม่ถึงขั้นต่ำ

            discount = (
                (coupon.discount_value / 100) * self.total_price if coupon.discount_type == "percent"
                else coupon.discount_value
            )
            discount = min(discount, self.total_price)
            self.discount = discount
            self.final_price = self.total_price - discount
            self.coupon = coupon
            self.save()
            return True
        return False  # คูปองไม่สามารถใช้ได้

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    image = models.URLField(blank=True, null=True)

    def total_price(self):
        return self.price * self.quantity

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)  # ชื่อห้องแชท (ใช้สำหรับกรณีเป็นกลุ่ม)
    users = models.ManyToManyField(User, related_name="chatrooms")  # ผู้ใช้งานที่อยู่ในห้องแชท
    created_at = models.DateTimeField(auto_now_add=True)  # เวลาที่ห้องแชทถูกสร้าง

    def __str__(self):
        return f"Room {self.name or 'Private Chat'} - {', '.join(user.username for user in self.users.all())}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.message} ({self.timestamp})"

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)  # แชทห้องที่ข้อความถูกส่งไป
    sender = models.ForeignKey(User, on_delete=models.CASCADE)  # ผู้ส่งข้อความ
    content = models.TextField()  # เนื้อหาข้อความ
    sent_at = models.DateTimeField(auto_now_add=True)  # เวลาเมื่อข้อความถูกส่ง
    read = models.BooleanField(default=False)  # สถานะการอ่านข้อความ (อ่านแล้วหรือยัง)

    def __str__(self):
        return f"Message from {self.sender.username} in {self.chat_room.name}"

class MessageHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # เชื่อมกับผู้ใช้
    product = models.ForeignKey(Shoe, on_delete=models.CASCADE)  # เชื่อมกับสินค้า
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 ดาว
    comment = models.TextField()  # คอมเมนต์
    created_at = models.DateTimeField(auto_now_add=True)  # เวลาที่รีวิวถูกสร้าง

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.model}"