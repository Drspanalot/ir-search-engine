import os
import pickle


class MetadataManager:
    """ניהול טעינה ושליפה של PageRank, PageViews ומיפוי כותרות [cite: 10, 56]"""
    def __init__(self, base_path="."):
        self.pagerank = self._load(os.path.join(base_path, "pagerank.pkl"))
        # pageviews צריכים להיות מאוגוסט 2021 [cite: 10]
        self.pageviews = self._load(os.path.join(base_path, "pageviews.pkl"))
        self.id_to_title = self._load(os.path.join(base_path, "id_to_title.pkl"))

    def _load(self, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return {}

    def get_pagerank(self, wiki_ids):
        return [self.pagerank.get(wid, 0) for wid in wiki_ids]

    def get_pageview(self, wiki_ids):
        return [self.pageviews.get(wid, 0) for wid in wiki_ids]