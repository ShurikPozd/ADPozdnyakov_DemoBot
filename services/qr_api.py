"""Генератор QR-кодов с использованием библиотеки qrcode.

Принимает строку данных и возвращает BytesIO-объект с изображением PNG.
"""


import qrcode
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

async def generate_qr_code(data: str) -> BytesIO:
    """Генерирует QR-код для переданной строки данных.

    Args:
        data: Текст или ссылка для кодирования.

    Returns:
        BytesIO: Поток байтов с изображением QR-кода в формате PNG.

    Raises:
        Exception: Любая ошибка при генерации QR-кода (пробрасывается выше).
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        logger.debug(f"QR code generated for data length {len(data)}")
        return bio
    except Exception as e:
        logger.exception(f"Failed to generate QR code for data: {data[:50]}")
        raise  # пробросим исключение выше, где оно будет обработано в хендлере