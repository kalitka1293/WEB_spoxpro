import json
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin import EnumField, TextAreaField, StringField, IntegerField
from starlette_admin.actions import link_row_action
from starlette_admin.auth import AuthProvider
from starlette_admin.exceptions import LoginFailed

from config.settings import get_settings
from db.database import engine, SessionLocal
from db.categories import Category
from db.product_colors import ProductColor
from db.product_sizes import ProductSize
from db.products import Product
from db.users import User
from db.orders import Order
from db.reviews import Review
from db.pickup import Pickup

_settings = get_settings()


class AdminAuth(AuthProvider):
    async def login(self, username: str, password: str, remember_me: bool, request: Request, response: Response) -> Response:
        if username == _settings.admin_username and password == _settings.admin_password:
            request.session.update({"admin_logged_in": True})
            return response
        raise LoginFailed("Неверный логин или пароль")

    async def is_authenticated(self, request: Request) -> bool:
        return request.session.get("admin_logged_in", False)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response


class CategoryView(ModelView):
    label = "Категории"
    icon = "fa fa-tags"
    fields = [
        "id",
        StringField("name", label="Название"),
        EnumField("tags", label="Тег",
                  choices=[("main", "Все категории"), ("sport", "Спорт"), ("accessories", "Аксессуары")]),
    ]


class ColorView(ModelView):
    label = "Цвета"
    icon = "fa fa-palette"


class SizeView(ModelView):
    label = "Размеры"
    icon = "fa fa-ruler"


def get_colors(request: Request):
    db = SessionLocal()
    try:
        items = db.query(ProductColor).all()
        return [(c.name, c.name) for c in items] if items else []
    finally:
        db.close()


def get_sizes(request: Request):
    db = SessionLocal()
    try:
        items = db.query(ProductSize).all()
        return [(s.name, s.name) for s in items] if items else []
    finally:
        db.close()


def get_category_ids(request: Request):
    db = SessionLocal()
    try:
        items = db.query(Category).all()
        return [(str(c.id), c.name) for c in items] if items else []
    finally:
        db.close()


class ProductView(ModelView):
    label = "Товары"
    icon = "fa fa-box"
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    row_actions = ["view", "edit", "manage_images", "delete"]
    fields = [
        "id",
        StringField("name", label="Название"),
        TextAreaField("description", label="Описание"),
        IntegerField("price", label="Цена"),
        EnumField("gender", label="Пол", choices=[("M", "Мужской"), ("F", "Женский"), ("U", "Унисекс")]),
        IntegerField("discount", label="Скидка"),
        EnumField("color", label="Цвет", choices_loader=get_colors),
        EnumField("sizes", label="Размеры", multiple=True, choices_loader=get_sizes),
        EnumField("category_id", label="Категория", choices_loader=get_category_ids, coerce=int),
        IntegerField("stock_quantity", label="Количество на складе"),
        "images",
        "created_at",
    ]

    async def before_create(self, request, data, obj):
        if isinstance(data.get("sizes"), list):
            obj.sizes = json.dumps(data["sizes"])

    async def before_edit(self, request, data, obj):
        if isinstance(data.get("sizes"), list):
            obj.sizes = json.dumps(data["sizes"])

    async def serialize_field_value(self, value, field, action, request):
        if field.name == "sizes" and isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = []
        if field.name == "category_id" and value is not None:
            value = str(value)
        return await super().serialize_field_value(value, field, action, request)

    @link_row_action(
        name="manage_images",
        text="Изображения",
        icon_class="fas fa-images",
    )
    def manage_images_action(self, request: Request, pk) -> str:
        return f"/image-manager/{pk}"


class UserView(ModelView):
    label = "Пользователи"
    icon = "fa fa-users"

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False


class OrderView(ModelView):
    label = "Заказы"
    icon = "fa fa-shopping-cart"

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False


def get_product_choices(request: Request):
    db = SessionLocal()
    try:
        items = db.query(Product).all()
        return [(str(p.id), f"{p.name} (ID: {p.id})") for p in items] if items else []
    finally:
        db.close()


class ReviewView(ModelView):
    label = "Отзывы"
    icon = "fa fa-comments"
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    fields = [
        "id",
        EnumField("product_id", label="Товар", choices_loader=get_product_choices, coerce=int),
        IntegerField("user_id", label="ID пользователя"),
        StringField("username", label="Имя"),
        EnumField("rating", label="Оценка", choices=[("1","1"),("2","2"),("3","3"),("4","4"),("5","5")], coerce=int),
        TextAreaField("text", label="Текст отзыва"),
        "created_at",
    ]

    async def serialize_field_value(self, value, field, action, request):
        if field.name == "product_id" and value is not None:
            value = str(value)
        if field.name == "rating" and value is not None:
            value = str(value)
        return await super().serialize_field_value(value, field, action, request)


class PickupView(ModelView):
    label = "Самовывоз"
    icon = "fa fa-map-marker-alt"
    fields = [
        "id",
        StringField("address", label="Адрес"),
    ]


def setup_admin(app):
    from admin.image_manager import router_images
    admin = Admin(
        engine,
        title="spoXpro Admin",
        auth_provider=AdminAuth(login_path="/login", logout_path="/logout"),
    )
    admin.add_view(CategoryView(Category))
    admin.add_view(ColorView(ProductColor))
    admin.add_view(SizeView(ProductSize))
    admin.add_view(ProductView(Product))
    admin.add_view(UserView(User))
    admin.add_view(OrderView(Order))
    admin.add_view(ReviewView(Review))
    admin.add_view(PickupView(Pickup))
    admin.mount_to(app)
    app.include_router(router_images)
