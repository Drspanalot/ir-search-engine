import math
import pickle
import re
from collections import Counter, defaultdict
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from google.cloud import storage
import sys
import inverted_index_gcp
import io

old_module_names = [
    'inverted_index_title_nostem',
    'inverted_index_body_stemmed',
    'inverted_index_anchor',
    'inverted_index'
]

for name in old_module_names:
    sys.modules[name] = inverted_index_gcp

BUCKET_NAME = "db204905756"

def get_gcs_client():
    """Get or create GCS client."""
    return storage.Client()

class RenameUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        old_modules = [
            'inverted_index_title_nostem',
            'inverted_index_body_stemmed',
            'inverted_index_anchor',
            'inverted_index_title_stemmed',
            'inverted_index',
            '__main__'
        ]
        if module in old_modules:
            return getattr(inverted_index_gcp, name)
        return super().find_class(module, name)

def renamed_load(file_obj):
    return RenameUnpickler(file_obj).load()

def read_pickle_from_gcs(bucket_name, blob_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    if not blob.exists():
        raise FileNotFoundError(f"Missing: gs://{bucket_name}/{blob_path}")
    return RenameUnpickler(io.BytesIO(blob.download_as_bytes())).load()


class BackendClass:
    def __init__(self):
        self.body_stem_index = None
        self.title_stem_index = None
        self.title_nostem_index = None
        self.anchor_index = None
        self.title_phrase_index = None
        self.body_phrase_index = None
        self.page_rank = {}
        self.page_views = {}
        self.doc_lengths = {}
        self.id_to_title = {}
        self.stop_words = frozenset(stopwords.words('english'))
        self.stemmer = PorterStemmer()
        self.RE_WORD = re.compile(r"[\#\@\w](['\-]?\w){2,24}", re.UNICODE)
        self.gcs_client = storage.Client()
        self.bucket = self.gcs_client.bucket(BUCKET_NAME)

        BUCKET_NAME_LOCAL = "db204905756"

        print("Loading Indices")
        self.body_stem_index = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'postings_gcp/index.pkl')
        self.title_stem_index = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'title_stemmed/index.pkl')
        self.title_nostem_index = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'title_nostem/index.pkl')
        self.anchor_index = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'anchor_index/anchor_index.pkl')
        #######
        #phrase testing:
        self.title_phrase_index = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'title_stemmed_phrases_idx/index.pkl')
        self.body_phrase_index = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'body_stemmed_phrases_idx/index.pkl')
        
        # Phrases not needed - unigrams work better

        print("Loading Metadata")
        self.page_rank = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'pr/pr.pkl')
        self.page_views = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'page_views/pageview.pkl')

        try:
            self.doc_lengths = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'postings_gcp/doc_lengths.pkl')
        except:
            self.doc_lengths = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'postings_gcp/doc_lengths.pickle')

        print("Loading Title Mappings")
        even = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'id_title/even_id_title_dict.pkl')
        odd = read_pickle_from_gcs(BUCKET_NAME_LOCAL, 'id_title/uneven_id_title_dict.pkl')
        self.id_to_title = {**even, **odd}
        
        self.N = len(self.id_to_title)
        #maoing for the indexes
        self.index_gcs_dirs = {
            id(self.body_stem_index): 'postings_gcp',
            id(self.title_stem_index): 'title_stemmed',
            id(self.title_nostem_index): 'title_nostem',
            id(self.anchor_index): 'anchor_postings_gcp',
            id(self.title_phrase_index): 'title_stemmed_phrases_idx',
            id(self.body_phrase_index): 'body_stemmed_phrases_idx'
        }

        print("Backend ready!")

    def read_posting_list_from_gcs(self, index, term, gcs_folder):
        """
        callin for the psoting list from GCP
        """
        if term not in index.posting_locs:
            return []
        
        posting_list = []
        locs = index.posting_locs[term]
        TUPLE_SIZE = 6
        
        for file_name, offset in locs:
            if '/' in file_name:
                file_name = file_name.split('/')[-1]

            blob_path = f"{gcs_folder}/{file_name}"
            blob = self.bucket.blob(blob_path)
            
            if not blob.exists():
                continue
            
            data = blob.download_as_bytes()
            
            # read the posting list
            num_entries = index.df[term]
            for i in range(num_entries):
                pos = offset + (i * TUPLE_SIZE)
                if pos + TUPLE_SIZE <= len(data):
                    doc_id = int.from_bytes(data[pos:pos+4], 'big')
                    tf = int.from_bytes(data[pos+4:pos+TUPLE_SIZE], 'big')
                    posting_list.append((doc_id, tf))
        
        return posting_list

    def create_bigrams(self, tokens):
        """create bigram from the tokens list"""
        bigrams = []
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            bigrams.append(bigram)
        return bigrams
    
    def tokenize(self, text, stem=True):
        tokens = [token.group().lower() for token in self.RE_WORD.finditer(text)]
        if stem:
            return [self.stemmer.stem(t) for t in tokens if t not in self.stop_words]
        return [t for t in tokens if t not in self.stop_words]
    
    def extract_phrases(self, tokens):
        """
        """
        phrases = []
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            phrases.append(bigram)
        return phrases

    def search(self, query):
        tokens = self.tokenize(query, stem=True)
        if not tokens:
            return []

        body_results_raw = self.get_body_scores(query)
        title_results_raw = self.get_title_scores(query)
        anchor_results_raw = self.get_anchor_incoming_score(query)  # Query-Specific PageRank!

        body_sorted = sorted(body_results_raw.items(), key=lambda x: x[1], reverse=True)[:500]
        title_sorted = sorted(title_results_raw.items(), key=lambda x: x[1], reverse=True)[:500]
        anchor_sorted = sorted(anchor_results_raw.items(), key=lambda x: x[1], reverse=True)[:500]
        
        body_dict = dict(body_sorted)
        title_dict = dict(title_sorted)
        anchor_dict = dict(anchor_sorted)

        candidate_ids = set(body_dict.keys()) | set(title_dict.keys()) | set(anchor_dict.keys())

        #normalize the wieght
        max_body = max(body_dict.values()) if body_dict else 1
        max_title = max(title_dict.values()) if title_dict else 1
        max_anchor = max(anchor_dict.values()) if anchor_dict else 1
        
        candidate_prs = [self.page_rank.get(int(doc_id), 0) for doc_id in candidate_ids]
        max_pr = max(candidate_prs) if candidate_prs else 1

        final_scores = []
        for doc_id in candidate_ids:
            s_body = (body_dict.get(doc_id, 0) / max_body)
            s_title = (title_dict.get(doc_id, 0) / max_title)
            s_anchor = (anchor_dict.get(doc_id, 0) / max_anchor)

            pr = self.page_rank.get(int(doc_id), 0)
            pr_normalized = pr / max_pr  # נרמול!
            pv = self.page_views.get(int(doc_id), 0)

            score = (0.3 * s_body) + (0.5 * s_title) + (0.15 * s_anchor) + (0.05 * pr_normalized)  # Max title!

            title = self.id_to_title.get(int(doc_id), "Unknown")
            final_scores.append((str(doc_id), title, score))

        final_scores.sort(key=lambda x: x[2], reverse=True)
        return [(res[0], res[1]) for res in final_scores[:100]]
    
    def get_body_scores(self, query):
        """החזר dict של {doc_id: score} לגוף - with BM25 + phrases!"""
        tokens = self.tokenize(query, stem=False)
        if not tokens:
            return {}
        
        stemmed_tokens = [self.stemmer.stem(t) for t in tokens]
        bigrams = self.create_bigrams(stemmed_tokens)
        
        unigram_scores = self.calculate_bm25(stemmed_tokens, self.body_stem_index, 'postings_gcp')
        
        if bigrams and hasattr(self, 'body_phrase_index') and self.body_phrase_index is not None:
            phrase_scores = self.calculate_bm25(bigrams, self.body_phrase_index, 'body_stemmed_phrases_idx')
            for doc_id, score in phrase_scores.items():
                unigram_scores[doc_id] = unigram_scores.get(doc_id, 0) + score
        
        return unigram_scores
    

    def get_title_scores(self, query):
        """
        Smart IDF-Weighted Title with Missing Word Penalty
        """
        import math
        from collections import defaultdict
        
        tokens = self.tokenize(query, stem=False)
        if not tokens:
            return {}
        
        stemmed_tokens = [self.stemmer.stem(t) for t in tokens]
        scores = defaultdict(float)
        
        # Calculate IDF for each query term (use nostem index - the one we have!)
        query_idfs = {}
        for token in tokens:  # Use original tokens, not stemmed
            if token in self.title_nostem_index.df:
                df = self.title_nostem_index.df[token]
                query_idfs[token] = math.log10(self.N / df) if df > 0 else 0
        
        # Sum IDF of matching terms
        for token, idf in query_idfs.items():
            try:
                for doc_id, tf in self.read_posting_list_from_gcs(
                    self.title_nostem_index, token, 'postings_title_nostem'
                ):
                    scores[doc_id] += idf
            except:
                continue
        
        # Penalty for missing rare words
        for doc_id in list(scores.keys()):
            title = self.id_to_title.get(doc_id, '').lower()
            title_tokens = set(self.tokenize(title, stem=False))  # No stem to match
            
            missing_penalty = 0
            for token in tokens:  # Check original tokens
                if token not in title_tokens:
                    idf = query_idfs.get(token, 0)
                    if idf > 3.5:  # Rare word missing = penalty
                        missing_penalty += idf * 0.15  # Gentler penalty
            
            scores[doc_id] -= missing_penalty
        
        return scores
    
    def get_anchor_scores(self, query):
        """החזר dict של {doc_id: score} ל-anchor"""
        tokens = self.tokenize(query, stem=False)
        if not tokens:
            return {}

    def get_anchor_incoming_score(self, query):
        """
        Query-Specific PageRank!
        """
        import math
        from collections import defaultdict
        
        tokens = self.tokenize(query, stem=False)
        if not tokens:
            return {}
        
        scores = defaultdict(float)
        
        for token in tokens:
            if token not in self.anchor_index.df:
                continue
            
            df = self.anchor_index.df[token]
            idf = math.log10(self.N / df) if df > 0 else 0
            
            try:
                for doc_id, anchor_count in self.read_posting_list_from_gcs(
                    self.anchor_index, token, 'anchor_postings_gcp'
                ):
                    scores[doc_id] += idf * math.log1p(anchor_count)
            except Exception as e:
                continue
        
        return scores
        return self.get_overlap_score(tokens, self.anchor_index, 'anchor_postings_gcp')

    def calculate_bm25(self, tokens, index, gcs_folder, k1=1.2, b=0.5):
        """
        BM25 scoring - better than TF-IDF for IR!
        k1=1.2: term frequency saturation (lower = more saturation)
        b=0.5: document length normalization (lower = less penalty for long docs)
        """
        scores = defaultdict(float)
        
        # Calculate average document length
        if not hasattr(self, '_avgdl'):
            self._avgdl = sum(self.doc_lengths.values()) / len(self.doc_lengths) if self.doc_lengths else 1
        avgdl = self._avgdl
        
        query_counts = Counter(tokens)
        
        for term in set(tokens):  # Unique terms only
            if term not in index.df:
                continue
                
            df = index.df[term]
            # BM25 IDF (different from TF-IDF!)
            idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1.0)
            
            for doc_id, tf in self.read_posting_list_from_gcs(index, term, gcs_folder):
                doc_len = self.doc_lengths.get(doc_id, avgdl)
                
                # BM25 formula
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avgdl))
                
                scores[doc_id] += idf * (numerator / denominator)
        
        return scores

    def get_overlap_score(self, tokens, index, gcs_folder):
        scores = defaultdict(float)
        unique_tokens = set(tokens)
        
        for term in unique_tokens:
            if term in index.df:
                for doc_id, freq in self.read_posting_list_from_gcs(index, term, gcs_folder):
                    scores[doc_id] += 1
        
        return scores

    def search_body(self, query):
        tokens = self.tokenize(query, stem=False)
        if not tokens:
            return []

        stemmed_tokens = [self.stemmer.stem(t) for t in tokens]
        scores = self.calculate_cosine_similarity(stemmed_tokens, self.body_stem_index, 'postings_gcp')

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:100]
        return [(str(doc_id), self.id_to_title.get(doc_id, "Unknown")) for doc_id, _ in sorted_results]

    def search_title(self, query):
        tokens = self.tokenize(query, stem=False)
        if not tokens:
            return []
        
        scores = self.get_overlap_score(tokens, self.title_nostem_index, 'postings_title_nostem')
        
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(str(doc_id), self.id_to_title.get(doc_id, "Unknown")) for doc_id, _ in sorted_results]

    def search_anchor(self, query):
        tokens = self.tokenize(query, stem=False)
        if not tokens:
            return []
        
        scores = self.get_overlap_score(tokens, self.anchor_index, 'anchor_postings_gcp')
        
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(str(doc_id), self.id_to_title.get(doc_id, "Unknown")) for doc_id, _ in sorted_results]

    def get_pagerank(self, wiki_ids):
        return [self.page_rank.get(int(doc_id), 0) for doc_id in wiki_ids]

    def get_pageview(self, wiki_ids):
        return [self.page_views.get(int(doc_id), 0) for doc_id in wiki_ids]
