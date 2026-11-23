# CELL-R Grocery POS & Inventory Management System

A Django web-based Point of Sale (POS), Inventory, Supplier Stock-In, and Customer Credit (*Utang*) Management System designed for **CELL-R Grocery Store**.

## Features
- **Authentication & Role Management:** Login portal with `Administrator` and `Cashier` role permissions.
- **Dashboard:** Real-time KPIs for today's sales, transaction count, low-stock alerts, and outstanding *utang* balances.
- **Point of Sale (POS):** Product search, barcode filtering, discount handling, Cash/E-Wallet/*Utang* checkouts, and automatic stock deduction.
- **Inventory Management:** Full CRUD for products with automatic `In Stock`, `Low Stock`, and `Out of Stock` status tags.
- **Stock-In & Suppliers:** Log incoming supplier shipments and automatically update inventory counts and unit costs.
- **Utang / Credit Ledger:** Track customer credit balances and record partial or full payments.
- **Reports & Settings:** Daily/weekly sales summaries, 7-day trend chart, top-selling items, CSV report export, and SQLite database backup.

## Team Members (CELL-R)
- Esteban, Maria Victoria N.
- Caliguran, Ayane
- Cricoto, Angel Christian
- Tarnate, Athea Glaize
- Riza, Christina
- Cala, Jonnel
- Lagrismos, Don

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url>
   cd CELLR_Grocery_POS_GitHub
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Apply database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Load sample demo accounts & products:**
   ```bash
   python manage.py seed_demo
   ```
   * **Admin Login:** `admin` / `admin123`
   * **Cashier Login:** `cashier1` / `cashier123`

5. **Run the server:**
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.
