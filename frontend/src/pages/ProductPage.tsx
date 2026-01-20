import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Star, ShoppingBag, Heart, Share2, ChevronLeft, ChevronRight } from 'lucide-react'
import { getProductById, mockProducts } from '../data/mockProducts'

const ProductPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const product = id ? getProductById(id) : null
  
  const [selectedImageIndex, setSelectedImageIndex] = useState(0)
  const [selectedSize, setSelectedSize] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [isWishlisted, setIsWishlisted] = useState(false)

  if (!product) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Товар не найден</h1>
          <Link to="/catalog" className="btn-primary">
            Вернуться к каталогу
          </Link>
        </div>
      </div>
    )
  }

  const discountedPrice = product.discountPercent > 0 
    ? Math.round(product.price * (1 - product.discountPercent / 100))
    : product.price

  const relatedProducts = mockProducts
    .filter(p => p.categoryId === product.categoryId && p.id !== product.id)
    .slice(0, 4)

  const availableSizes = ['XS', 'S', 'M', 'L', 'XL']

  const nextImage = () => {
    setSelectedImageIndex((prev) => 
      prev === product.images.length - 1 ? 0 : prev + 1
    )
  }

  const prevImage = () => {
    setSelectedImageIndex((prev) => 
      prev === 0 ? product.images.length - 1 : prev - 1
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Навигация */}
        <div className="flex items-center mb-8 text-sm">
          <Link to="/catalog" className="text-gray-600 hover:text-blue-600 transition-colors">
            Каталог
          </Link>
          <span className="text-gray-400 mx-2">/</span>
          <Link 
            to={`/category/${product.category.slug}`}
            className="text-gray-600 hover:text-blue-600 transition-colors"
          >
            {product.category.name}
          </Link>
          <span className="text-gray-400 mx-2">/</span>
          <span className="text-gray-900">{product.name}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
          {/* Галерея изображений */}
          <div className="space-y-4">
            {/* Основное изображение */}
            <div className="relative aspect-square bg-gray-100 rounded-2xl overflow-hidden">
              <img
                src={product.images[selectedImageIndex]}
                alt={product.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = '/img/placeholder-product.jpg';
                }}
              />
              
              {/* Навигация по изображениям */}
              {product.images.length > 1 && (
                <>
                  <button
                    onClick={prevImage}
                    className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/80 hover:bg-white rounded-full flex items-center justify-center shadow-lg transition-colors"
                  >
                    <ChevronLeft className="h-5 w-5 text-gray-700" />
                  </button>
                  <button
                    onClick={nextImage}
                    className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/80 hover:bg-white rounded-full flex items-center justify-center shadow-lg transition-colors"
                  >
                    <ChevronRight className="h-5 w-5 text-gray-700" />
                  </button>
                </>
              )}

              {/* Индикаторы */}
              {product.images.length > 1 && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-2">
                  {product.images.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setSelectedImageIndex(index)}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        index === selectedImageIndex ? 'bg-white' : 'bg-white/50'
                      }`}
                    />
                  ))}
                </div>
              )}

              {/* Бейджи */}
              <div className="absolute top-4 left-4 space-y-2">
                {product.discountPercent > 0 && (
                  <div className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                    -{product.discountPercent}%
                  </div>
                )}
                {product.stockQuantity < 5 && product.stockQuantity > 0 && (
                  <div className="bg-orange-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                    Осталось {product.stockQuantity}
                  </div>
                )}
              </div>
            </div>

            {/* Миниатюры */}
            {product.images.length > 1 && (
              <div className="grid grid-cols-4 gap-3">
                {product.images.slice(0, 4).map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedImageIndex(index)}
                    className={`aspect-square bg-gray-100 rounded-lg overflow-hidden border-2 transition-colors ${
                      index === selectedImageIndex ? 'border-blue-500' : 'border-transparent hover:border-gray-300'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`${product.name} ${index + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = '/img/placeholder-product.jpg';
                      }}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Информация о товаре */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                {product.name}
              </h1>
              
              {/* Рейтинг */}
              <div className="flex items-center space-x-2 mb-4">
                <div className="flex items-center text-yellow-400">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 fill-current" />
                  ))}
                </div>
                <span className="text-sm text-gray-600">(4.8) • 127 отзывов</span>
              </div>

              {/* Цена */}
              <div className="flex items-center space-x-4 mb-6">
                <span className="text-3xl font-bold text-gray-900">
                  {discountedPrice}₽
                </span>
                {product.discountPercent > 0 && (
                  <span className="text-xl text-gray-500 line-through">
                    {product.price}₽
                  </span>
                )}
                {product.discountPercent > 0 && (
                  <span className="text-lg text-green-600 font-medium">
                    Экономия {product.price - discountedPrice}₽
                  </span>
                )}
              </div>
            </div>

            {/* Описание */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Описание</h3>
              <p className="text-gray-600 leading-relaxed">
                {product.description}
              </p>
            </div>

            {/* Характеристики */}
            <div className="grid grid-cols-2 gap-4 py-4 border-t border-b border-gray-200">
              <div>
                <span className="text-sm text-gray-500">Цвет:</span>
                <span className="text-sm font-medium text-gray-900 ml-2">{product.color}</span>
              </div>
              <div>
                <span className="text-sm text-gray-500">Пол:</span>
                <span className="text-sm font-medium text-gray-900 ml-2">
                  {product.gender === 'M' ? 'Мужской' : product.gender === 'F' ? 'Женский' : 'Унисекс'}
                </span>
              </div>
              <div>
                <span className="text-sm text-gray-500">Бренд:</span>
                <span className="text-sm font-medium text-gray-900 ml-2">spoXpro</span>
              </div>
              <div>
                <span className="text-sm text-gray-500">Артикул:</span>
                <span className="text-sm font-medium text-gray-900 ml-2">{product.id}</span>
              </div>
            </div>

            {/* Выбор размера */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Размер</h3>
              <div className="grid grid-cols-5 gap-3 mb-4">
                {availableSizes.map((size) => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`py-3 px-4 border rounded-lg text-center font-medium transition-colors ${
                      selectedSize === size
                        ? 'border-blue-500 bg-blue-50 text-blue-600'
                        : 'border-gray-300 hover:border-gray-400 text-gray-700'
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
              <Link to="/size-guide" className="text-sm text-blue-600 hover:underline">
                Таблица размеров
              </Link>
            </div>

            {/* Количество */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Количество</h3>
              <div className="flex items-center space-x-4">
                <div className="flex items-center border border-gray-300 rounded-lg">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="px-3 py-2 hover:bg-gray-100 transition-colors"
                  >
                    -
                  </button>
                  <span className="px-4 py-2 font-medium">{quantity}</span>
                  <button
                    onClick={() => setQuantity(Math.min(product.stockQuantity, quantity + 1))}
                    className="px-3 py-2 hover:bg-gray-100 transition-colors"
                  >
                    +
                  </button>
                </div>
                <span className="text-sm text-gray-600">
                  В наличии: {product.stockQuantity} шт.
                </span>
              </div>
            </div>

            {/* Кнопки действий */}
            <div className="space-y-4">
              <button
                disabled={!selectedSize || product.stockQuantity === 0}
                className="w-full btn-primary text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <ShoppingBag className="h-5 w-5 mr-2" />
                {product.stockQuantity === 0 ? 'Нет в наличии' : 'Добавить в корзину'}
              </button>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => setIsWishlisted(!isWishlisted)}
                  className={`flex-1 btn-outline flex items-center justify-center py-3 ${
                    isWishlisted ? 'text-red-600 border-red-600' : ''
                  }`}
                >
                  <Heart className={`h-5 w-5 mr-2 ${isWishlisted ? 'fill-current' : ''}`} />
                  {isWishlisted ? 'В избранном' : 'В избранное'}
                </button>
                
                <button className="btn-outline flex items-center justify-center px-6 py-3">
                  <Share2 className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Доставка */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">Доставка и оплата</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Бесплатная доставка по Москве от 3000₽</li>
                <li>• Доставка в день заказа при заказе до 15:00</li>
                <li>• Оплата картой или наличными при получении</li>
                <li>• Возврат и обмен в течение 14 дней</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Похожие товары */}
        {relatedProducts.length > 0 && (
          <div className="border-t border-gray-200 pt-16">
            <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
              Похожие товары
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {relatedProducts.map((relatedProduct) => (
                <Link
                  key={relatedProduct.id}
                  to={`/product/${relatedProduct.id}`}
                  className="product-card-hover card p-4 bg-white group"
                >
                  <div className="relative mb-4">
                    <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                      <img
                        src={relatedProduct.images[0]}
                        alt={relatedProduct.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = '/img/placeholder-product.jpg';
                        }}
                      />
                    </div>
                    {relatedProduct.discountPercent > 0 && (
                      <div className="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                        -{relatedProduct.discountPercent}%
                      </div>
                    )}
                  </div>
                  
                  <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
                    {relatedProduct.name}
                  </h3>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {relatedProduct.discountPercent > 0 ? (
                        <>
                          <span className="font-bold text-gray-900">
                            {Math.round(relatedProduct.price * (1 - relatedProduct.discountPercent / 100))}₽
                          </span>
                          <span className="text-sm text-gray-500 line-through">
                            {relatedProduct.price}₽
                          </span>
                        </>
                      ) : (
                        <span className="font-bold text-gray-900">
                          {relatedProduct.price}₽
                        </span>
                      )}
                    </div>
                    <div className="flex items-center text-yellow-400">
                      <Star className="h-4 w-4 fill-current" />
                      <span className="text-sm text-gray-600 ml-1">4.8</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProductPage
