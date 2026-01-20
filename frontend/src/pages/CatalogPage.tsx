import React, { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Filter, Grid, List, Star } from 'lucide-react'
import { CLOTHING_CATEGORIES } from '../types/product'
import { mockProducts } from '../data/mockProducts'

const CatalogPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [selectedCategories, setSelectedCategories] = useState<number[]>([])
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'discount'>('name')
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 10000])
  const [productTypes, setProductTypes] = useState<string[]>(['clothing', 'accessories'])
  const [selectedActivities, setSelectedActivities] = useState<string[]>([])

  // Применить фильтр категории из URL при загрузке
  useEffect(() => {
    const categoryParam = searchParams.get('category')
    if (categoryParam) {
      const categoryId = parseInt(categoryParam, 10)
      if (!isNaN(categoryId)) {
        setSelectedCategories([categoryId])
      }
    } else {
      // Если нет параметра category, сбросить фильтр
      setSelectedCategories([])
    }
  }, [searchParams])

  // Скролл вверх при загрузке страницы
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  // Рандомные рекомендации (товары из других категорий или случайные)
  const recommendedProducts = React.useMemo(() => {
    let otherProducts
    
    if (selectedCategories.length > 0) {
      // Если выбраны категории - показывать товары из других категорий
      otherProducts = mockProducts.filter(
        product => !selectedCategories.includes(product.categoryId) && product.discountPercent === 0
      )
    } else {
      // Если категории не выбраны - показывать случайные товары
      otherProducts = mockProducts.filter(product => product.discountPercent === 0)
    }
    
    // Перемешать и взять первые 3
    const shuffled = [...otherProducts].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, 3)
  }, [selectedCategories])

  // Фильтрация товаров
  const filteredProducts = mockProducts.filter(product => {
    if (selectedCategories.length > 0 && !selectedCategories.includes(product.categoryId)) return false
    if (product.price < priceRange[0] || product.price > priceRange[1]) return false
    if (product.discountPercent > 0) return false // Убрать товары со скидкой
    return true
  })

  // Сортировка товаров
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    switch (sortBy) {
      case 'price':
        return a.price - b.price
      case 'discount':
        return b.discountPercent - a.discountPercent
      default:
        return a.name.localeCompare(b.name)
    }
  })


  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Каталог товаров
          </h1>
          <p className="text-lg text-gray-600">
            Найдите идеальную спортивную одежду из нашей коллекции
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Боковая панель фильтров */}
          <div className="lg:w-1/4">
            <div className="card p-6 bg-white">
              <div className="flex items-center mb-6">
                <Filter className="h-5 w-5 text-gray-600 mr-2" />
                <h2 className="text-lg font-semibold text-gray-900">Фильтры</h2>
              </div>

              {/* Тип товара */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">Тип товара</h3>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={productTypes.includes('clothing')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setProductTypes([...productTypes, 'clothing'])
                        } else {
                          setProductTypes(productTypes.filter(t => t !== 'clothing'))
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Одежда</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={productTypes.includes('accessories')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setProductTypes([...productTypes, 'accessories'])
                        } else {
                          setProductTypes(productTypes.filter(t => t !== 'accessories'))
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Аксессуары</span>
                  </label>
                </div>
              </div>

              {/* Виды активности */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">Вид спорта</h3>
                <div className="space-y-2">
                  {['fitness', 'yoga', 'running', 'walking', 'stretching', 'dancing'].map((activity) => {
                    const activityNames: {[key: string]: string} = {
                      fitness: 'Fitness',
                      yoga: 'Yoga',
                      running: 'Бег',
                      walking: 'Прогулка',
                      stretching: 'Растяжка',
                      dancing: 'Танцы'
                    }
                    return (
                      <label key={activity} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedActivities.includes(activity)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedActivities([...selectedActivities, activity])
                            } else {
                              setSelectedActivities(selectedActivities.filter(a => a !== activity))
                            }
                          }}
                          className="mr-2"
                        />
                        <span className="text-sm text-gray-700">{activityNames[activity]}</span>
                      </label>
                    )
                  })}
                </div>
              </div>

              {/* Категории */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">Категории</h3>
                <div className="space-y-2">
                  {CLOTHING_CATEGORIES.map((category) => (
                    <label key={category.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedCategories.includes(category.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCategories([...selectedCategories, category.id])
                          } else {
                            setSelectedCategories(selectedCategories.filter(id => id !== category.id))
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">{category.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Ценовой диапазон */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">Цена</h3>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <input
                      type="number"
                      placeholder="От"
                      value={priceRange[0]}
                      onChange={(e) => setPriceRange([Number(e.target.value), priceRange[1]])}
                      className="input text-sm w-full"
                    />
                    <span className="text-gray-500">—</span>
                    <input
                      type="number"
                      placeholder="До"
                      value={priceRange[1]}
                      onChange={(e) => setPriceRange([priceRange[0], Number(e.target.value)])}
                      className="input text-sm w-full"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setPriceRange([0, 3000])}
                      className="text-xs px-3 py-1 border border-gray-300 rounded-full hover:bg-gray-100"
                    >
                      До 3000₽
                    </button>
                    <button
                      onClick={() => setPriceRange([3000, 5000])}
                      className="text-xs px-3 py-1 border border-gray-300 rounded-full hover:bg-gray-100"
                    >
                      3000-5000₽
                    </button>
                    <button
                      onClick={() => setPriceRange([5000, 10000])}
                      className="text-xs px-3 py-1 border border-gray-300 rounded-full hover:bg-gray-100"
                    >
                      От 5000₽
                    </button>
                  </div>
                </div>
              </div>

              {/* Сброс фильтров */}
              <button
                onClick={() => {
                  setSelectedCategories([])
                  setPriceRange([0, 10000])
                  setProductTypes(['clothing', 'accessories'])
                  setSelectedActivities([])
                }}
                className="w-full btn-outline text-sm py-2"
              >
                Сбросить фильтры
              </button>
            </div>
          </div>

          {/* Основной контент */}
          <div className="lg:w-3/4">
            {/* Панель управления */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
              <div className="text-sm text-gray-600">
                Найдено товаров: <span className="font-medium">{sortedProducts.length}</span>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Сортировка */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'name' | 'price' | 'discount')}
                  className="input text-sm min-w-[150px]"
                >
                  <option value="name">По названию</option>
                  <option value="price">По цене</option>
                </select>

                {/* Переключатель вида */}
                <div className="flex space-x-2">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded-lg border ${viewMode === 'grid' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-100'}`}
                    title="Сетка"
                  >
                    <Grid className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded-lg border ${viewMode === 'list' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-100'}`}
                    title="Список"
                  >
                    <List className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Сетка товаров */}
            <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
              {sortedProducts.map((product) => (
                <Link
                  key={product.id}
                  to={`/product/${product.id}`}
                  className={`product-card-hover card bg-white group ${viewMode === 'list' ? 'flex p-6' : 'p-6'}`}
                >
                  <div className={`relative ${viewMode === 'list' ? 'w-80 h-80 flex-shrink-0 mr-8' : 'mb-4'}`}>
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
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className={`font-semibold text-gray-900 group-hover:text-blue-600 transition-colors ${viewMode === 'list' ? 'text-2xl' : 'text-lg'}`}>
                        {product.name}
                      </h3>
                      <div className="flex items-center text-yellow-400 ml-2">
                        <Star className={`fill-current ${viewMode === 'list' ? 'h-5 w-5' : 'h-4 w-4'}`} />
                        <span className={`text-gray-600 ml-1 ${viewMode === 'list' ? 'text-base' : 'text-sm'}`}>4.8</span>
                      </div>
                    </div>
                    
                    <p className={`text-gray-600 mb-4 ${viewMode === 'list' ? 'text-base' : 'text-sm line-clamp-2'}`}>
                      {product.description}
                    </p>
                    
                    <div className="flex items-center justify-between">
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
                      
                      <div className="flex items-center space-x-2 text-sm text-gray-500">
                        <span className="px-2 py-1 bg-gray-100 rounded-full">
                          {product.size}
                        </span>
                        <span className="px-2 py-1 bg-gray-100 rounded-full">
                          {product.color}
                        </span>
                      </div>
                    </div>
                    
                    {viewMode === 'list' && (
                      <div className="mt-4">
                        <span className="text-sm text-gray-600">
                          Категория: <span className="font-medium">{product.category.name}</span>
                        </span>
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>


            {/* Рекомендации "Вам также может понравиться" */}
            {recommendedProducts.length > 0 && sortedProducts.length > 0 && (
              <div className="mt-16">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-8 text-center">
                  Вам также может понравиться
                </h2>
                <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                  {recommendedProducts.map((product) => (
                    <Link
                      key={product.id}
                      to={`/product/${product.id}`}
                      className="product-card-hover card bg-white group p-6"
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
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                            {product.name}
                          </h3>
                          <div className="flex items-center text-yellow-400 ml-2">
                            <Star className="h-4 w-4 fill-current" />
                            <span className="text-sm text-gray-600 ml-1">4.8</span>
                          </div>
                        </div>
                        
                        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                          {product.description}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-xl font-bold text-gray-900">
                            {product.price}₽
                          </span>
                          
                          <div className="flex items-center space-x-2 text-sm text-gray-500">
                            <span className="px-2 py-1 bg-gray-100 rounded-full">
                              {product.size}
                            </span>
                            <span className="px-2 py-1 bg-gray-100 rounded-full">
                              {product.color}
                            </span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Пустое состояние */}
            {sortedProducts.length === 0 && (
              <div className="text-center py-12">
                <div className="text-gray-400 mb-4">
                  <Filter className="h-16 w-16 mx-auto" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Товары не найдены
                </h3>
                <p className="text-gray-600 mb-6">
                  Попробуйте изменить параметры фильтрации
                </p>
                <button
                  onClick={() => {
                    setSelectedCategories([])
                    setPriceRange([0, 10000])
                    setProductTypes(['clothing', 'accessories'])
                    setSelectedActivities([])
                  }}
                  className="btn-primary"
                >
                  Сбросить фильтры
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CatalogPage
