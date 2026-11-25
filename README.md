# CELL-R Grocery POS & Inventory Management System

A web-based Point of Sale (POS), Inventory Catalog, Stock-In Replenishment, *Utang* (Customer Credit) Ledger, and Sales Reporting system built with **Python (Django)** and **SQLite** for **CELL-R Grocery Store (Quiapo, Manila, Philippines)**.

---

## Tech Stack

- **Backend:** Python 3.12+, Django 6.1
- **Database:** SQLite (`db.sqlite3`)
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Vanilla JavaScript

---

## Core Modules & Role-Based Access Control (RBAC)

| Module | Route | Administrator | Cashier |
| :--- | :--- | :---: | :---: |
| **Dashboard** | `/` | Full Access | Read-Only Overview |
| **POS / Create Bill** | `/pos/` | Full Access | Full Access |
| **Inventory Catalog** | `/inventory/` | Full CRUD (Add/Edit/Delete) | View & Search Only |
| **Utang / Customers** | `/utang/` | Full Access | View & Record Payments |
| **Stock-In & Orders** | `/purchase-orders/` | Full Access | Restricted |
| **Sales Reports & CSV** | `/reports/` | Full Access | Restricted |
| **System Settings & Backup** | `/settings/` | Full Access | Restricted |

---

## How to Run This Project on Another Laptop or PC

Follow these steps to clone and run the application locally on a new Windows, macOS, or Linux machine:

### 1. Prerequisites
Ensure the target computer has the following installed:
- **Python 3.12 or higher** *(On Windows, check **"Add Python to PATH"** during installation)*
- **Git** ([git-scm.com](https://git-scm.com/))
- **A modern web browser** (Google Chrome, Microsoft Edge, or Firefox)

### 2. Clone the Repository
Open **Terminal**, **Command Prompt**, or **PowerShell** and run:

```bash
git clone [https://github.com/424000472-byte/CELL-R-Grocery-Application.git](https://github.com/424000472-byte/CELL-R-Grocery-Application.git)
cd CELL-R-Grocery-Application
```

### 3. Create and Activate a Virtual Environment

- **Windows (PowerShell / Command Prompt):**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
  *(If PowerShell blocks script execution, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once, then re-run `venv\Scripts\activate`.)*

-
