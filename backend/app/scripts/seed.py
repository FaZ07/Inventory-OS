"""
Seed script — generates realistic demo data for InventoryOS.
Run: python -m app.scripts.seed
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models import User, UserRole, Supplier, Warehouse, Product, Order, OrderItem, Shipment, ShipmentEvent
from app.models.product import ProductCategory, ProductStatus
from app.models.supplier import SupplierStatus
from app.models.warehouse import WarehouseStatus
from app.models.order import OrderType, OrderStatus, OrderPriority
from app.models.shipment import ShipmentStatus, ShipmentCarrier


WAREHOUSES = [
    {"name": "East Coast Hub", "code": "ECH", "address": "123 Commerce Dr", "city": "New York", "country": "USA", "latitude": 40.7128, "longitude": -74.0060, "capacity_sqft": 150000, "max_weight_kg": 500000},
    {"name": "West Coast DC", "code": "WCD", "address": "456 Pacific Blvd", "city": "Los Angeles", "country": "USA", "latitude": 34.0522, "longitude": -118.2437, "capacity_sqft": 200000, "max_weight_kg": 700000},
    {"name": "Midwest Central", "code": "MWC", "address": "789 Heartland Ave", "city": "Chicago", "country": "USA", "latitude": 41.8781, "longitude": -87.6298, "capacity_sqft": 180000, "max_weight_kg": 600000},
    {"name": "Southern Hub", "code": "SHB", "address": "321 Gulf Way", "city": "Houston", "country": "USA", "latitude": 29.7604, "longitude": -95.3698, "capacity_sqft": 120000, "max_weight_kg": 400000},
    {"name": "London Europe DC", "code": "LED", "address": "10 Logistics Lane", "city": "London", "country": "UK", "latitude": 51.5074, "longitude": -0.1278, "capacity_sqft": 100000, "max_weight_kg": 350000},
]

SUPPLIERS = [
    {"name": "Apex Electronics Co.", "code": "AEC", "contact_email": "supply@apex.com", "country": "USA", "lead_time_days": 5, "on_time_delivery_rate": 0.97, "quality_score": 0.95, "price_competitiveness": 0.80},
    {"name": "Global Tech Supply", "code": "GTS", "contact_email": "orders@globaltech.com", "country": "Taiwan", "lead_time_days": 14, "on_time_delivery_rate": 0.91, "quality_score": 0.88, "price_competitiveness": 0.92},
    {"name": "FastShip Logistics", "code": "FSL", "contact_email": "b2b@fastship.com", "country": "Germany", "lead_time_days": 7, "on_time_delivery_rate": 0.99, "quality_score": 0.92, "price_competitiveness": 0.70},
    {"name": "Pacific Rim Partners", "code": "PRP", "contact_email": "trade@pacificrim.com", "country": "China", "lead_time_days": 21, "on_time_delivery_rate": 0.82, "quality_score": 0.78, "price_competitiveness": 0.98},
    {"name": "Nordic Quality Goods", "code": "NQG", "contact_email": "sales@nordic.com", "country": "Sweden", "lead_time_days": 10, "on_time_delivery_rate": 0.98, "quality_score": 0.99, "price_competitiveness": 0.65},
]

PRODUCT_TEMPLATES = [
    ("LAPTOP-PRO-16", "ProBook Laptop 16\"", ProductCategory.ELECTRONICS, 899.99, 1299.99, 2.1),
    ("LAPTOP-GAME-001", "Gaming Rig X900", ProductCategory.ELECTRONICS, 1299.99, 1899.99, 3.2),
    ("PHONE-ULTRA-5G", "Quantum Phone 5G", ProductCategory.ELECTRONICS, 499.99, 799.99, 0.21),
    ("TABLET-AIR-11", "AirTab 11 Pro", ProductCategory.ELECTRONICS, 349.99, 549.99, 0.47),
    ("HDPHN-NOISE-PRO", "SoundMax Pro Headphones", ProductCategory.ELECTRONICS, 149.99, 249.99, 0.31),
    ("CHAIR-ERGO-LX", "ErgoChair Luxe", ProductCategory.FURNITURE, 299.99, 499.99, 18.5),
    ("DESK-STAND-48", "StandDesk 48\"", ProductCategory.FURNITURE, 399.99, 649.99, 25.0),
    ("SHIRT-CLASSIC-M", "Classic Oxford Shirt M", ProductCategory.CLOTHING, 24.99, 59.99, 0.35),
    ("JACKET-WINTER-L", "Alpine Winter Jacket L", ProductCategory.CLOTHING, 89.99, 189.99, 1.2),
    ("FOOD-PROTEIN-VAN", "WheyMax Protein Vanilla 2kg", ProductCategory.FOOD, 29.99, 54.99, 2.0),
    ("MACH-DRILL-IND", "IndustrialDrill X500", ProductCategory.MACHINERY, 599.99, 899.99, 12.5),
    ("MED-GLOVE-L-100", "Sterile Gloves L (Box 100)", ProductCategory.MEDICAL, 12.99, 24.99, 0.8),
    ("CHEM-SOLVENT-5L", "Industrial Solvent 5L", ProductCategory.CHEMICALS, 39.99, 69.99, 5.5),
    ("MONITOR-4K-27", "4K ProDisplay 27\"", ProductCategory.ELECTRONICS, 399.99, 649.99, 6.8),
    ("MOUSE-WIRELESS-G", "Precision Wireless Mouse", ProductCategory.ELECTRONICS, 39.99, 79.99, 0.12),
]


async def seed():
    async with AsyncSessionLocal() as db:
        print("Seeding users…")
        users = [
            User(email="admin@inventoryos.com", full_name="System Admin", hashed_password=hash_password("admin123456"), role=UserRole.ADMIN),
            User(email="manager@inventoryos.com", full_name="Warehouse Manager", hashed_password=hash_password("manager123"), role=UserRole.WAREHOUSE_MANAGER),
            User(email="supplier@inventoryos.com", full_name="Supplier Rep", hashed_password=hash_password("supplier123"), role=UserRole.SUPPLIER),
        ]
        db.add_all(users)
        await db.flush()

        print("Seeding suppliers…")
        supplier_objs = []
        for s in SUPPLIERS:
            sup = Supplier(**s, status=SupplierStatus.ACTIVE, total_orders=random.randint(50, 500))
            sup.composite_score = (sup.on_time_delivery_rate * 0.35 + sup.quality_score * 0.30 + sup.price_competitiveness * 0.20 + (1 - sup.lead_time_days / 30) * 0.15)
            db.add(sup)
            supplier_objs.append(sup)
        await db.flush()

        print("Seeding warehouses…")
        wh_objs = []
        for w in WAREHOUSES:
            wh = Warehouse(**w, status=WarehouseStatus.ACTIVE, current_utilization_pct=random.uniform(20, 85))
            db.add(wh)
            wh_objs.append(wh)
        await db.flush()

        print("Seeding products…")
        prod_objs = []
        for sku, name, category, cost, price, weight in PRODUCT_TEMPLATES:
            sup = random.choice(supplier_objs)
            prod = Product(
                sku=sku, name=name, category=category,
                unit_cost=cost, unit_price=price, weight_kg=weight,
                min_stock_level=random.randint(10, 50),
                max_stock_level=random.randint(200, 1000),
                total_quantity=random.randint(20, 800),
                avg_daily_demand=round(random.uniform(1, 50), 2),
                turnover_rate=round(random.uniform(0.5, 8.0), 2),
                supplier_id=sup.id,
                status=ProductStatus.ACTIVE,
            )
            db.add(prod)
            prod_objs.append(prod)
        await db.flush()

        print("Seeding orders…")
        for i in range(30):
            order_type = random.choice([OrderType.PURCHASE, OrderType.SALES])
            status = random.choice(list(OrderStatus))
            priority = random.choice(list(OrderPriority))
            wh = random.choice(wh_objs)
            sup = random.choice(supplier_objs) if order_type == OrderType.PURCHASE else None
            due = datetime.now(timezone.utc) + timedelta(days=random.randint(-5, 30))
            order = Order(
                order_number=f"{'PO' if order_type == OrderType.PURCHASE else 'SO'}-{i+1:04d}",
                order_type=order_type, status=status, priority=priority,
                supplier_id=sup.id if sup else None,
                warehouse_id=wh.id,
                expected_delivery=due,
                created_by=users[0].id,
            )
            db.add(order)
            await db.flush()

            subtotal = 0.0
            for _ in range(random.randint(1, 4)):
                prod = random.choice(prod_objs)
                qty = random.randint(1, 50)
                item = OrderItem(order_id=order.id, product_id=prod.id, quantity=qty, unit_price=prod.unit_price, total_price=qty * prod.unit_price)
                subtotal += item.total_price
                db.add(item)

            order.subtotal = round(subtotal, 2)
            order.tax_amount = round(subtotal * 0.1, 2)
            order.total_amount = round(order.subtotal + order.tax_amount, 2)

        print("Seeding shipments…")
        carriers = list(ShipmentCarrier)
        for i in range(20):
            origin = random.choice(wh_objs)
            dest = random.choice([w for w in wh_objs if w.id != origin.id])
            status = random.choice([ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELIVERED, ShipmentStatus.DELAYED, ShipmentStatus.PENDING])
            eta = datetime.now(timezone.utc) + timedelta(days=random.randint(-3, 10))
            shipment = Shipment(
                tracking_number=f"IOS-{i+1:010d}",
                origin_warehouse_id=origin.id,
                dest_warehouse_id=dest.id,
                carrier=random.choice(carriers),
                status=status,
                weight_kg=round(random.uniform(5, 2000), 1),
                route_distance_km=round(random.uniform(100, 8000), 1),
                estimated_arrival=eta,
                actual_arrival=eta - timedelta(days=1) if status == ShipmentStatus.DELIVERED else None,
            )
            db.add(shipment)
            await db.flush()
            event = ShipmentEvent(shipment_id=shipment.id, status=ShipmentStatus.PENDING, description="Created")
            db.add(event)

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
