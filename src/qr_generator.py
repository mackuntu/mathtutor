"""QR code generation for worksheet identification."""

from io import BytesIO

import qrcode


def create_qr_code(worksheet_id: str) -> BytesIO:
    """Generate a QR code for worksheet identification.

    Args:
        worksheet_id: Unique identifier for worksheet.

    Returns:
        BytesIO containing QR code image.
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
    )
    qr.add_data(worksheet_id)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")
    byte_stream = BytesIO()
    qr_image.save(byte_stream, format="PNG")
    byte_stream.seek(0)

    return byte_stream
