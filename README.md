# spoXpro

## Таски
### Бекенд
- [x] ~~Создание регистрации~~
- [x] ~~Создание авторизации~~
- [x] ~~Базовый функционал для создания токена~~
- [x] ~~Подключение Redis и PSQL~~
- [x] ~~Создание абстракций для избежания зависимостей~~
- [x] ~~Создание методов для сохранения и получения токена~~
- [x] ~~Добавить сваггер~~
- [ ] Создание методов для сохранения и получения данных о пользователе
- [ ] Создание возможности получать данные о пользователе без использования БД через токен
- [ ] Разработать схему для баз данных для одежды
- [ ] Создание баз данных для одежды
- [ ] Разработать методы для сохранения и получения данных об одежде
- [ ] Реализовать админку, а если точнее, то дать возможность создавать одежду только админу

## Swagger Documentation

Swagger is integrated into the API to provide interactive documentation. To access the Swagger UI:

1. Generate the Swagger documentation by running:
   ```bash
   cd backend
   ./scripts/generate_swagger.sh
   ```

2. Start the server:
   ```bash
   cd backend
   go run cmd/main.go
   ```

3. Access the Swagger UI in your browser at:
   ```
   http://localhost:8080/swagger/index.html
   ```

The Swagger UI provides interactive documentation of all API endpoints, allowing you to:
- See endpoint details including parameters, request bodies, and responses
- Execute API calls directly from the UI
- View response models and error codes

### References
- [Swagger Documentation](https://github.com/swaggo/swag)
- [Gin Swagger Integration](https://github.com/swaggo/gin-swagger)



-----------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------

product.go -

-----------------------------------------------------------------------------------------------------

Особенности реализации:
- Интеграция с моделями: Используется структура models.Product из вашего пакета моделей
- Поддержка UUID: Работа с ID типа string (UUID)
- Контекст: Все операции принимают context.Context для контроля времени выполнения
- Связи данных:
      - Автоматическая загрузка категории через Preload("Category")
      - Поддержка связей с другими моделями (User, Category)
- Безопасность: Использование подготовленных запросов через GORM

------------------------------------------------------------------------------------------------------

Пример использования:

go
// Создание нового товара
newProduct := &models.Product{
    Name:          "Футболка Classic",
    Description:   "Хлопковая футболка премиум-класса",
    Price:         1999.99,
    StockQuantity: 50,
    Size:          "M",
    Color:         "Белый",
    Gender:        "U",
    DiscountPercent: 10,
    CategoryID:    2,
}

err := productRepo.Create(context.Background(), newProduct)
if err != nil {
    // обработка ошибки
}

// Получение товара
product, err := productRepo.GetByID(context.Background(), "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
if err != nil {
    // обработка ошибки
}
fmt.Printf("Цена со скидкой: %.2f\n", product.DiscountedPrice())

--------------------------------------------------------------------------------------------------------------------

Рекомендации по улучшению:

- Пагинация: Добавить параметры limit/offset в методы получения списков
- Фильтрация: Реализовать гибкую систему фильтров
- Кеширование: Добавить Redis для кеширования частых запросов
- Мягкое удаление: Использовать gorm.DeletedAt для soft-delete
- Валидация: Добавить проверку бизнес-правил перед сохранением

--------------------------------------------------------------------------------------------------------------------

Для использования репозитория нужно инициализировать его в основном коде приложения, передав подключение к БД:


go
db := // инициализация GORM
productRepo := psql.NewProductRepository(db)

--------------------------------------------------------------------------------------------------------------------