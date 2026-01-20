import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Star } from 'lucide-react'
import { CLOTHING_CATEGORIES } from '../types/product'
import { getProductsByCategory } from '../data/mockProducts'

const CategoryPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>()
  
  const category = CLOTHING_CATEGORIES.find(cat => cat.slug === slug)
  const products = category ? getProductsByCategory(category.id) : []

  if (!category) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Категория не найдена</h1>
          <Link to="/catalog" className="btn-primary">
            Вернуться к каталогу
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Навигация */}
        <div className="flex items-center mb-8">
          <Link
            to="/catalog"
            className="flex items-center text-gray-600 hover:text-blue-600 transition-colors mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Каталог
          </Link>
          <span className="text-gray-400">/</span>
          <span className="text-gray-900 ml-4">{category.name}</span>
        </div>

        {/* Заголовок категории */}
        <div className="mb-12">
          <div className="flex flex-col lg:flex-row items-start lg:items-center gap-8">
            <div className="flex-1">
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                {category.name}
              </h1>
              <p className="text-lg text-gray-600 mb-6">
                {category.description}
              </p>
              <div className="text-sm text-gray-500">
                Найдено товаров: <span className="font-medium text-gray-900">{products.length}</span>
              </div>
            </div>
            
            {/* Превью изображение категории */}
            <div className="w-full lg:w-80 h-80 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl overflow-hidden">
              <img
                src={`/img/clothes/${category.folder}/${category.folder}1.jpg`}
                alt={category.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = '/img/placeholder-category.jpg';
                }}
              />
            </div>
          </div>
        </div>

        {/* Товары категории */}
        {products.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product) => (
              <Link
                key={product.id}
                to={`/product/${product.id}`}
                className="product-card-hover card p-6 bg-white group"
              >
                <div className="relative mb-4">
                  <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                    <img
                      src={product.images[0]}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = '/img/placeholder-product.jpg';
                      }}
                    />
                  </div>
                  {product.discountPercent > 0 && (
                    <div className="absolute top-3 left-3 bg-red-500 text-white px-2 py-1 rounded-full text-sm font-medium">
                      -{product.discountPercent}%
                    </div>
                  )}
                  {product.stockQuantity < 5 && (
                    <div className="absolute top-3 right-3 bg-orange-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                      Осталось {product.stockQuantity}
                    </div>
                  )}
                </div>
                
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
                  {product.name}
                </h3>
                <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                  {product.description}
                </p>
                
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {product.discountPercent > 0 ? (
                      <>
                        <span className="text-xl font-bold text-gray-900">
                          {Math.round(product.price * (1 - product.discountPercent / 100))}₽
                        </span>
                        <span className="text-sm text-gray-500 line-through">
                          {product.price}₽
                        </span>
                      </>
                    ) : (
                      <span className="text-xl font-bold text-gray-900">
                        {product.price}₽
                      </span>
                    )}
                  </div>
                  <div className="flex items-center text-yellow-400">
                    <Star className="h-4 w-4 fill-current" />
                    <span className="text-sm text-gray-600 ml-1">4.8</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 bg-gray-100 rounded-full text-gray-700">
                      {product.size}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 rounded-full text-gray-700">
                      {product.color}
                    </span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    product.stockQuantity > 10 
                      ? 'bg-green-100 text-green-800' 
                      : product.stockQuantity > 0 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {product.stockQuantity > 10 ? 'В наличии' : 
                     product.stockQuantity > 0 ? `Осталось ${product.stockQuantity}` : 
                     'Нет в наличии'}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto flex items-center justify-center">
                <span className="text-4xl">📦</span>
              </div>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              В этой категории пока нет товаров
            </h3>
            <p className="text-gray-600 mb-6">
              Мы работаем над пополнением ассортимента
            </p>
            <Link to="/catalog" className="btn-primary">
              Посмотреть другие категории
            </Link>
          </div>
        )}

        {/* Рекомендации */}
        {products.length > 0 && (
          <div className="mt-16 pt-12 border-t border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
              Вам также может понравиться
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {CLOTHING_CATEGORIES
                .filter(cat => cat.id !== category.id)
                .slice(0, 3)
                .map((relatedCategory) => (
                  <Link
                    key={relatedCategory.id}
                    to={`/category/${relatedCategory.slug}`}
                    className="category-card p-6 hover:scale-105 transition-all duration-300 group"
                  >
                    <div className="aspect-square bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg mb-4 overflow-hidden">
                      <img
                        src={`/img/clothes/${relatedCategory.folder}/${relatedCategory.folder}1.jpg`}
                        alt={relatedCategory.name}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = '/img/placeholder-category.jpg';
                        }}
                      />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                      {relatedCategory.name}
                    </h3>
                    <p className="text-gray-600 text-sm">
                      {relatedCategory.description}
                    </p>
                  </Link>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CategoryPage
