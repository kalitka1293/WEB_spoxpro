import React, { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Search, ShoppingBag, User, Menu, X } from 'lucide-react'
import { CLOTHING_CATEGORIES } from '../../types/product'
import { getCategory, getBasketScore, checkUser } from '@/API/RequestAPI'
import { Category } from '@/API/interface'
import { toast } from '@/components/Toast'


const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen)
  const handleSearchClick = () => {
    if (location.pathname !== '/catalog') {
      navigate('/catalog?search=open')
    } else {
      window.dispatchEvent(new Event('toggle-search'))
    }
  }

  const [category, setCategory] = useState<Category | null>(null);
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    const fetchCategory = async () => {
      try {
        const data = await getCategory();
        if (data !== undefined && data !== null) {  // ← ИСПРАВЛЕНИЕ
        setCategory(data);
      }
      } catch (error) {
        toast('Ошибка загрузки категории')
        console.error('Ошибка загрузки категории:', error);
      }
    };

    fetchCategory();
    
    const fetchBasketScore = async () => {
      try {
        const data = await getBasketScore();
        if (data !== undefined && data !== null) {
          setCartCount(data.score);
        }
      } catch (error) {
        console.error('Ошибка загрузки корзины:', error);
      }
    };
    fetchBasketScore();

    const onCartUpdated = () => setCartCount(prev => prev + 1)
    window.addEventListener('cart-updated', onCartUpdated)
    return () => window.removeEventListener('cart-updated', onCartUpdated)
  }, []);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      {/* Основной хедер */}
      <div className="container mx-auto px-4">
        <div className="flex items-center h-[72px] relative">
          {/* Логотип слева */}
          <div className="absolute left-[-190px] top-0 transform relative inline-block">
            {/* Большая видимая картинка (не кликабельна) */}
            <img
              src="/img/name/name.png"
              alt="spoXpro"
              className="pointer-events-none h-24 md:h-32 w-auto"
              loading="eager"
              decoding="async"
              aria-hidden="true"
            />
            {/* Меньшая кликабельная зона, центрированная поверх изображения */}
            <Link
              to="/"
              className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 block h-12 md:h-14 w-28 md:w-40"
              aria-label="Перейти на главную spoXpro"
              title="spoXpro"
            />
          </div>

          {/* Центральная навигация: О нас, Каталог, Контакты */}
          <nav className="hidden lg:flex items-center space-x-10 absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2">
            {/* О нас */}
            <Link to="/about" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
              О нас
            </Link>
            
            {/* Каталог с выпадающим меню категорий */}
            <div className="relative group">
              <Link to="/catalog" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
                Каталог
              </Link>
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-[750px] bg-white/70 backdrop-blur-md rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                <div className="flex">
                  {/* Левая колонка - Категории */}
                  <div className="flex-1 py-3">
                    {/* Заголовок "Категории" */}
                    <div className="px-4 pb-2">
                      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                        Категории
                      </h3>
                    </div>
                    
                    {/* Ссылка "Смотреть все" */}
                    <div className="px-4 pb-2">
                      <Link
                        to="/catalog"
                        className="text-sm text-orange-500 hover:text-orange-600 font-medium"
                      >
                        Смотреть все
                      </Link>
                    </div>
                    
                    {/* Список всех категорий */}

                    {category?.category_main?.map((cat) => (
                        <Link
                          key={cat.id}
                          to={`/catalog?category=${cat.id}`}
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                        >
                          {cat.name}
                        </Link>
                      ))}
                  </div>

                  {/* Средняя колонка - Вид спорта */}
                  <div className="flex-1 py-3">
                    {/* Заголовок "Вид спорта" */}
                    <div className="px-4 pb-2">
                      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                        Вид спорта
                      </h3>
                    </div>
                    
                    {/* Список активностей */}
                    {category?.category_sport?.map((cat) => (
                        <Link
                          key={cat.id}
                          to={`/catalog?activity=${cat.id}`}
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                        >
                          {cat.name}
                        </Link>
                      ))}
                  </div>

                  {/* Правая колонка - Аксессуары */}
                  <div className="flex-1 py-3">
                    {/* Заголовок "Аксессуары" */}
                    <div className="px-4 pb-2">
                      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                        Аксессуары
                      </h3>
                    </div>
                    
                    {/* Список аксессуаров */}

                    {category?.category_accessories?.map((cat) => (
                        <Link
                          key={cat.id}
                          to={`/catalog?accessory=${cat.id}`}
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                        >
                          {cat.name}
                        </Link>
                      ))}
                      
                  </div>
                </div>
              </div>
            </div>

            {/* Контакты */}
            <Link to="/contact" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
              Контакты
            </Link>
          </nav>

          {/* Правая часть (зафиксирована справа) */}
          <div className="flex items-center space-x-4 absolute right-[-170px] top-1/2 -translate-y-1/2">
            {/* Поиск */}
            <button
              onClick={handleSearchClick}
              className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <Search className="h-5 w-5" />
            </button>

            {/* Аккаунт */}
            <button
              onClick={async () => {
                const isAuth = await checkUser()
                navigate(isAuth ? '/profile' : '/auth')
              }}
              className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <User className="h-5 w-5" />
            </button>

            {/* Корзина */}
            <Link
              to="/cart"
              className="relative p-2 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <ShoppingBag className="h-5 w-5" />
              <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {cartCount}
              </span>
            </Link>

            {/* Мобильное меню */}
            <button
              onClick={toggleMenu}
              className="lg:hidden p-2 text-gray-600 hover:text-blue-600 transition-colors"
            >
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

      </div>

      {/* Мобильное меню */}
      {isMenuOpen && (
        <div className="lg:hidden bg-white border-t border-gray-200">
          <div className="px-4 py-2 space-y-1">
            <Link
              to="/catalog"
              className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              Каталог
            </Link>
            
            {/* Категории в мобильном меню */}
            <div className="px-3 py-2">
              <div className="text-gray-500 text-sm font-medium mb-2">Категории:</div>
              {CLOTHING_CATEGORIES.slice(0, 4).map((category) => (
                <Link
                  key={category.id}
                  to={`/catalog?category=${category.id}`}
                  className="block px-2 py-1 text-sm text-gray-600 hover:text-blue-600"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {category.name}
                </Link>
              ))}
            </div>

            <Link
              to="/about"
              className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              О нас
            </Link>
            <Link
              to="/contact"
              className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              Контакты
            </Link>
          </div>
        </div>
      )}
    </header>
  )
}

export default Header
