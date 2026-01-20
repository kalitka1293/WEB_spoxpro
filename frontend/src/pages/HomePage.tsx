import React from 'react'
import { Link } from 'react-router-dom'
import { Star, Truck, Shield, Headphones } from 'lucide-react'
import { CLOTHING_CATEGORIES } from '../types/product'
import { mockProducts } from '../data/mockProducts'

const HomePage: React.FC = () => {
  const [currentImage, setCurrentImage] = React.useState(0)
  const [progress, setProgress] = React.useState(0)
  const [isDimming, setIsDimming] = React.useState(false)
  const featuredCategories = CLOTHING_CATEGORIES.slice(0, 6)
  
  // Минимальная цена по категории (с учетом скидки)
  const minPriceByCategory = React.useMemo(() => {
    const map = new Map<string, number>()
    mockProducts.forEach((p) => {
      const price = p.discountPercent > 0
        ? Math.round(p.price * (1 - p.discountPercent / 100))
        : p.price
      const key = String(p.categoryId)
      const current = map.get(key)
      if (current === undefined || price < current) map.set(key, price)
    })
    return map
  }, [])
  
  // Карусель «СПЕЦИАЛЬНО ДЛЯ ВАС»: только категории с товарами
  const categoriesCarousel = React.useMemo(() => {
    return CLOTHING_CATEGORIES.filter(cat => minPriceByCategory.has(String(cat.id)))
  }, [minPriceByCategory])
  
  const SLIDE_DURATION = 6500 // 6.5 секунд на каждый слайд
  const [scrollPosition, setScrollPosition] = React.useState(0)
  const [isHovered, setIsHovered] = React.useState(false)
  const carouselRef = React.useRef<HTMLDivElement>(null)

  // Массив изображений для слайдера
  const heroImages = [
    "/img/clothes/kombez blue/kombez blue1.jpg",
    "/img/clothes/blue hudi/blue hudi1.jpg", 
    "/img/clothes/legensi and rashgard/legensi and rashgard1.jpg",
    "/img/clothes/antracid/antracid1.jpg",
    "/img/clothes/white hudi/white hudi1.jpg"
  ]

  const changeImage = (index: number) => {
    setCurrentImage(index)
    setProgress(0)
  }

  // Автоматическое переключение слайдов
  React.useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 98) {
          setIsDimming(true)
        }
        if (prev >= 100) {
          setCurrentImage((current) => (current + 1) % heroImages.length)
          setTimeout(() => setIsDimming(false), 200)
          return 0
        }
        return prev + (100 / (SLIDE_DURATION / 100))
      })
    }, 100)

    return () => clearInterval(interval)
  }, [])

  // Автоматическая прокрутка карусели с requestAnimationFrame
  React.useEffect(() => {
    let animationFrameId: number
    let lastTime = Date.now()
    
    const animate = () => {
      const currentTime = Date.now()
      const deltaTime = currentTime - lastTime
      
      // Обновляем каждые ~16ms (60 FPS), но только если не наведен курсор
      if (deltaTime >= 16 && !isHovered) {
        setScrollPosition(prev => prev + 2)
        lastTime = currentTime
      }
      
      animationFrameId = requestAnimationFrame(animate)
    }
    
    animationFrameId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationFrameId)
  }, [categoriesCarousel.length, isHovered])

  return (
    <div className="min-h-screen">
      {/* Hero секция с большим фото */}
      <section className="relative h-[calc(100vh-72px)] w-full overflow-hidden bg-gradient-to-br from-blue-600 to-purple-700">
        {/* Отображение текущего изображения */}
        <div className="absolute inset-0">
          <img 
            src={heroImages[currentImage]}
            alt="spoXpro Collection"
            className={`w-full h-full object-cover transition-all duration-500 ${isDimming ? 'brightness-95' : 'brightness-100'}`}
            onError={(e) => {
              console.error('Image failed to load:', heroImages[currentImage]);
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
            }}
            onLoad={() => console.log('Image loaded successfully:', heroImages[currentImage])}
          />
        </div>

        {/* Темный оверлей */}
        <div className="absolute inset-0 bg-black bg-opacity-40"></div>
        
        {/* Контент поверх изображения */}
        <div className="relative z-10 flex items-center justify-center h-full">
          <div className="text-center text-white px-4 max-w-4xl mx-auto">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 animate-fade-in drop-shadow-lg">
              spoXpro
            </h1>
            <p className="text-xl md:text-3xl mb-8 animate-slide-up drop-shadow-md">
              Премиальная спортивная одежда для активного образа жизни
            </p>
            <p className="text-lg md:text-xl mb-12 max-w-2xl mx-auto opacity-90 drop-shadow-md">
              Откройте для себя коллекцию качественной спортивной одежды: 
              от стильных худи до функциональных комбинезонов
            </p>
          </div>
        </div>
        
        {/* Кнопка отдельно внизу */}
        <div className="absolute bottom-32 left-1/2 transform -translate-x-1/2 z-20">
          <Link
            to="/catalog"
            className="bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 text-lg px-8 py-4 rounded-full font-semibold hover:scale-105 transition-all duration-300 shadow-lg inline-block border border-white/30"
          >
            К ПОКУПКАМ
          </Link>
        </div>

        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex gap-4 z-20 w-[32rem]">
          {heroImages.map((_, index) => (
            <button
              key={index}
              onClick={() => changeImage(index)}
              className="flex-1 h-0.5 bg-white bg-opacity-20 rounded-full overflow-hidden cursor-pointer"
              aria-label={`Показать изображение ${index + 1}`}
            >
              <div
                className="h-full bg-white transition-all duration-100 ease-linear"
                style={{
                  width: index === currentImage ? `${progress}%` : index < currentImage ? '100%' : '0%'
                }}
              />
            </button>
          ))}
        </div>
      </section>

      {/* Категории */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Наши категории
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Выберите идеальную одежду для ваших тренировок и активного отдыха
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {featuredCategories.map((category) => (
              <Link
                key={category.id}
                to={`/catalog?category=${category.id}`}
                className="hover:scale-105 transition-all duration-300 group"
              >
                <div className="relative">
                  <div className="aspect-square mb-4 overflow-hidden">
                    <img
                      src={`/img/clothes/${category.folder}/${category.folder}1.jpg`}
                      alt={category.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = '/img/placeholder-product.jpg';
                      }}
                    />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2 transition-colors text-center group-hover:underline underline-offset-2 decoration-current">
                    {category.name}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4 text-center">
                    {category.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
          <div className="text-center mt-10">
            <Link
              to="/catalog"
              className="inline-block bg-gray-300 border-[3px] border-gray-600 hover:bg-sky-400/30 text-black hover:text-black text-lg font-bold px-8 py-3 rounded-lg uppercase tracking-wide transition-colors"
            >
              СМОТРЕТЬ ВСЕ
            </Link>
          </div>
        </div>
      </section>

      {categoriesCarousel.length > 0 && (
        <section className="py-16 bg-gray-50">
          <div className="w-full px-2 md:px-3 lg:px-4">
            <div className="text-center pt-1 mb-4">
              <h2 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-4 transform -translate-y-6">
                СПЕЦИАЛЬНО ДЛЯ ВАС
              </h2>
            </div>
            <div 
              className="relative overflow-hidden py-4"
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
            >
              {/* Карусель с бесконечной прокруткой */}
              <div 
                ref={carouselRef}
                className="flex"
                style={{
                  transform: `translate3d(-${scrollPosition % (carouselRef.current?.scrollWidth || 0) / 2}px, 0, 0)`,
                  backfaceVisibility: 'hidden',
                  perspective: 1000,
                  willChange: 'transform'
                }}
              >
                {/* Дублируем карточки много раз для бесшовной прокрутки */}
                {Array.from({length: 6}, () => categoriesCarousel).flat().map((cat, index) => (
                  <Link
                    key={`${cat.id}-${index}`}
                    to={`/catalog?category=${cat.id}`}
                    className="group flex flex-col items-center flex-shrink-0 w-1/2 md:w-1/4 px-2 transition-transform duration-500 ease-in-out hover:scale-[1.03]"
                  >
                    <div className="relative mb-2 w-full">
                      <div className="aspect-square overflow-hidden">
                        <img
                          src={`/img/clothes/${cat.folder}/${cat.folder}1.jpg`}
                          alt={cat.name}
                          className="w-full h-full object-cover transition-transform duration-300"
                          style={{ transform: 'scale(1)' }}
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = '/img/placeholder-product.jpg'
                          }}
                        />
                      </div>
                    </div>
                    <h3 className="text-base md:text-lg font-medium text-gray-700 transition-all text-center group-hover:underline decoration-sky-400 underline-offset-4 decoration-[2.5px]">
                      {cat.name}
                    </h3>
                    <div className="text-lg md:text-xl font-normal text-gray-700 mt-2 text-center">
                      от {minPriceByCategory.get(String(cat.id))}₽
                    </div>
                  </Link>
                ))}
              </div>
            </div>
            
          </div>
        </section>
      )}

      {/* Преимущества */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Почему выбирают spoXpro
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center group">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-blue-200 transition-colors">
                <Truck className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Быстрая доставка
              </h3>
              <p className="text-gray-600 text-sm">
                Бесплатная доставка по Москве от 3000₽. Доставка в день заказа.
              </p>
            </div>
            
            <div className="text-center group">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-green-200 transition-colors">
                <Shield className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Гарантия качества
              </h3>
              <p className="text-gray-600 text-sm">
                Только оригинальные товары от проверенных производителей.
              </p>
            </div>
            
            <div className="text-center group">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-purple-200 transition-colors">
                <Headphones className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Поддержка 24/7
              </h3>
              <p className="text-gray-600 text-sm">
                Наша команда всегда готова помочь с выбором и ответить на вопросы.
              </p>
            </div>
            
            <div className="text-center group">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-orange-200 transition-colors">
                <Star className="h-8 w-8 text-orange-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Высокие оценки
              </h3>
              <p className="text-gray-600 text-sm">
                Более 10,000 довольных клиентов и средняя оценка 4.8/5.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA секция */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Готовы начать активную жизнь?
          </h2>
          <p className="text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
            Присоединяйтесь к тысячам клиентов, которые уже выбрали качество spoXpro
          </p>
          <Link
            to="/catalog"
            className="btn bg-white text-blue-600 hover:bg-gray-100 text-lg px-8 py-4 rounded-full font-semibold hover:scale-105 transition-transform"
          >
            Начать покупки
          </Link>
        </div>
      </section>
    </div>
  )
}

export default HomePage
