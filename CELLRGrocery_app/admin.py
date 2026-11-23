from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, StoreSettings, Supplier, Product, Customer,
    StockInDelivery, StockInDetail,
    SaleTransaction, SaleDetail, CreditRecord
)

admin.site.register(User, UserAdmin)
admin.site.register(StoreSettings)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(StockInDelivery)
admin.site.register(StockInDetail)
admin.site.register(SaleTransaction)
admin.site.register(SaleDetail)
admin.site.register(CreditRecord)
