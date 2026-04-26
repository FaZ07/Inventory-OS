from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_manager
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductSearchResult
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.product_service import ProductService
from app.algorithms.forecasting import economic_order_quantity, safety_stock

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_manager),
):
    return await ProductService.create(db, data)


@router.get("", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    supplier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    items, total = await ProductService.list_products(db, page, page_size, category, status, supplier_id)
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/search", response_model=list[ProductSearchResult])
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    fuzzy: bool = Query(False, description="Enable fuzzy (Levenshtein) matching"),
    top_k: int = Query(10, ge=1, le=50),
    _=Depends(get_current_user),
):
    """
    Trie-backed O(k) prefix search.
    Set fuzzy=true for edit-distance tolerance (typo correction).
    """
    results = await ProductService.trie_search(q, fuzzy=fuzzy, top_k=top_k)
    return results


@router.post("/search/rebuild-index", response_model=MessageResponse)
async def rebuild_search_index(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_manager),
):
    count = await ProductService.rebuild_search_index(db)
    return MessageResponse(message=f"Search index rebuilt with {count} products")


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ProductService.get_by_id(db, product_id)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_manager),
):
    return await ProductService.update(db, product_id, data)


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_manager),
):
    await ProductService.delete(db, product_id)
    return MessageResponse(message="Product deactivated")


@router.get("/{product_id}/eoq")
async def get_eoq(
    product_id: int,
    annual_demand: float = Query(..., gt=0),
    ordering_cost: float = Query(50.0, gt=0),
    holding_cost_pct: float = Query(0.25, gt=0, le=1),
    unit_cost: float = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Economic Order Quantity calculation for a product."""
    product = await ProductService.get_by_id(db, product_id)
    result = economic_order_quantity(annual_demand, ordering_cost, holding_cost_pct, unit_cost)
    return {
        "product_id": product_id,
        "sku": product.sku,
        **result.__dict__,
    }


@router.get("/{product_id}/safety-stock")
async def get_safety_stock(
    product_id: int,
    avg_demand_per_day: float = Query(..., gt=0),
    demand_std: float = Query(..., ge=0),
    avg_lead_days: float = Query(..., gt=0),
    lead_std: float = Query(1.0, ge=0),
    service_level: float = Query(0.95),
    _=Depends(get_current_user),
):
    """Safety stock calculation using service-level Z-scores."""
    ss = safety_stock(avg_demand_per_day, demand_std, avg_lead_days, lead_std, service_level)
    return {"product_id": product_id, "safety_stock_units": ss, "service_level_pct": service_level * 100}
