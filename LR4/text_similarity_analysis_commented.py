"""Анализ схожести двух текстов разными метриками.

Этот файл — прокомментированная копия исходного скрипта.
Логика и структура сохранены, добавлены пояснения к шагам алгоритма.
"""

from collections import Counter, defaultdict
from pathlib import Path
import math
import re

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams

# Настройка шрифта для корректного отображения кириллицы на графиках.
rcParams["font.sans-serif"] = ["DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

# Пытаемся использовать spaCy для токенизации.
# Если библиотека недоступна, работаем через regex.
try:
    import spacy
    NLP = spacy.load("ru_core_news_sm")
except Exception:
    NLP = None


HAS_LEMMATIZER = NLP is not None and "lemmatizer" in NLP.pipe_names


def tok(text, lemmatize=True):
    """Токенизация текста в нижнем регистре.

    Возвращает только буквенные токены:
    - через spaCy, если он доступен (с лемматизацией при lemmatize=True);
    - через regex как fallback.
    """
    text = text.lower()
    if NLP is not None:
        doc = NLP(text)
        if lemmatize and HAS_LEMMATIZER:
            # Если лемма не определена, откатываемся к исходному токену.
            return [
                (t.lemma_.lower() if t.lemma_ and t.lemma_ != "-PRON-" else t.text)
                for t in doc
                if t.text.strip() and t.is_alpha
            ]
        return [t.text for t in doc if t.text.strip() and t.is_alpha]
    return re.findall(r"\w+", text, flags=re.UNICODE)


def make_windows(words, k):
    """Формирует скользящие окна длины k.

    Для каждого окна возвращает кортеж:
    (индекс начала, строка окна, множество слов окна).
    Множество нужно для быстрого подсчета пересечений по словам.
    """
    return [(i, " ".join(words[i : i + k]), set(words[i : i + k])) for i in range(max(0, len(words) - k + 1))]


def lev(a, b):
    """Нормализованная схожесть Левенштейна в диапазоне [0, 1]."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    # Делаем a более длинной строкой, чтобы уменьшить размер DP-буфера.
    if len(a) < len(b):
        a, b = b, a

    # Одномерная динамика по расстоянию редактирования.
    prev = list(range(len(b) + 1))
    for i, c1 in enumerate(a, 1):
        cur = [i]
        for j, c2 in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (c1 != c2)))
        prev = cur

    # Преобразуем расстояние в схожесть: 1 - normalized_distance.
    return 1 - prev[-1] / max(len(a), len(b))


def jaro(a, b):
    """Схожесть Жаро в диапазоне [0, 1]."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    la, lb = len(a), len(b)
    # Радиус поиска совпадающих символов.
    d = max(0, max(la, lb) // 2 - 1)

    ma, mb, m = [0] * la, [0] * lb, 0
    for i in range(la):
        for j in range(max(0, i - d), min(i + d + 1, lb)):
            if not mb[j] and a[i] == b[j]:
                ma[i] = mb[j] = 1
                m += 1
                break

    if m == 0:
        return 0.0

    # Подсчет транспозиций среди совпавших символов.
    t, j = 0, 0
    for i in range(la):
        if not ma[i]:
            continue
        while not mb[j]:
            j += 1
        t += a[i] != b[j]
        j += 1

    return (m / la + m / lb + (m - t / 2) / m) / 3


def winkler(a, b, p=0.1, bt=0.7):
    """Схожесть Jaro-Winkler.

    Если базовая схожесть Жаро выше порога bt, добавляем бонус
    за общий префикс (до 4 символов).
    """
    dj = jaro(a, b)
    if dj <= bt:
        return dj

    pref = 0
    for x, y in zip(a[:4], b[:4]):
        if x != y:
            break
        pref += 1
    return dj + pref * p * (1 - dj)


def jaccard(a, b, n=2):
    """Схожесть Жаккара по n-граммам строки."""

    def ng(s):
        if len(s) < n:
            return {s} if s else set()
        return {s[i : i + n] for i in range(len(s) - n + 1)}

    x, y = ng(a), ng(b)
    if not x and not y:
        return 1.0
    if not x or not y:
        return 0.0
    return len(x & y) / len(x | y)


def best_thr(vals, method):
    """Подбор порога схожести по сетке.

    Идея: максимизируем компромисс между:
    - средним качеством отобранных совпадений;
    - покрытием (доля значений выше порога).

    Функция качества:
    q = 0.65 * mean(selected) + 0.35 * coverage
    """
    if vals.size == 0:
        return 1.0

    # Для разных метрик используем разные стартовые диапазоны порогов.
    grid = np.arange(0.65, 1.001, 0.01) if method in {"jaro", "jaro_winkler"} else (
        np.arange(0.55, 1.001, 0.01) if method == "levenshtein" else np.arange(0.35, 1.001, 0.01)
    )

    best_t, best_q = float(grid[0]), -1.0
    for t in grid:
        s = vals[vals >= t]
        if s.size == 0:
            continue
        q = 0.65 * float(np.mean(s)) + 0.35 * (s.size / vals.size)
        if q > best_q:
            best_t, best_q = float(t), q
    return best_t


def score_pairs(w1, w2, sim, min_overlap):
    """Считает схожесть только для перспективных пар окон.

    Оптимизация:
    - строим обратный индекс: слово -> список окон второго текста;
    - сравниваем окна, если у них хотя бы min_overlap общих слов.
    """
    idx = defaultdict(list)
    for j, (_, _, terms) in enumerate(w2):
        for term in terms:
            idx[term].append(j)

    out = []
    for i, p1, t1 in w1:
        # Считаем, сколько общих слов у текущего окна с каждым окном w2.
        c = Counter()
        for term in t1:
            for j in idx.get(term, []):
                c[j] += 1

        # Для прошедших фильтр пар вычисляем строковую схожесть.
        for j, ov in c.items():
            if ov >= min_overlap:
                out.append((p1, sim(p1, w2[j][1])))
    return out


def analyze(words1, words2, ws=(5, 10, 20, 30), n=2, p=0.1, bt=0.7):
    """Основной цикл анализа по метрикам и размерам окон."""
    methods = {
        "levenshtein": lev,
        "jaro": jaro,
        "jaro_winkler": lambda a, b: winkler(a, b, p, bt),
        "jaccard": lambda a, b: jaccard(a, b, n),
    }
    stats = defaultdict(dict)

    print("=" * 64)
    print("АНАЛИЗ СХОЖЕСТИ ТЕКСТОВ")
    print("=" * 64)
    print(f"Текст 1: {len(words1)} слов")
    print(f"Текст 2: {len(words2)} слов")
    print(f"Токенизация: {'SpaCy' if NLP is not None else 'regex fallback'}")

    for name, sim in methods.items():
        print("\n" + "-" * 64)
        print(name.upper())
        print("-" * 64)

        for k in ws:
            w1, w2 = make_windows(words1, k), make_windows(words2, k)

            # Минимум общих слов для допуска пары к детальному сравнению.
            scored = score_pairs(w1, w2, sim, max(1, math.ceil(k * 0.35)))
            vals = np.array([x[1] for x in scored], dtype=float)

            thr = best_thr(vals, name)
            matched = [x for x in scored if x[1] >= thr]

            # total_length: сумма длин строк-окон из первого текста среди совпадений.
            total = sum(len(x[0]) for x in matched)
            avg = float(np.mean([x[1] for x in matched])) if matched else 0.0

            stats[name][k] = {
                "threshold": thr,
                "matches_count": len(matched),
                "total_length": int(total),
                "avg_similarity": avg,
            }

            print(
                f"окно={k:>2} | порог={thr:.2f} | совпадений={len(matched):>4} | "
                f"длина={int(total):>5} | ср={avg:.3f}"
            )
    return stats


def plot(stats, ws, out):
    """Строит 4 графика и сохраняет их в PNG."""
    methods = list(stats)
    fig, ax = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Схожесть текстов", fontsize=14)

    items = [
        ("matches_count", "Количество совпадений", "o", None),
        ("total_length", "Суммарная длина", "s", None),
        ("avg_similarity", "Средняя схожесть", "^", (0, 1)),
        ("threshold", "Оптимальные пороги", "D", (0, 1)),
    ]

    for a, (key, title, marker, ylim) in zip(ax.flat, items):
        for m in methods:
            a.plot(ws, [stats[m][k][key] for k in ws], marker=marker, linewidth=2, label=m)
        a.set_title(title)
        a.set_xlabel("Размер окна (слов)")
        if ylim:
            a.set_ylim(*ylim)
        a.grid(alpha=0.3)
        a.legend()

    plt.tight_layout()
    img = out / "similarity_analysis.png"
    plt.savefig(img, dpi=250, bbox_inches="tight")
    print(f"\nСохранен график: {img}")


def main():
    """Точка входа: чтение файлов, анализ, печать сводки и построение графика."""
    base = Path(__file__).resolve().parent
    use_lemmatization = True

    words1 = tok((base / "hameleon_short.txt").read_text(encoding="utf-8"), lemmatize=use_lemmatization)
    words2 = tok((base / "hameleon.txt").read_text(encoding="utf-8"), lemmatize=use_lemmatization)
    ws = [5, 10, 20, 30]

    if use_lemmatization and HAS_LEMMATIZER:
        print("Лемматизация: включена (spaCy lemmatizer)")
    elif use_lemmatization and not HAS_LEMMATIZER:
        print("Лемматизация: недоступна (fallback к токенам без лемм)")
    else:
        print("Лемматизация: выключена")

    stats = analyze(words1, words2, ws=ws, n=2, p=0.1, bt=0.7)

    print("\n" + "=" * 64)
    print("ИТОГОВАЯ СВОДКА")
    print("=" * 64)
    for m in stats:
        cnt = sum(stats[m][k]["matches_count"] for k in ws)
        ln = sum(stats[m][k]["total_length"] for k in ws)
        print(f"{m:>13}: совпадений={cnt:>4}, суммарная длина={ln:>5}")

    plot(stats, ws, base)
    print("\nАНАЛИЗ ЗАВЕРШЕН")


if __name__ == "__main__":
    main()
