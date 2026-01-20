import React from 'react'
import { Link } from 'react-router-dom'
import { Phone, Mail, MapPin, Instagram, Facebook, Youtube } from 'lucide-react'

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Логотип и описание */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <img 
                src="/img/logo/logo.png" 
                alt="spoXpro Logo" 
                className="h-8 w-auto filter brightness-0 invert"
              />
              <img 
                src="/img/name/name.png" 
                alt="spoXpro" 
                className="h-6 w-auto filter brightness-0 invert"
              />
            </div>
            <p className="text-gray-300 text-sm leading-relaxed">
              spoXpro - премиальная спортивная одежда для активного образа жизни. 
              Качество, стиль и комфорт в каждой вещи.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Instagram className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Facebook className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Youtube className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Каталог */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Каталог</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/catalog" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Вся одежда
                </Link>
              </li>
              <li>
                <Link to="/catalog?category=2" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Худи
                </Link>
              </li>
              <li>
                <Link to="/catalog?category=3" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Легинсы и топы
                </Link>
              </li>
              <li>
                <Link to="/catalog?category=4" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Комбинезоны
                </Link>
              </li>
              <li>
                <Link to="/catalog?category=7" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Шорты
                </Link>
              </li>
            </ul>
          </div>

          {/* Информация */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Информация</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/about" className="text-gray-300 hover:text-white transition-colors text-sm">
                  О компании
                </Link>
              </li>
              <li>
                <Link to="/delivery" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Доставка и оплата
                </Link>
              </li>
              <li>
                <Link to="/returns" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Возврат и обмен
                </Link>
              </li>
              <li>
                <Link to="/size-guide" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Таблица размеров
                </Link>
              </li>
              <li>
                <Link to="/care" className="text-gray-300 hover:text-white transition-colors text-sm">
                  Уход за изделиями
                </Link>
              </li>
            </ul>
          </div>

          {/* Контакты */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Контакты</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <Phone className="h-4 w-4 text-gray-400" />
                <a href="tel:+78007773297" className="text-gray-300 hover:text-white transition-colors text-sm">
                  +7 (800) 777-32-97
                </a>
              </div>
              <div className="flex items-center space-x-3">
                <Mail className="h-4 w-4 text-gray-400" />
                <a href="mailto:info@spoxpro.ru" className="text-gray-300 hover:text-white transition-colors text-sm">
                  info@spoxpro.ru
                </a>
              </div>
              <div className="flex items-start space-x-3">
                <MapPin className="h-4 w-4 text-gray-400 mt-0.5" />
                <div className="text-gray-300 text-sm">
                  <p>г. Москва</p>
                  <p>Работаем ежедневно</p>
                  <p>с 9:00 до 21:00</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Нижняя часть */}
        <div className="border-t border-gray-800 mt-12 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-gray-400 text-sm">
              © 2024 spoXpro. Все права защищены.
            </div>
            <div className="flex space-x-6">
              <Link to="/privacy" className="text-gray-400 hover:text-white transition-colors text-sm">
                Политика конфиденциальности
              </Link>
              <Link to="/terms" className="text-gray-400 hover:text-white transition-colors text-sm">
                Пользовательское соглашение
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
