import csv
import json
import os
import shutil
from datetime import timedelta
from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count, F
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import (
    User, StoreSettings, Supplier, Product, Customer,
    StockInDelivery, StockInDetail, SaleTransaction, SaleDetail, CreditRecord
)


def admin_required(redirect_to='dashboard'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role != 'Administrator' and not request.user.is_superuser:
                messages.error(request, "Access denied: Administrator privileges required.")
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember_me')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'CELLRGrocery_app/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    todays_sales_qs = SaleTransaction.objects.filter(transaction_datetime__date=today)
    todays_sales = todays_sales_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    todays_count = todays_sales_qs.count()

    low_stock_count = Product.objects.filter(stock_quantity__lte=F('low_stock_threshold')).count()
    outstanding_utang = Customer.objects.aggregate(total=Sum('current_credit_balance'))['total'] or Decimal('0.00')
    recent_transactions = SaleTransaction.objects.select_related('user', 'customer').order_by('-transaction_datetime')[:8]

    context = {
        'todays_sales': todays_sales,
        'todays_count': todays_count,
        'low_stock_count': low_stock_count,
        'outstanding_utang': outstanding_utang,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'CELLRGrocery_app/dashboard.html', context)


@login_required
def pos_view(request):
    products = Product.objects.filter(stock_quantity__gt=0).order_by('product_name')
    categories = Product.objects.values_list('category', flat=True).distinct()
    customers = Customer.objects.order_by('customer_name')
    context = {
        'products': products,
        'categories': categories,
        'customers': customers,
    }
    return render(request, 'CELLRGrocery_app/pos.html', context)


@login_required
def pos_checkout(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        cart_items = data.get('items', [])
        payment_method = data.get('payment_method', 'Cash')
        discount = Decimal(str(data.get('discount', 0) or 0))
        amount_tendered = Decimal(str(data.get('amount_tendered', 0) or 0))
        customer_id = data.get('customer_id')
        new_customer_name = data.get('new_customer_name', '').strip()
        new_customer_contact = data.get('new_customer_contact', '').strip()

        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty.'}, status=400)

        with transaction.atomic():
            customer = None
            if customer_id:
                customer = Customer.objects.get(id=customer_id)
            elif new_customer_name:
                customer = Customer.objects.create(
                    customer_name=new_customer_name,
                    contact_number=new_customer_contact
                )

            if payment_method == 'Utang' and not customer:
                return JsonResponse({'success': False, 'error': 'Please select or enter a customer for Utang / Credit.'}, status=400)

            raw_total = Decimal('0.00')
            validated_items = []

            for item in cart_items:
                product = Product.objects.select_for_update().get(id=item['id'])
                qty = int(item['quantity'])
                if qty <= 0:
                    continue
                if product.stock_quantity < qty:
                    return JsonResponse({
                        'success': False,
                        'error': f"Insufficient stock for {product.product_name} (Available: {product.stock_quantity})."
                    }, status=400)
                subtotal = product.selling_price * qty
                raw_total += subtotal
                validated_items.append((product, qty, product.selling_price, subtotal))

            total_amount = max(Decimal('0.00'), raw_total - discount)

            if payment_method == 'Utang':
                change_given = Decimal('0.00')
            else:
                if amount_tendered < total_amount:
                    return JsonResponse({'success': False, 'error': 'Amount tendered is less than total amount.'}, status=400)
                change_given = amount_tendered - total_amount

            sale = SaleTransaction.objects.create(
                user=request.user,
                customer=customer,
                discount_amount=discount,
                total_amount=total_amount,
                amount_tendered=amount_tendered,
                change_given=change_given,
                payment_method=payment_method
            )

            for product, qty, unit_price, subtotal in validated_items:
                SaleDetail.objects.create(
                    sale=sale,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                product.stock_quantity -= qty
                product.save()

            if payment_method == 'Utang' and customer:
                customer.current_credit_balance += total_amount
                customer.save()
                CreditRecord.objects.create(
                    customer=customer,
                    sale=sale,
                    credit_amount=total_amount,
                    payment_amount=Decimal('0.00'),
                    remaining_balance=customer.current_credit_balance,
                    notes=f"POS Sale #{sale.id}",
                    status='Unpaid'
                )

        return JsonResponse({
            'success': True,
            'sale_id': sale.id,
            'total_amount': str(total_amount),
            'change_given': str(change_given),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def inventory_list_view(request):
    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()

    products = Product.objects.all().order_by('product_name')
    if query:
        products = products.filter(product_name__icontains=query) | products.filter(barcode_code__icontains=query)
    if category_filter:
        products = products.filter(category=category_filter)
    if status_filter:
        products = products.filter(status=status_filter)

    categories = Product.objects.values_list('category', flat=True).distinct()
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'category_filter': category_filter,
        'status_filter': status_filter,
    }
    return render(request, 'CELLRGrocery_app/inventory_list.html', context)


@login_required
@admin_required('inventory_list')
def product_add(request):
    if request.method == 'POST':
        Product.objects.create(
            barcode_code=request.POST.get('barcode_code') or None,
            product_name=request.POST.get('product_name'),
            category=request.POST.get('category'),
            description=request.POST.get('description', ''),
            cost_price=Decimal(request.POST.get('cost_price') or '0'),
            selling_price=Decimal(request.POST.get('selling_price') or '0'),
            low_stock_threshold=int(request.POST.get('low_stock_threshold') or 10),
            stock_quantity=int(request.POST.get('stock_quantity') or 0),
        )
        messages.success(request, "Product added to inventory.")
    return redirect('inventory_list')


@login_required
@admin_required('inventory_list')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.barcode_code = request.POST.get('barcode_code') or None
        product.product_name = request.POST.get('product_name')
        product.category = request.POST.get('category')
        product.description = request.POST.get('description', '')
        product.cost_price = Decimal(request.POST.get('cost_price') or '0')
        product.selling_price = Decimal(request.POST.get('selling_price') or '0')
        product.low_stock_threshold = int(request.POST.get('low_stock_threshold') or 10)
        product.stock_quantity = int(request.POST.get('stock_quantity') or 0)
        product.save()
        messages.success(request, f"Updated {product.product_name}.")
    return redirect('inventory_list')


@login_required
@admin_required('inventory_list')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.product_name
        product.delete()
        messages.warning(request, f"Deleted {name}.")
    return redirect('inventory_list')


@login_required
@admin_required('dashboard')
def purchase_orders_view(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        product_id = request.POST.get('product_id')
        qty = int(request.POST.get('quantity_received') or 0)
        unit_cost = Decimal(request.POST.get('unit_cost') or '0')
        notes = request.POST.get('notes', '')

        if supplier_id and product_id and qty > 0:
            with transaction.atomic():
                supplier = get_object_or_404(Supplier, pk=supplier_id)
                product = get_object_or_404(Product, pk=product_id)
                subtotal = unit_cost * qty

                delivery = StockInDelivery.objects.create(
                    supplier=supplier,
                    received_by=request.user,
                    total_value=subtotal,
                    notes=notes
                )
                StockInDetail.objects.create(
                    stock_in=delivery,
                    product=product,
                    quantity_received=qty,
                    unit_cost=unit_cost,
                    subtotal=subtotal
                )
                product.stock_quantity += qty
                product.cost_price = unit_cost
                product.save()

            messages.success(request, f"Stock-In recorded: +{qty} {product.product_name} from {supplier.supplier_name}.")
        else:
            messages.error(request, "Please complete all required Stock-In fields.")
        return redirect('purchase_orders')

    suppliers = Supplier.objects.all().order_by('supplier_name')
    products = Product.objects.all().order_by('product_name')
    deliveries = StockInDelivery.objects.select_related('supplier', 'received_by').prefetch_related('details__product').order_by('-delivery_date')[:15]

    context = {
        'suppliers': suppliers,
        'products': products,
        'deliveries': deliveries,
    }
    return render(request, 'CELLRGrocery_app/purchase_orders.html', context)


@login_required
@admin_required('dashboard')
def supplier_add(request):
    if request.method == 'POST':
        Supplier.objects.create(
            supplier_name=request.POST.get('supplier_name'),
            contact_person=request.POST.get('contact_person', ''),
            contact_number=request.POST.get('contact_number', ''),
            address=request.POST.get('address', ''),
        )
        messages.success(request, "New supplier added.")
    return redirect('purchase_orders')


@login_required
def utang_list_view(request):
    customers = Customer.objects.all().order_by('-current_credit_balance', 'customer_name')
    records = CreditRecord.objects.select_related('customer', 'sale').order_by('-record_date')[:20]
    return render(request, 'CELLRGrocery_app/utang_list.html', {
        'customers': customers,
        'records': records,
    })


@login_required
def utang_pay(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method == 'POST':
        payment = Decimal(request.POST.get('payment_amount') or '0')
        notes = request.POST.get('notes', 'Credit Payment')
        if payment > 0:
            with transaction.atomic():
                customer.current_credit_balance = max(Decimal('0.00'), customer.current_credit_balance - payment)
                customer.save()
                status = 'Paid' if customer.current_credit_balance == 0 else 'Partial'
                CreditRecord.objects.create(
                    customer=customer,
                    credit_amount=Decimal('0.00'),
                    payment_amount=payment,
                    remaining_balance=customer.current_credit_balance,
                    notes=notes,
                    status=status
                )
            messages.success(request, f"Recorded ₱{payment:.2f} payment for {customer.customer_name}.")
    return redirect('utang_list')


@login_required
@admin_required('dashboard')
def reports_view(request):
    today = timezone.localdate()
    week_ago = today - timedelta(days=6)

    daily_sales = SaleTransaction.objects.filter(transaction_datetime__date=today).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    weekly_sales = SaleTransaction.objects.filter(transaction_datetime__date__gte=week_ago).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    top_items = (
        SaleDetail.objects.values('product__product_name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('subtotal'))
        .order_by('-total_qty')[:10]
    )

    chart_labels = []
    chart_values = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_total = SaleTransaction.objects.filter(transaction_datetime__date=d).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        chart_labels.append(d.strftime('%b %d'))
        chart_values.append(float(day_total))

    context = {
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'top_items': top_items,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
    }
    return render(request, 'CELLRGrocery_app/reports.html', context)


@login_required
@admin_required('dashboard')
def export_sales_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cellr_grocery_sales_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Date & Time', 'Cashier', 'Customer', 'Payment Method', 'Discount', 'Total Amount'])

    for sale in SaleTransaction.objects.select_related('user', 'customer').order_by('-transaction_datetime'):
        writer.writerow([
            sale.id,
            sale.transaction_datetime.strftime('%Y-%m-%d %H:%M'),
            sale.user.username if sale.user else 'N/A',
            sale.customer.customer_name if sale.customer else 'Walk-in',
            sale.payment_method,
            sale.discount_amount,
            sale.total_amount,
        ])
    return response


@login_required
@admin_required('dashboard')
def settings_view(request):
    store_settings, _ = StoreSettings.objects.get_or_create(id=1)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_store':
            store_settings.store_name = request.POST.get('store_name', store_settings.store_name)
            store_settings.address = request.POST.get('address', store_settings.address)
            store_settings.contact_number = request.POST.get('contact_number', store_settings.contact_number)
            store_settings.receipt_footer = request.POST.get('receipt_footer', store_settings.receipt_footer)
            store_settings.save()
            messages.success(request, "Store information updated.")
        elif action == 'create_user':
            uname = request.POST.get('username')
            pwd = request.POST.get('password')
            fname = request.POST.get('first_name', '')
            lname = request.POST.get('last_name', '')
            role = request.POST.get('role', 'Cashier')
            if uname and pwd:
                if User.objects.filter(username=uname).exists():
                    messages.error(request, "Username already exists.")
                else:
                    new_u = User.objects.create_user(
                        username=uname, password=pwd,
                        first_name=fname, last_name=lname, role=role
                    )
                    if role == 'Administrator':
                        new_u.is_staff = True
                        new_u.save()
                    messages.success(request, f"User {uname} ({role}) created.")
        return redirect('settings')

    users = User.objects.all().order_by('username')
    return render(request, 'CELLRGrocery_app/settings.html', {
        'store_settings': store_settings,
        'users': users,
    })


@login_required
@admin_required('dashboard')
def backup_database(request):
    db_path = settings.DATABASES['default']['NAME']
    if os.path.exists(db_path):
        return FileResponse(open(db_path, 'rb'), as_attachment=True, filename='cellr_grocery_backup.sqlite3')
    messages.error(request, "Database file not found.")
    return redirect('settings')