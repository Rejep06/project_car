# Источники визуальных материалов

## Логотип

`logo.png` и `favicon.png` созданы специально для проекта и хранятся локально
в `public/assets` обоих frontend-приложений.

## Фотографии автомобилей

Фотографии загружены с Unsplash, обрезаны и оптимизированы для интерфейса.

- Главная карточка: Puscas Adryan — https://unsplash.com/photos/zQ31Ul9QMtw
- Резервная обложка программы: Lorenzo Hamers — https://unsplash.com/photos/FlkyX7zZosY
- Лицензия Unsplash: https://unsplash.com/license

Frontend сначала показывает `image_url`, указанный администратором для программы.
Если ссылка отсутствует или изображение не загрузилось, используется локальная
резервная фотография `program-car-photo.jpg`.
