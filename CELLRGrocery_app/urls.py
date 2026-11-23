from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pos/', views.pos_view, name='pos'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),
    path('inventory/', views.inventory_list_view, name='inventory_list'),
    path('inventory/add/', views.product_add, name='product_add'),
    path('inventory/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('inventory/delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('purchase-orders/', views.purchase_orders_view, name='purchase_orders'),
    path('purchase-orders/supplier/add/', views.supplier_add, name='supplier_add'),
    path('utang/', views.utang_list_view, name='utang_list'),
    path('utang/pay/<int:customer_id>/', views.utang_pay, name='utang_pay'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/export-csv/', views.export_sales_csv, name='export_sales_csv'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/backup-db/', views.backup_database, name='backup_database'),
]
