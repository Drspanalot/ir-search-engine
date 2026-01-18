import nltk
from nltk.corpus import stopwords
import re

# הורדת רשימת המילים - יש לבצע פעם אחת בתהליך ההתקנה
# nltk.download('stopwords')

class QueryProcessor:
    """מעבד שאילתות המשתמש בספריית NLTK לניקוי מילים נפוצות """
    def __init__(self):
        # טעינת רשימת ה-Stopwords באנגלית מהספרייה
        self.stop_words = set(stopwords.words('english'))
        # שימוש בטוקנייזר שהוגדר על ידי הסגל [cite: 20]
        self.tokenizer = re.compile(r"""[\#\@\w](['\-]?\w)*""", re.UNICODE)

    def tokenize(self, text):
        """המרת טקסט לרשימת טוקנים נקייה [cite: 20]"""
        # 1. המרה לאותיות קטנות (Lowercasing)
        text = text.lower()
        # 2. פיצול למילים לפי ה-Regex של הסגל [cite: 20]
        tokens = [token.group() for token in self.tokenizer.finditer(text)]
        # 3. סינון מילים המופיעות בספריית NLTK
        return [t for t in tokens if t not in self.stop_words]