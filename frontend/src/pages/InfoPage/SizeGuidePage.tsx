import React from 'react'

const sizes = [
  { size: 'XS', chest: '80-84', waist: '60-64', hips: '86-90' },
  { size: 'S', chest: '84-88', waist: '64-68', hips: '90-94' },
  { size: 'M', chest: '88-92', waist: '68-72', hips: '94-98' },
  { size: 'L', chest: '92-96', waist: '72-76', hips: '98-102' },
  { size: 'XL', chest: '96-100', waist: '76-80', hips: '102-106' },
  { size: 'XXL', chest: '100-104', waist: '80-84', hips: '106-110' },
]

const SizeGuidePage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Таблица размеров</h1>
      <div className="card bg-white p-8">
        <p className="text-gray-600 mb-6">Все размеры указаны в сантиметрах. Измерьте свои параметры и сравните с таблицей.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Размер</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Грудь (см)</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Талия (см)</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Бёдра (см)</th>
              </tr>
            </thead>
            <tbody>
              {sizes.map(s => (
                <tr key={s.size} className="border-t border-gray-200">
                  <td className="px-4 py-3 font-medium text-gray-900">{s.size}</td>
                  <td className="px-4 py-3 text-gray-600">{s.chest}</td>
                  <td className="px-4 py-3 text-gray-600">{s.waist}</td>
                  <td className="px-4 py-3 text-gray-600">{s.hips}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
)

export default SizeGuidePage
