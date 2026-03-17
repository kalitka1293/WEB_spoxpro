import React from 'react'
import { Phone, Mail, MapPin, Clock } from 'lucide-react'

const ContactPage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Контакты</h1>
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card bg-white p-6 flex items-start space-x-4">
          <Phone className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-gray-900 mb-1">Телефон</h3>
            <a href="tel:+78007773297" className="text-blue-600 hover:underline">+7 (800) 777-32-97</a>
            <p className="text-sm text-gray-500 mt-1">Бесплатно по России</p>
          </div>
        </div>
        <div className="card bg-white p-6 flex items-start space-x-4">
          <Mail className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-gray-900 mb-1">Email</h3>
            <a href="mailto:info@spoxpro.ru" className="text-blue-600 hover:underline">info@spoxpro.ru</a>
            <p className="text-sm text-gray-500 mt-1">Ответим в течение 24 часов</p>
          </div>
        </div>
        <div className="card bg-white p-6 flex items-start space-x-4">
          <MapPin className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-gray-900 mb-1">Адрес</h3>
            <p className="text-gray-600">г. Москва</p>
          </div>
        </div>
        <div className="card bg-white p-6 flex items-start space-x-4">
          <Clock className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-gray-900 mb-1">Режим работы</h3>
            <p className="text-gray-600">Ежедневно с 9:00 до 21:00</p>
          </div>
        </div>
      </div>
    </div>
  </div>
)

export default ContactPage
