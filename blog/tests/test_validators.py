from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import random
from blog.models import validate_image_file  # импорт валидатора
from django.core.exceptions import ValidationError  # ← ДОБАВЬТЕ ЭТУ СТРОКУ

class ImageValidatorTest(TestCase):

    def setUp(self):
        # Создаём корректное тестовое изображение
        self.valid_image = self.create_test_image('valid.jpg', (100, 100), 'red')

    def create_test_image(self, name, size, color=None, quality=90, noise=False):
        """Создаёт тестовое изображение в памяти"""
        if noise:
            # Создаём изображение со случайным шумом (плохо сжимается)
            image = Image.new('RGB', size)
            pixels = image.load()
            for x in range(size[0]):
                for y in range(size[1]):
                    pixels[x, y] = (
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255)
                    )
        else:
            # Однотонное изображение
            image = Image.new('RGB', size, color=color)

        image_file = io.BytesIO()
        image.save(image_file, 'JPEG', quality=quality)
        image_file.seek(0)

        return SimpleUploadedFile(
            name=name,
            content=image_file.getvalue(),
            content_type='image/jpeg'
        )

    def test_valid_image(self):
        """Тест корректного изображения"""
        try:
            validate_image_file(self.valid_image)
        except ValidationError:
            self.fail("validate_image_file() raised ValidationError unexpectedly!")

    def test_invalid_file_extension(self):
        """Тестирует недопустимые расширения файлов"""
        invalid_file = SimpleUploadedFile(
            name='document.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )

        with self.assertRaises(ValidationError) as context:
            validate_image_file(invalid_file)

        self.assertIn(
            'Недопустимое расширение файла',
            str(context.exception)
        )

    def test_image_size_limit(self):
        """Тестирует ограничение размера файла (5 МБ)"""
        large_image = self.create_test_image(
            'large.jpg',
            (4900, 4900),
            noise=True,  # Включаем шум
            quality=100  # Максимальное качество
        )

        print(f"Размер изображения: {len(large_image.read())} байт")

        with self.assertRaises(ValidationError) as context:
            validate_image_file(large_image)

        self.assertIn(
            'Размер файла не должен превышать 5 МБ',
            str(context.exception)
        )

    def test_corrupted_image(self):
        """Тестирует повреждённое изображение"""
        corrupted_file = SimpleUploadedFile(
            name='corrupted.jpg',
            content=b'not_an_image_data',
            content_type='image/jpeg'
        )

        with self.assertRaises(ValidationError) as context:
            validate_image_file(corrupted_file)

        self.assertIn(
            'не является корректным изображением или повреждён',
            str(context.exception)
        )
