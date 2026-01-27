# Pydantic models for API package

from .auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    AuthResponse,
    GuestCookieRequest,
    GuestCookieResponse,
    VerificationCodeRequest,
    VerifyCodeRequest,
    TokenValidationRequest,
    TokenValidationResponse,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    AuthErrorResponse,
    UserProfileResponse,
    UpdateProfileRequest
)

from .store import (
    GenderEnum,
    SizeEnum,
    ProductSizeResponse,
    ProductTypeResponse,
    CategoryResponse,
    SportTypeResponse,
    MaterialResponse,
    ProductResponse,
    ProductSummaryResponse,
    ProductFilterRequest,
    ProductListResponse,
    CreateProductRequest,
    UpdateProductRequest,
    InventoryUpdateRequest,
    StoreStatisticsResponse
)

from .user import (
    AddToCartRequest,
    UpdateCartItemRequest,
    CartItemResponse,
    CartResponse,
    CartValidationResponse,
    CreateOrderRequest,
    OrderItemResponse,
    OrderResponse,
    OrderListResponse,
    UpdateOrderStatusRequest,
    UserStatisticsResponse,
    WishlistItemResponse,
    WishlistResponse,
    AddToWishlistRequest,
    CartMigrationRequest,
    CartMigrationResponse
)

__all__ = [
    # Authentication DTOs
    "UserRegistrationRequest",
    "UserLoginRequest",
    "AuthResponse",
    "GuestCookieRequest",
    "GuestCookieResponse",
    "VerificationCodeRequest",
    "VerifyCodeRequest",
    "TokenValidationRequest",
    "TokenValidationResponse",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "AuthErrorResponse",
    "UserProfileResponse",
    "UpdateProfileRequest",
    
    # Store DTOs
    "GenderEnum",
    "SizeEnum",
    "ProductSizeResponse",
    "ProductTypeResponse",
    "CategoryResponse",
    "SportTypeResponse",
    "MaterialResponse",
    "ProductResponse",
    "ProductSummaryResponse",
    "ProductFilterRequest",
    "ProductListResponse",
    "CreateProductRequest",
    "UpdateProductRequest",
    "InventoryUpdateRequest",
    "StoreStatisticsResponse",
    
    # User and Cart DTOs
    "AddToCartRequest",
    "UpdateCartItemRequest",
    "CartItemResponse",
    "CartResponse",
    "CartValidationResponse",
    "CreateOrderRequest",
    "OrderItemResponse",
    "OrderResponse",
    "OrderListResponse",
    "UpdateOrderStatusRequest",
    "UserStatisticsResponse",
    "WishlistItemResponse",
    "WishlistResponse",
    "AddToWishlistRequest",
    "CartMigrationRequest",
    "CartMigrationResponse"
]