x = [{
        "id": 1,
        "name": "Синяя хлопковая футболка",
        "description": "Легкая повседневная футболка из 100% хлопка. Удобная посадка, дышащая ткань.",
        "price": 1299,
        "discountPercent": 15,
        "stockQuantity": 47,
        "size": ["M", 'SX', "TEST"],
        "color": "Синий",
        "gender": "M",
        "images": [
            "/img/clothes/kombez blue/kombez blue3.jpg",
            "/img/clothes/kombez blue/kombez blue2.jpg",
            "/img/clothes/kombez blue/kombez blue1.jpg"
        ],
        "category": {
            "name": "Футболки",
            "categoryId": 1,
        }
    }]

import json

print(type((json.dumps(x))))