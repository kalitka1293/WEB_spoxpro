package psql // Пакет для работы с PostgreSQL репозиториями

import (
	"context" // Для контроля выполнения запросов (таймауты, отмены)
	"errors"  // Стандартная библиотека для работы с ошибками

	"github.com/YoungGoofy/shopping/backend/internal/models" // Модели предметной области приложения

	"gorm.io/gorm" // ORM для работы с БД
)

// ProductRepository - структура репозитория для работы с товарами
type ProductRepository struct {
	db *gorm.DB // Подключение к БД через GORM
}

// NewProductRepository - конструктор для инициализации репозитория
func NewProductRepository(db *gorm.DB) *ProductRepository {
	return &ProductRepository{db: db} // Возвращает новый экземпляр репозитория
}

// Create - создает новый товар в БД
func (r *ProductRepository) Create(ctx context.Context, product *models.Product) error {
	// Выполняем INSERT запрос с контекстом
	result := r.db.WithContext(ctx).Create(product)
	if result.Error != nil {
		return result.Error // Возвращаем ошибку при неудаче
	}
	return nil // Успешное выполнение
}

// GetByID - получает товар по его UUID
func (r *ProductRepository) GetByID(ctx context.Context, id string) (*models.Product, error) {
	var product models.Product // Инициализация переменной для результата

	// Выполняем запрос с:
	result := r.db.WithContext(ctx). // - контекстом
						Preload("Category").          // - загрузкой связанной категории
						First(&product, "id = ?", id) // - поиском первой записи по ID

	// Обработка ошибок:
	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		return nil, errors.New("product not found") // Специальная ошибка для "не найдено"
	} else if result.Error != nil {
		return nil, result.Error // Другие ошибки БД
	}
	return &product, nil // Возвращаем найденный товар
}

// Update - обновляет существующий товар
func (r *ProductRepository) Update(ctx context.Context, product *models.Product) error {
	// Сохраняем все поля товара:
	result := r.db.WithContext(ctx).Save(product)
	if result.Error != nil {
		return result.Error // Ошибка операции
	}
	if result.RowsAffected == 0 {
		return errors.New("no records updated") // Нет обновленных записей
	}
	return nil // Успешное обновление
}

// Delete - удаляет товар по ID
func (r *ProductRepository) Delete(ctx context.Context, id string) error {
	// Выполняем DELETE запрос:
	result := r.db.WithContext(ctx).
		Delete(&models.Product{}, "id = ?", id) // Удаление по ID

	if result.Error != nil {
		return result.Error // Ошибка операции
	}
	if result.RowsAffected == 0 {
		return errors.New("product not found") // Товар не найден
	}
	return nil // Успешное удаление
}

// GetByCategory - возвращает товары по категории
func (r *ProductRepository) GetByCategory(ctx context.Context, categoryID uint) ([]models.Product, error) {
	var products []models.Product // Слайс для результатов

	// Ищем товары с указанным categoryID:
	result := r.db.WithContext(ctx).
		Where("category_id = ?", categoryID). // Условие фильтрации
		Find(&products)                       // Запись результатов в слайс

	if result.Error != nil {
		return nil, result.Error // Ошибка запроса
	}
	return products, nil // Возвращаем найденные товары
}

// GetDiscountedProducts - возвращает товары со скидкой
func (r *ProductRepository) GetDiscountedProducts(ctx context.Context) ([]models.Product, error) {
	var products []models.Product // Слайс для результатов

	// Ищем товары с ненулевой скидкой:
	result := r.db.WithContext(ctx).
		Where("discount_percent > 0"). // Условие скидки
		Find(&products)                // Запись результатов

	if result.Error != nil {
		return nil, result.Error // Ошибка запроса
	}
	return products, nil // Возвращаем товары со скидкой
}

// UpdateStock - обновляет количество товара на складе
func (r *ProductRepository) UpdateStock(ctx context.Context, productID string, newStock int) error {
	// Частичное обновление только stock_quantity:
	result := r.db.WithContext(ctx).
		Model(&models.Product{}).          // Указываем модель
		Where("id = ?", productID).        // Условие по ID
		Update("stock_quantity", newStock) // Обновляем только одно поле

	if result.Error != nil {
		return result.Error // Ошибка операции
	}
	if result.RowsAffected == 0 {
		return errors.New("product not found") // Товар не найден
	}
	return nil // Успешное обновление
}
