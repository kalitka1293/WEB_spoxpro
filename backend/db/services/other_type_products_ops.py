from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import List
from db.models.product import ProductType, Category, SportType, Material  # предполагаем models.py с моделями


# ========================================
# ProductType Operations
# ========================================
class ProductTypeOps:
    @staticmethod
    async def create(session: AsyncSession, name: str) -> ProductType:
        """Добавление нового типа продукта."""
        product_type = ProductType(name=name)
        session.add(product_type)
        await session.commit()
        await session.refresh(product_type)
        return product_type

    @staticmethod
    async def delete(session: AsyncSession, product_type_id: int) -> bool:
        """Удаление типа продукта по ID."""
        result = await session.execute(
            select(ProductType).where(ProductType.id == product_type_id)
        )
        product_type = result.scalar_one_or_none()
        if product_type:
            await session.delete(product_type)
            await session.commit()
            return True
        return False

    @staticmethod
    async def get_all(session: AsyncSession) -> List[ProductType]:
        """Получить все типы продуктов."""
        result = await session.execute(select(ProductType))
        return result.scalars().all()


# ========================================
# Category Operations
# ========================================
class CategoryOps:
    @staticmethod
    async def create(session: AsyncSession, name: str) -> Category:
        """Добавление новой категории."""
        category = Category(name=name)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def delete(session: AsyncSession, category_id: int) -> bool:
        """Удаление категории по ID."""
        result = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        if category:
            await session.delete(category)
            await session.commit()
            return True
        return False

    @staticmethod
    async def get_all(session: AsyncSession) -> List[Category]:
        """Получить все категории."""
        result = await session.execute(select(Category))
        return result.scalars().all()


# ========================================
# SportType Operations
# ========================================
class SportTypeOps:
    @staticmethod
    async def create(session: AsyncSession, name: str) -> SportType:
        """Добавление нового типа спорта."""
        sport_type = SportType(name=name)
        session.add(sport_type)
        await session.commit()
        await session.refresh(sport_type)
        return sport_type

    @staticmethod
    async def delete(session: AsyncSession, sport_type_id: int) -> bool:
        """Удаление типа спорта по ID."""
        result = await session.execute(
            select(SportType).where(SportType.id == sport_type_id)
        )
        sport_type = result.scalar_one_or_none()
        if sport_type:
            await session.delete(sport_type)
            await session.commit()
            return True
        return False

    @staticmethod
    async def get_all(session: AsyncSession) -> List[SportType]:
        """Получить все типы спорта."""
        result = await session.execute(select(SportType))
        return result.scalars().all()


# ========================================
# Material Operations
# ========================================
class MaterialOps:
    @staticmethod
    async def create(session: AsyncSession, name: str) -> Material:
        """Добавление нового материала."""
        material = Material(name=name)
        session.add(material)
        await session.commit()
        await session.refresh(material)
        return material

    @staticmethod
    async def delete(session: AsyncSession, material_id: int) -> bool:
        """Удаление материала по ID."""
        result = await session.execute(
            select(Material).where(Material.id == material_id)
        )
        material = result.scalar_one_or_none()
        if material:
            await session.delete(material)
            await session.commit()
            return True
        return False

    @staticmethod
    async def get_all(session: AsyncSession) -> List[Material]:
        """Получить все материалы."""
        result = await session.execute(select(Material))
        return result.scalars().all()
