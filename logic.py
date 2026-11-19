import random


def split_random(student_ids, n):
    """Делит список id на n групп как можно ровнее, случайно."""
    ids = student_ids[:]
    random.shuffle(ids)
    groups = [[] for _ in range(n)]
    for i, sid in enumerate(ids):
        groups[i % n].append(sid)
    return groups


def pick_student(student_ids):
    """Случайный ученик из списка id."""
    if not student_ids:
        return None
    return random.choice(student_ids)


STAGES = [
    {"name": "Оргмомент", "minutes": 2},
    {"name": "Проверка домашнего", "minutes": 5},
    {"name": "Новая тема", "minutes": 10},
    {"name": "Закрепление", "minutes": 7},
    {"name": "Итог урока", "minutes": 3},
]


def next_stage(current_index):
    """Возвращает индекс следующего этапа или None, если урок закончен."""
    nxt = current_index + 1
    if nxt >= len(STAGES):
        return None
    return nxt