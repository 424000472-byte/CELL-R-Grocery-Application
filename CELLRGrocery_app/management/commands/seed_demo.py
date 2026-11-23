from decimal import Decimal
from django.core.management.base import BaseCommand
from CELLRGrocery_app.models import User, StoreSettings, Supplier, Product, Customer


class Command(BaseCommand):
    help = 'Seeds initial demo accounts, products, suppliers, and customers for CELL-R Grocery POS'

    def handle(self, *args, **kwargs):
        StoreSettings.objects.get_or_create(id=1)

        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@cellrgrocery.local',
                password='admin123',
                first_name='Maria Victoria',
                last_name='Esteban',
                role='Administrator'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user (admin / admin123)'))

        if not User.objects.filter(username='cashier1').exists():
            User.objects.create_user(
                username='cashier1',
                password='cashier123',
                first_name='Ayane',
                last_name='Caliguran',
                role='Cashier'
            )
            self.stdout.write(self.style.SUCCESS('Created cashier user (cashier1 / cashier123)'))

        s1, _ = Supplier.objects.get_or_create(
            supplier_name='Metro Grocery Wholesale Corp.',
            defaults={'contact_person': 'Don Lagrismos', 'contact_number': '0917-111-2233', 'address': 'Warehouse District'}
        )
        s2, _ = Supplier.objects.get_or_create(
            supplier_name='FreshFarm Beverage & Dairy',
            defaults={'contact_person': 'Jonnel Cala', 'contact_number': '0918-444-5566', 'address': 'North Highway'}
        )

        sample_products = [
            ('4800016644801', 'Lucky Me! Pancit Canton Original', 'Noodles & Instant', Decimal('11.50'), Decimal('15.00'), 15, 48),
            ('4800888111222', 'Bear Brand Fortified Powdered Milk 300g', 'Dairy & Beverages', Decimal('105.00'), Decimal('120.00'), 10, 22),
            ('4800194123456', 'Argentina Corned Beef 175g', 'Canned Goods', Decimal('34.00'), Decimal('42.00'), 12, 8),
            ('4800049720111', 'Coca-Cola 1.5L Bottle', 'Dairy & Beverages', Decimal('58.00'), Decimal('70.00'), 10, 18),
            ('4800361390812', 'Nescafe Classic Twin Pack', 'Coffee & Sugar', Decimal('12.00'), Decimal('16.00'), 20, 60),
            ('4806502350019', 'Jasmine White Rice 5kg', 'Rice & Grains', Decimal('235.00'), Decimal('270.00'), 5, 4),
            ('4800024567890', 'Safeguard Pure White Soap 130g', 'Personal Care', Decimal('38.00'), Decimal('48.00'), 10, 25),
            ('4807770270017', 'Datu Puti Soy Sauce 1L', 'Condiments', Decimal('41.00'), Decimal('52.00'), 10, 14),
        ]

        for barcode, name, cat, cost, sell, thresh, qty in sample_products:
            Product.objects.get_or_create(
                barcode_code=barcode,
                defaults={
                    'product_name': name,
                    'category': cat,
                    'cost_price': cost,
                    'selling_price': sell,
                    'low_stock_threshold': thresh,
                    'stock_quantity': qty,
                }
            )

        Customer.objects.get_or_create(
            customer_name='Athea Glaize Tarnate',
            defaults={'contact_number': '0920-888-9900', 'current_credit_balance': Decimal('150.00')}
        )
        Customer.objects.get_or_create(
            customer_name='Christina Riza',
            defaults={'contact_number': '0921-777-6655', 'current_credit_balance': Decimal('0.00')}
        )

        self.stdout.write(self.style.SUCCESS('CELL-R Grocery demo data seeded successfully!'))
