from fastapi import APIRouter
from app.api.v1 import auth, products, warehouses, suppliers, orders, shipments, analytics

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(warehouses.router)
api_router.include_router(suppliers.router)
api_router.include_router(orders.router)
api_router.include_router(shipments.router)
api_router.include_router(analytics.router)
