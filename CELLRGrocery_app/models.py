from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('Administrator', 'Administrator'),
        ('Cashier', 'Cashier'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Cashier')

    def __str__(self):
        return f"{self.username} ({self.role})"


class StoreSettings(models.Model):
    store_name = models.CharField(max_length=150, default='CELL-R Grocery Store')
    address = models.TextField(default='Main Street, Poblacion')
    contact_number = models.CharField(max_length=30, default='0912-345-6789')
    receipt_footer = models.CharField(max_length=255, default='Thank you for shopping at CELL-R Grocery!')

    def __str__(self):
        return self.store_name


class Supplier(models.Model):
    supplier_name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.supplier_name


class Product(models.Model):
    STATUS_CHOICES = [
        ('In Stock', 'In Stock'),
        ('Low Stock', 'Low Stock'),
        ('Out of Stock', 'Out of Stock'),
    ]
    barcode_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    product_name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    stock_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Stock')
    date_added = models.DateTimeField(auto_now_add=True)

    def update_status(self):
        if self.stock_quantity == 0:
            self.status = 'Out of Stock'
        elif self.stock_quantity <= self.low_stock_threshold:
            self.status = 'Low Stock'
        else:
            self.status = 'In Stock'

    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} ({self.stock_quantity})"


class Customer(models.Model):
    customer_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, blank=True)
    current_credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.customer_name


class StockInDelivery(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='deliveries')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_deliveries')
    delivery_date = models.DateTimeField(auto_now_add=True)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Stock-In #{self.id} from {self.supplier.supplier_name}"


class StockInDetail(models.Model):
    stock_in = models.ForeignKey(StockInDelivery, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_received = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.product_name} x{self.quantity_received}"


class SaleTransaction(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('Utang', 'Utang / Credit'),
        ('GCash/E-Wallet', 'GCash / E-Wallet'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    transaction_datetime = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_tendered = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    change_given = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default='Cash')

    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount}"


class SaleDetail(models.Model):
    sale = models.ForeignKey(SaleTransaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.product_name} x{self.quantity}"


class CreditRecord(models.Model):
    STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Partial', 'Partial'),
        ('Paid', 'Paid'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='credit_records')
    sale = models.ForeignKey(SaleTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_records')
    record_date = models.DateTimeField(auto_now_add=True)
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Unpaid')

    def __str__(self):
        return f"{self.customer.customer_name} - {self.status} ({self.remaining_balance})"
