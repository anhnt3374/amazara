# Import all models here so Alembic can detect them for autogenerate
from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.brand import Brand  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.order_item import OrderItem  # noqa: F401
from app.models.cart_item import CartItem  # noqa: F401
from app.models.address import Address  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.store import Store  # noqa: F401
