import React, { useState, useEffect } from 'react'

interface HeroSliderProps {
  images: string[]
  interval?: number
}

const HeroSlider: React.FC<HeroSliderProps> = ({ images, interval = 5000 }) => {
  const [currentSlide, setCurrentSlide] = useState(0)

  useEffect(() => {
    const slideInterval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % images.length)
    }, interval)

    return () => clearInterval(slideInterval)
  }, [images.length, interval])

  const goToSlide = (index: number) => {
    setCurrentSlide(index)
  }

  return (
    <div className="hero-slider absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-700">
      {images.map((image, index) => (
        <div
          key={index}
          className={`hero-slide absolute inset-0 transition-opacity duration-1000 ${
            index === currentSlide ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <img 
            src={image}
            alt={`spoXpro Collection ${index + 1}`}
            className="w-full h-full object-cover"
            onLoad={() => console.log(`Image loaded: ${image}`)}
            onError={(e) => {
              console.error(`Failed to load image: ${image}`)
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
        </div>
      ))}
      
      {/* Индикаторы слайдов */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex space-x-3 z-20">
        {images.map((_, index) => (
          <button
            key={index}
            className={`hero-indicator w-3 h-3 rounded-full bg-white transition-opacity ${
              index === currentSlide ? 'active opacity-100' : 'opacity-40 hover:opacity-70'
            }`}
            onClick={() => goToSlide(index)}
          />
        ))}
      </div>
    </div>
  )
}

export default HeroSlider

