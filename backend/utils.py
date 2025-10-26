import qrcode
from io import BytesIO
from fastapi.responses import StreamingResponse


def make_qr_image(data: str):
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
