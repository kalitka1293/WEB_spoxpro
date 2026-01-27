import sys
import os
sys.path.append('.')

print("Testing imports...")

try:
    from db.services.cart_service import CartService as DBCartService
    print("✓ DBCartService import OK")
except Exception as e:
    print(f"✗ DBCartService import ERROR: {e}")

try:
    from db.models.order import CartItem
    print("✓ CartItem import OK")
except Exception as e:
    print(f"✗ CartItem import ERROR: {e}")

try:
    from logs.log_store import get_logger
    print("✓ get_logger import OK")
except Exception as e:
    print(f"✗ get_logger import ERROR: {e}")

print("\nTesting service import...")
try:
    import service.cart_service
    print("✓ Module import OK")
    print(f"Available: {[x for x in dir(service.cart_service) if not x.startswith('_')]}")
except Exception as e:
    print(f"✗ Module import ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting class import...")
try:
    from service.cart_service import CartService as BusinessCartService
    print("✓ BusinessCartService class import OK")
except Exception as e:
    print(f"✗ BusinessCartService class import ERROR: {e}")