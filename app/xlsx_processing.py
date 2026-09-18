from io import BytesIO

from openpyxl import load_workbook

from app.marketplaces import wildberries

_MARKETPLACES = [wildberries]


class UnrecognizedReportFormatError(Exception):
    """Файл не соответствует ни одному известному формату выгрузки."""


def process_xlsx(data: bytes) -> bytes:
    workbook = load_workbook(BytesIO(data), data_only=True)

    for marketplace in _MARKETPLACES:
        if marketplace.detect(workbook):
            result_workbook = marketplace.process(workbook)
            break
    else:
        raise UnrecognizedReportFormatError(
            "Формат файла не распознан. Попробуйте использовать другой файл."
        )

    buffer = BytesIO()
    result_workbook.save(buffer)
    return buffer.getvalue()
