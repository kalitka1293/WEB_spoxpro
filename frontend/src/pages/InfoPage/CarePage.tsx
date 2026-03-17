import React from 'react'

const CarePage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Уход за изделиями</h1>
      <div className="card bg-white p-8 space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Стирка</h2>
          <ul className="text-gray-600 space-y-2">
            <li>• Стирать при температуре не выше 30°C</li>
            <li>• Использовать деликатный режим стирки</li>
            <li>• Не использовать отбеливатели</li>
            <li>• Стирать изделие вывернутым наизнанку</li>
          </ul>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Сушка</h2>
          <ul className="text-gray-600 space-y-2">
            <li>• Сушить в расправленном виде на горизонтальной поверхности</li>
            <li>• Не использовать машинную сушку</li>
            <li>• Избегать прямых солнечных лучей</li>
          </ul>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Глажка</h2>
          <ul className="text-gray-600 space-y-2">
            <li>• Гладить при низкой температуре (до 110°C)</li>
            <li>• Не гладить по принтам и декоративным элементам</li>
          </ul>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Хранение</h2>
          <ul className="text-gray-600 space-y-2">
            <li>• Хранить в сухом проветриваемом месте</li>
            <li>• Не хранить во влажном состоянии</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
)

export default CarePage
