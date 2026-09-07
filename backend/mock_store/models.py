from django.db import models

# Create your models here.
class MockProduct(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.external_id} - {self.title}"

class MockVariant(models.Model):
    product = models.ForeignKey(
        MockProduct,
        on_delete=models.CASCADE,
        related_name="variants",
    
    )
    external_id=models.CharField(max_length=100, unique=True)
    sku = models.CharField(max_length=100)
    price=models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")

    def __str__(self):
        return f"{self.external_id} - {self.sku}"

class MockInventory(models.Model):
    variant = models.OneToOneField(
        MockVariant,
        on_delete=models.CASCADE,
        related_name="inventory",
    )
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.variant} - {self.quantity}"

class MockOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        FULFILLED = "fulfilled", "Fulfilled"

    external_id = models.CharField(max_length=100, unique=True)
    customer_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.external_id} - {self.customer_name}"