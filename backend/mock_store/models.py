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