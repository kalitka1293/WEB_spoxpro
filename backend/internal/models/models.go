package models

import (
	"time"

	"gorm.io/gorm"
)

type User struct {
	gorm.Model
	ID       string `gorm:"unique;NOT NULL"`
	Name     string `gorm:"type:varchar(20);NOT NULL"`
	LastName string `gorm:"type:varchar(20)"`
	Country  string `gorm:"type:varchar(10);NOT NULL;"`
	Phone    uint64 `gorm:"unique;NOT NULL;type:numeric"`
	Email    string `gorm:"unique;NOT NULL"`
	Address  string `gorm:"NOT NULL;type:text"`
	Password string `gorm:"NOT NULL"`
	IsAdmin  bool   `gorm:"NOT NULL;type:bool"`
}

// ShopSettings - настройки магазина
type ShopSettings struct {
	gorm.Model
	ID           uint   `gorm:"primaryKey"`                            // Уникальный идентификатор настроек
	ShopName     string `gorm:"size:100;default:'spoXpro'"`            // Название магазина (по умолчанию 'spoXpro')
	Currency     string `gorm:"size:3;default:'RUB'"`                  // Валюта магазина (3-буквенный код)
	SupportEmail string `gorm:"size:100;default:'support@spoxpro.ru'"` // Email службы поддержки
}

// Category - категории товаров (иерархическая структура)
type Category struct {
	gorm.Model
	ID       uint       `gorm:"primaryKey"`                   // Уникальный идентификатор категории
	Name     string     `gorm:"size:50;uniqueIndex;not null"` // Название категории (уникальное)
	ParentID *uint      `gorm:"index"`                        // Ссылка на родительскую категорию (для вложенности)
	Parent   *Category  `gorm:"foreignKey:ParentID"`          // Родительская категория
	Children []Category `gorm:"foreignKey:ParentID"`          // Дочерние категории
}

// Collection - коллекции товаров (сезонные подборки)
// TODO: в будущем можно будет реализовать
type Collection struct {
	gorm.Model
	ID              string    `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"` // UUID коллекции
	Name            string    `gorm:"size:100;uniqueIndex;not null"`                  // Название коллекции
	Slug            string    `gorm:"size:120;uniqueIndex;not null"`                  // Человеко-понятный URL
	Description     string    `gorm:"type:text"`                                      // Описание коллекции
	Season          string    `gorm:"size:20"`                                        // Сезон (например: SS24, FW23)
	LaunchDate      time.Time // Дата запуска коллекции
	IsActive        bool      `gorm:"default:true"`              // Флаг активности коллекции
	CoverImage      string    `gorm:"size:255"`                  // Путь к обложке коллекции
	MetaTitle       string    `gorm:"size:70"`                   // SEO заголовок (для метатега)
	MetaDescription string    `gorm:"size:160"`                  // SEO описание (для метатега)
	Keywords        string    `gorm:"size:255"`                  // SEO ключевые слова
	CreatedAt       time.Time `gorm:"default:CURRENT_TIMESTAMP"` // Дата создания записи
}

// Product - товары магазина
type Product struct {
	gorm.Model
	ID              string    `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`                // UUID товара
	Name            string    `gorm:"size:200;index;not null"`                                       // Название товара
	Description     string    `gorm:"type:text;not null"`                                            // Описание товара
	Price           float64   `gorm:"type:numeric(10,2);index;not null;check:price>0"`               // Цена (с проверкой >0)
	StockQuantity   int       `gorm:"not null;check:stock_quantity>=0"`                              // Количество на складе
	Size            string    `gorm:"size:20;not null"`                                              // Размер (S, M, L, 42, 44 и т.д.)
	Color           string    `gorm:"size:30;not null"`                                              // Цвет товара
	Gender          string    `gorm:"size:1;check:gender IN ('M','F','U')"`                          // Пол (M - муж, F - жен, U - унисекс)
	DiscountPercent int       `gorm:"default:0;check:discount_percent>=0 AND discount_percent<=100"` // Процент скидки (0-100)
	Brand           string    `gorm:"size:100;default:'spoXpro';not null"`                           // Бренд (фиксированное значение 'spoXpro')
	CreatedAt       time.Time `gorm:"default:CURRENT_TIMESTAMP"`                                     // Дата создания товара

	// Связи
	CategoryID uint     `gorm:"not null"`                                            // ID категории
	Category   Category `gorm:"foreignKey:CategoryID;constraint:OnDelete:RESTRICT;"` // Связь с категорией
	// CollectionID *uuid.UUID  // ID коллекции (может быть null)
	// Collection   *Collection `gorm:"foreignKey:CollectionID;constraint:OnDelete:SET NULL;"` // Связь с коллекцией
}

// Order - заказы пользователей
type Order struct {
	gorm.Model
	ID              string    `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`                                          // UUID заказа
	UserID          string    `gorm:"not null"`                                                                                // ID пользователя
	User            User      `gorm:"foreignKey:UserID;constraint:OnDelete:CASCADE;"`                                          // Связь с пользователем
	OrderDate       time.Time `gorm:"default:CURRENT_TIMESTAMP"`                                                               // Дата заказа
	Status          string    `gorm:"size:20;index;not null;check:status IN ('processing','shipped','delivered','cancelled')"` // Статус заказа
	TotalAmount     float64   `gorm:"type:numeric(10,2);not null;check:total_amount>0"`                                        // Итоговая сумма
	ShippingAddress string    `gorm:"type:text;not null"`                                                                      // Адрес доставки
}

// OrderItem - позиции в заказе
type OrderItem struct {
	gorm.Model
	ID              string  `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`        // UUID позиции заказа
	OrderID         string  `gorm:"not null"`                                              // ID заказа
	Order           Order   `gorm:"foreignKey:OrderID;constraint:OnDelete:CASCADE;"`       // Связь с заказом
	ProductID       string  `gorm:"not null"`                                              // ID товара
	Product         Product `gorm:"foreignKey:ProductID;constraint:OnDelete:RESTRICT;"`    // Связь с товаром
	Quantity        int     `gorm:"not null;check:quantity>0"`                             // Количество товара
	PriceAtPurchase float64 `gorm:"type:numeric(10,2);not null;check:price_at_purchase>0"` // Цена на момент покупки
}

// Review - отзывы о товарах
type Review struct {
	gorm.Model
	ID        string    `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`    // UUID отзыва
	ProductID string    `gorm:"not null"`                                          // ID товара
	Product   Product   `gorm:"foreignKey:ProductID;constraint:OnDelete:CASCADE;"` // Связь с товаром
	UserID    string    `gorm:"not null"`                                          // ID пользователя
	User      User      `gorm:"foreignKey:UserID;constraint:OnDelete:CASCADE;"`    // Связь с пользователем
	Rating    int       `gorm:"not null;check:rating>=1 AND rating<=5"`            // Оценка (1-5 звезд)
	Comment   string    // Текст отзыва
	CreatedAt time.Time `gorm:"default:CURRENT_TIMESTAMP"` // Дата создания отзыва

	// Уникальный индекс: 1 отзыв на товар от пользователя
	// gorm.UniqueIndex("idx_product_user", "product_id", "user_id")
}

// DiscountedPrice - расчет цены со скидкой
func (p *Product) DiscountedPrice() float64 {
	return p.Price * (1 - float64(p.DiscountPercent)/100)
}

// IsAvailable - проверка доступности коллекции
func (c *Collection) IsAvailable() bool {
	// Коллекция доступна если активна и дата запуска прошла
	return c.IsActive && c.LaunchDate.Before(time.Now())
}
