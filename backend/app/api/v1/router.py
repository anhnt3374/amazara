from fastapi import APIRouter

from app.api.v1.endpoints.address import router as address_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.cart import router as cart_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.chat_ws import router as chat_ws_router
from app.api.v1.endpoints.favorite import router as favorite_router
from app.api.v1.endpoints.order import router as order_router
from app.api.v1.endpoints.product import router as product_router
from app.api.v1.endpoints.review import router as review_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(address_router)
api_router.include_router(product_router)
api_router.include_router(cart_router)
api_router.include_router(favorite_router)
api_router.include_router(order_router)
api_router.include_router(review_router)
api_router.include_router(chat_router)
api_router.include_router(chat_ws_router)
