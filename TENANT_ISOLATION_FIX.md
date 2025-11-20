# 🔐 Tenant Isolation Fix - Complete Implementation

**Date:** 2025-11-20
**Status:** ✅ FIXED - Tenant isolation fully working

---

## Problem Overview

All stores were showing identical data in analytics, sales, and products because:
1. All tenant-specific data was stored in the `public` schema instead of tenant-specific schemas
2. Django wasn't configured to separate shared vs tenant-specific apps
3. No database router to direct queries to correct schemas

---

## Solution Implemented

### 1. Configure SHARED_APPS and TENANT_APPS

**File:** [config/settings.py](config/settings.py#L22-L65)

```python
# SHARED_APPS: Tables in PUBLIC schema (shared across all tenants)
SHARED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'django_celery_beat',
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',  # Store model is shared
]

# TENANT_APPS: Tables in TENANT schemas (isolated per store)
TENANT_APPS = [
    'products.apps.ProductsConfig',
    'sales.apps.SalesConfig',
    'customers.apps.CustomersConfig',
    'analytics.apps.AnalyticsConfig',
    'tasks.apps.TasksConfig',
]

# INSTALLED_APPS combines both
INSTALLED_APPS = SHARED_APPS + TENANT_APPS
```

**Why this matters:**
- Django now knows which apps should have data isolated per tenant
- Products, Sales, Customers, Analytics, and Tasks are tenant-specific
- User accounts, authentication, and Store metadata are shared

---

### 2. Create Database Router

**File:** [core/routers.py](core/routers.py) (NEW FILE)

```python
class TenantDatabaseRouter:
    """Routes database operations to correct schema"""

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        When migrating:
        - PUBLIC schema → only migrate SHARED_APPS
        - TENANT schema → only migrate TENANT_APPS
        """
        # Get current schema from connection
        with connection.cursor() as cursor:
            cursor.execute("SHOW search_path")
            search_path = cursor.fetchone()[0]
            current_schema = search_path.split(',')[0].strip().strip('"')

        tenant_apps = [app.split('.')[0] for app in settings.TENANT_APPS]
        is_tenant_app = app_label in tenant_apps
        is_public_schema = current_schema == 'public'

        if is_public_schema:
            return not is_tenant_app  # In public: only shared apps
        else:
            return is_tenant_app  # In tenant: only tenant apps
```

**Registered in settings:**
```python
DATABASE_ROUTERS = ['core.routers.TenantDatabaseRouter']
```

---

### 3. Fix Schema Naming Issues

**Problem:** Some schemas had hyphens (`tenant_novyj-testovyj-magazin-2`) but PostgreSQL requires quoted names

**Solution:** Created management command to fix schemas

**File:** [users/management/commands/fix_tenant_schemas.py](users/management/commands/fix_tenant_schemas.py) (NEW FILE)

```bash
# Check what needs fixing
python manage.py fix_tenant_schemas --dry-run

# Apply fixes
python manage.py fix_tenant_schemas
```

**What it does:**
- Renames schemas with hyphens to use underscores
- Creates missing schemas for existing stores
- Example: `tenant_novyj-testovyj-magazin-2` → `tenant_novyj_testovyj_magazin_2`

---

### 4. Create Tables in Tenant Schemas

**Problem:** Schemas existed but were empty (no tables)

**Solution:** Created management command to create tables directly

**File:** [users/management/commands/create_tenant_tables.py](users/management/commands/create_tenant_tables.py) (NEW FILE)

```bash
# Create tables in all tenant schemas
python manage.py create_tenant_tables

# Create for specific store
python manage.py create_tenant_tables --store test_shop
```

**What it does:**
- Uses Django's SchemaEditor to create tables directly from models
- Creates 32 tables per tenant (products, sales, customers, analytics, tasks)
- Copies migration history from public schema

**Result:**
```
📦 admin (tenant_admin): ✅ 32 tables created
📦 Тестовый Магазин (tenant_test_shop): ✅ 32 tables created
📦 Новый Тестовый Магазин 2 (tenant_novyj_testovyj_magazin_2): ✅ 32 tables created
📦 asdawd (tenant_asdawd): ✅ 32 tables created
```

---

## Verification

### Test 1: Data Isolation

```python
# Create product in test_shop
with connection.cursor() as cursor:
    cursor.execute('SET search_path TO tenant_test_shop, public')

product1 = Product.objects.create(name="Product A", ...)
# Result: ID=1 in tenant_test_shop

# Create product in asdawd
with connection.cursor() as cursor:
    cursor.execute('SET search_path TO tenant_asdawd, public')

product2 = Product.objects.create(name="Product B", ...)
# Result: ID=1 in tenant_asdawd (separate from test_shop!)
```

✅ **Result:** Each tenant has independent data with separate ID sequences

### Test 2: Schema Contents

```sql
SELECT schemaname, COUNT(*) as tables
FROM pg_tables
WHERE schemaname LIKE 'tenant_%'
GROUP BY schemaname;
```

```
tenant_admin:                       33 tables
tenant_test_shop:                   33 tables
tenant_asdawd:                      33 tables
tenant_novyj_testovyj_magazin_2:   33 tables
```

✅ **Result:** All tenant schemas have full table sets

---

## Current State

### ✅ What's Working

1. **Tenant Isolation:** Each store has its own PostgreSQL schema
2. **Correct Schema Naming:** All schemas use underscores (PostgreSQL compatible)
3. **Tables Created:** All tenant schemas have complete table sets
4. **New Data Isolated:** New products, sales, etc. go to correct tenant schema
5. **Middleware:** Automatically switches schemas based on X-Tenant-Key header

### ⚠️ Old Data

**Old data in public schema:**
- Products: 5 records
- Sales: ~19 records
- Analytics: 2 records

**Options:**
1. **Keep it:** Old data stays in public, new data in tenant schemas
2. **Migrate it:** Move old data from public to appropriate tenant schemas
3. **Archive it:** Move to archive schema and start fresh

**Current behavior:** Old data is NOT visible through API because middleware switches to tenant schemas. This is expected and correct.

---

## How It Works Now

### API Request Flow

```
1. User sends request with X-Tenant-Key: test_shop_4dfa7a5a
   ↓
2. JWTAuthenticationMiddleware validates token
   ↓
3. TenantByKeyMiddleware:
   - Finds Store with tenant_key = "test_shop_4dfa7a5a"
   - Sets search_path = "tenant_test_shop, public"
   ↓
4. ViewSet queries data:
   - Product.objects.all() → queries tenant_test_shop.products_product
   - Sale.objects.all() → queries tenant_test_shop.sales_sale
   ↓
5. TenantByKeyMiddleware.process_response():
   - Resets search_path to public
   - Adds tenant_key, store_name, store_slug to response
```

### Database Router

```
When Django performs database operations:

READ/WRITE:
- Always uses 'default' database
- Schema determined by search_path (set by middleware)

MIGRATIONS:
- Public schema: Only apply SHARED_APPS migrations
- Tenant schema: Only apply TENANT_APPS migrations
- Router checks current search_path to decide
```

---

## Testing

### Test Tenant Isolation

```bash
# Create product in test_shop
curl -X POST http://localhost:8000/api/products/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", ...}'

# Create product in asdawd
curl -X POST http://localhost:8000/api/products/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_8b43a536" \
  -H "Content-Type: application/json" \
  -d '{"name": "Another Product", ...}'

# List products for each store
curl http://localhost:8000/api/products/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"
# Returns only test_shop products

curl http://localhost:8000/api/products/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_8b43a536"
# Returns only asdawd products
```

### Verify Schema Structure

```bash
python manage.py shell << 'EOF'
from django.db import connection

# List all tenant schemas
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schema_name,
               (SELECT COUNT(*) FROM pg_tables WHERE schemaname = schema_name) as table_count
        FROM information_schema.schemata
        WHERE schema_name LIKE 'tenant_%'
    """)

    for schema, count in cursor.fetchall():
        print(f"{schema}: {count} tables")
EOF
```

---

## Future Considerations

### 1. New Store Creation

When creating a new store, the system now automatically:
1. ✅ Creates PostgreSQL schema (via `SchemaManager.create_schema()`)
2. ✅ Creates tables in schema (via `SchemaManager._create_schema_tables()`)
3. ✅ Creates owner and staff Employee records
4. ⚠️ Cash register must be created manually after schema setup

**Fixed in:** [users/serializers.py](users/serializers.py#L415)

### 2. Migration Strategy for Old Data

If you want to migrate old data from public to tenant schemas:

```python
# Example migration script (not implemented yet)
from django.db import connection
from products.models import Product
from sales.models import Sale

def migrate_old_data():
    # For each store
    for store in Store.objects.all():
        # Switch to tenant schema
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{store.schema_name}", public')

        # Migrate products
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO products_product (...)
                SELECT * FROM public.products_product
                WHERE store_id = {store.id}
            """)
```

### 3. Analytics Regeneration

Old analytics in public schema won't be visible. Options:
1. Regenerate analytics for each tenant
2. Keep historical analytics in public (read-only)
3. Migrate analytics to tenant schemas

---

## Management Commands Reference

### Fix Schemas
```bash
# Check schema issues
python manage.py fix_tenant_schemas --dry-run

# Fix schema naming and create missing schemas
python manage.py fix_tenant_schemas
```

### Create Tables
```bash
# Create tables in all tenant schemas
python manage.py create_tenant_tables

# Create tables for specific store
python manage.py create_tenant_tables --store test_shop

# Drop and recreate tables
python manage.py create_tenant_tables --drop-existing
```

### Migrate Schemas (traditional)
```bash
# Apply migrations to all tenants
python manage.py migrate_tenant_schemas

# Apply to specific store
python manage.py migrate_tenant_schemas --store test_shop

# Skip public schema
python manage.py migrate_tenant_schemas --skip-public
```

---

## Files Modified/Created

### Modified
- [config/settings.py](config/settings.py) - Added SHARED_APPS, TENANT_APPS, DATABASE_ROUTERS
- [users/models.py](users/models.py) - Fixed schema_name generation with underscores

### Created
- [core/routers.py](core/routers.py) - Database router for tenant isolation
- [users/management/commands/fix_tenant_schemas.py](users/management/commands/fix_tenant_schemas.py) - Fix schema issues
- [users/management/commands/create_tenant_tables.py](users/management/commands/create_tenant_tables.py) - Create tables in tenant schemas
- [TENANT_ISOLATION_FIX.md](TENANT_ISOLATION_FIX.md) - This documentation

---

## Summary

✅ **Problem Solved:** All stores showing identical data
✅ **Root Cause Fixed:** Proper tenant schema isolation implemented
✅ **Verification:** Tested and confirmed data isolation working
✅ **Future-Proof:** New stores will automatically have proper isolation

**The multi-tenant architecture is now fully functional!** 🎉

Each store has:
- Its own PostgreSQL schema
- Isolated data (products, sales, customers, analytics, tasks)
- Separate ID sequences
- Complete table sets

New data automatically goes to the correct tenant schema thanks to the middleware and database router.
