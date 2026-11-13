# Лабораторная работа №11, вариант 5: Библиотека
# Кандидат: reader_id (readerId); низкокардинальный ключ: genre_id (genreId);
# последовательный ключ: loan_id (event_id). Основной запрос — выдачи читателя.
import random, hashlib, json
from collections import Counter

random.seed(42)
N, Q, SHARDS = 12000, 30000, 3
READERS, GENRES = 2500, 5          # >= 1000 уникальных readerId

rows = [dict(reader_id=i % READERS,
             genre_id=i % GENRES,
             loan_id=i,
             day_bucket=(i // 50) % 30) for i in range(N)]

def stable_hash(value):
    digest = hashlib.sha256(str(value).encode()).digest()
    return int.from_bytes(digest[:8], 'big')

def low_card(row):      # (A) genreId
    return row['genre_id'] % SHARDS

def hashed_reader(row): # (B) readerId, hashed
    return stable_hash(row['reader_id']) % SHARDS

def range_loan(row):    # (C) range по loan_id
    return min(row['loan_id'] // (N // SHARDS), SHARDS - 1)

def hashed_reader_day(row):  # (D) альтернатива: readerId + dayBucket, hashed
    return stable_hash(f"{row['reader_id']}:{row['day_bucket']}") % SHARDS

RESULTS = []
def describe(name, assign, requests, data=None):
    data = rows if data is None else data
    docs = Counter(assign(r) for r in data)
    load = Counter(assign(r) for r in requests)
    d = [docs[i] for i in range(SHARDS)]
    q = [load[i] for i in range(SHARDS)]
    res = dict(name=name, docs=d, queries=q,
               doc_pct=[round(x / len(data) * 100, 1) for x in d],
               q_pct=[round(x / len(requests) * 100, 1) for x in q],
               doc_max_mean=round(max(d) / (sum(d) / SHARDS), 2),
               query_max_mean=round(max(q) / (sum(q) / SHARDS), 2),
               query_max_min=round(max(q) / min(q), 2) if min(q) > 0 else None)
    RESULTS.append(res)
    print(name, 'docs=', d, 'queries=', q,
          'doc_max_mean=', res['doc_max_mean'],
          'query_max_mean=', res['query_max_mean'],
          'query_max_min=', res['query_max_min'])

# ---- Основной эксперимент (шаги 1-2) ----
uniform = random.choices(rows, k=Q)
hot_rows = [r for r in rows if r['genre_id'] == 0]
hot = [random.choice(hot_rows)
       if random.random() < 0.6 else random.choice(rows)
       for _ in range(Q)]

KEYS = [('genreId', low_card), ('hashed_readerId', hashed_reader),
        ('range_loanId', range_loan)]
print('== Основной эксперимент ==')
for name, fn in KEYS:
    describe(name + '/uniform', fn, uniform)
    describe(name + '/hot', fn, hot)

# ---- Шаг 4: один жанр содержит 80% записей ----
rng = random.Random(7)
rows80 = [dict(r, genre_id=0 if rng.random() < 0.8 else rng.randint(1, GENRES - 1))
          for r in rows]
hot_rows80 = [r for r in rows80 if r['genre_id'] == 0]
rng2 = random.Random(8)
uniform80 = rng2.choices(rows80, k=Q)
hot80 = [rng2.choice(hot_rows80) if rng2.random() < 0.6 else rng2.choice(rows80)
         for _ in range(Q)]
print('== Шаг 4: 80% записей в жанре 0 ==')
for name, fn in KEYS + [('hashed_readerId+dayBucket', hashed_reader_day)]:
    describe('S4 ' + name + '/uniform', fn, uniform80, rows80)
    describe('S4 ' + name + '/hot', fn, hot80, rows80)

# ---- AP-04: поток новых выдач (монотонный loan_id) ----
print('== AP-04: 3000 новых выдач (loan_id = 12000..14999) ==')
new = [dict(reader_id=i % READERS, genre_id=i % GENRES, loan_id=i,
            day_bucket=(i // 50) % 30) for i in range(N, N + 3000)]
def ap04(name, fn):
    c = Counter(fn(r) for r in new)
    v = [c[i] for i in range(SHARDS)]
    print(name, 'inserts=', v)
    RESULTS.append(dict(name='AP04 ' + name, inserts=v))
ap04('range_loanId', lambda r: min(r['loan_id'] // (N // SHARDS), SHARDS - 1))
ap04('hashed_readerId', hashed_reader)
ap04('hashed_readerId+dayBucket', hashed_reader_day)

# ---- Targeted / scatter-gather: сколько шардов затрагивает запрос ----
print('== Кол-во шардов на запрос AP-01 (выдачи читателя) ==')
by_reader = {}
for r in rows:
    by_reader.setdefault(r['reader_id'], set()).add(hashed_reader_day(r))
avg = sum(len(s) for s in by_reader.values()) / len(by_reader)
print('hashed_readerId+dayBucket без dayBucket в фильтре: среднее шардов =', round(avg, 2))

json.dump(RESULTS, open('results.json', 'w'), ensure_ascii=False, indent=1)
