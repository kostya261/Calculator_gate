# estimate_utils.py
from datetime import datetime


def prepare_materials_for_estimate(items):
    """Преобразует данные из БД в формат для EstimateDialog"""
    materials = []
    for item in items:
        materials.append([
            item['name'],
            "",
            str(item['length']),
            str(item['quantity']),
            item['weight'],
            "",
            item['note']
        ])
    return materials


def get_estimate_data(estimate_id):
    """Заглушка, но можно и настоящую логику"""
    return {
        'number': f"СМ-{datetime.now().strftime('%Y%m%d')}-001",
        'date': datetime.now().strftime('%d.%m.%Y'),
        'client': "Не выбран",
        'address': "Не указан"
    }