import math
from collections import Counter


def collect_counts(pages, tokenize_func):
    unigram_counts = Counter()
    bigram_counts = Counter()
    total_unigrams = 0

    for doc_id, title, body, links in pages:
        tokens = tokenize_func(body)
        unigram_counts.update(tokens)
        total_unigrams += len(tokens)

        # יצירת Bigrams (זוגות סמוכים)
        bigrams = zip(tokens, tokens[1:])
        bigram_counts.update(bigrams)

    return unigram_counts, bigram_counts, total_unigrams


def calculate_pmi(unigram_counts, bigram_counts, total_unigrams, min_count=5, threshold=5.0):
    phrases = {}

    # N הוא סך כל הטוקנים ב-Corpus
    N = total_unigrams

    for (w1, w2), count_12 in bigram_counts.items():
        if count_12 < min_count:
            continue

        # הסתברויות
        p_w1_w2 = count_12 / N
        p_w1 = unigram_counts[w1] / N
        p_w2 = unigram_counts[w2] / N

        # נוסחת PMI
        pmi = math.log2(p_w1_w2 / (p_w1 * p_w2))

        if pmi > threshold:
            phrases[(w1, w2)] = pmi

    return phrases