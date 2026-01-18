import math
from collections import Counter, defaultdict
class ScoringEngine:
    """לוגיקת החישובים המתמטיים [cite: 56, 64, 65]"""

    @staticmethod
    def cosine_similarity(query_tokens, index, top_n=100):
        scores = defaultdict(float)
        query_counts = Counter(query_tokens)

        q_norm_sq = 0
        for term, freq in query_counts.items():
            if term not in index.df: continue
            # idf = log10(N/df) [cite: 65]
            idf = math.log10(len(index.DL) / index.df[term])
            q_tfidf = (freq / len(query_tokens)) * idf
            q_norm_sq += q_tfidf ** 2

            postings = index.read_posting_list(term, ".")
            for doc_id, d_freq in postings:
                d_tfidf = (d_freq / index.DL.get(doc_id, 1)) * idf
                scores[doc_id] += q_tfidf * d_tfidf

        if not scores: return []

        q_norm = math.sqrt(q_norm_sq)
        final_scores = []
        for doc_id, score in scores.items():
            # חלוקה בנורמות של השאילתה והמסמך [cite: 64]
            normalized_score = score / (q_norm * index.doc_norm.get(doc_id, 1))
            final_scores.append((doc_id, normalized_score))

        return sorted(final_scores, key=lambda x: x[1], reverse=True)[:top_n]

    @staticmethod
    def binary_ranking(query_tokens, index):
        doc_counts = Counter()
        query_set = set(query_tokens)
        for term in query_set:
            if term in index.df:
                postings = index.read_posting_list(term, ".")
                for doc_id, _ in postings:
                    doc_counts[doc_id] += 1
        return sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)