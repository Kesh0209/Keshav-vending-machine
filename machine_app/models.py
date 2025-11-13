from django.db import models
from django.utils import timezone
from datetime import timedelta

# Mauritius timezone offset
MAURITIUS_OFFSET = timedelta(hours=4)


# ---------------------------
# PRODUCT MODEL
# ---------------------------
class VendingProduct(models.Model):
    PRODUCT_CATEGORIES = [
        ('snacks', 'Cakes & Snacks'),
        ('drinks', 'Soft Drinks'),
    ]

    product_name = models.CharField(max_length=120)
    cost = models.DecimalField(max_digits=6, decimal_places=2)
    available_quantity = models.PositiveIntegerField(default=30)
    product_image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=PRODUCT_CATEGORIES, default='snacks')
    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Vending Product"
        verbose_name_plural = "Vending Products"
        ordering = ['category', 'product_name']

    def __str__(self):
        return f"{self.product_name} (Rs {self.cost})"

    def reduce_stock(self, quantity):
        """Reduce available stock when a purchase is made"""
        if self.available_quantity >= quantity:
            self.available_quantity -= quantity
            self.save()
            return True
        return False

    def restock_product(self):
        """Refill product to maximum capacity (30)"""
        self.available_quantity = 30
        self.save()


# ---------------------------
# CUSTOMER SESSION MODEL
# ---------------------------
class CustomerSession(models.Model):
    customer_id = models.CharField(max_length=100, verbose_name="Student Name")
    deposited_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    returned_change = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    session_start = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)

    @property
    def timestamp(self):
        return self.session_start

    class Meta:
        verbose_name = "Customer Session"
        verbose_name_plural = "Customer Sessions"

    def __str__(self):
        return f"{self.customer_id} - {self.session_start.strftime('%d/%m/%Y %H:%M')}"

    def calculate_change(self):
        """Calculate change to be returned"""
        self.returned_change = max(self.deposited_amount - self.final_total, 0)
        return self.returned_change


# ---------------------------
# PURCHASE RECORD MODEL
# ---------------------------
class PurchaseRecord(models.Model):
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('refill', 'Refill'),
    ]

    customer_session = models.ForeignKey(
        CustomerSession,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    product = models.ForeignKey(VendingProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='purchase')
    timestamp = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        """Automatically calculate total and set timestamp"""
        if not self.total_price and self.transaction_type == 'purchase':
            self.total_price = self.product.cost * self.quantity

        # Use Mauritius local time
        self.timestamp = timezone.now() + MAURITIUS_OFFSET
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Purchase Record"
        verbose_name_plural = "Purchase Records"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity} ({self.transaction_type})"


# ---------------------------
# MONEY TRANSACTION MODEL
# ---------------------------
class MoneyTransaction(models.Model):
    TYPE_CHOICES = [
        ('inserted', 'Inserted'),
        ('change', 'Change Returned'),
    ]

    session = models.ForeignKey(
        CustomerSession,
        on_delete=models.CASCADE,
        related_name='denominations'
    )
    denomination = models.DecimalField(max_digits=6, decimal_places=2)
    count = models.IntegerField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        """Set timestamp in Mauritius time"""
        self.timestamp = timezone.now() + MAURITIUS_OFFSET
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Money Transaction"
        verbose_name_plural = "Money Transactions"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.type} - Rs {self.denomination} x {self.count}"
