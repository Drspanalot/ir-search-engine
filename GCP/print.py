import pickle
from itertools import islice

path = r"C:\Users\amalm\PycharmProjects\IR\index\even_id_title_dict.pkl"

with open(path, "rb") as f:
    obj = pickle.load(f)

print(f"Type of object: {type(obj)}")
print(f"Total entries: {len(obj):,}") # מדפיס כמה מסמכים יש בסך הכל
print("-" * 20)

# אם זה מילון (Dictionary)
if isinstance(obj, dict):
    # מדפיס את 10 האיברים הראשונים
    first_10 = dict(islice(obj.items(), 10))
    for doc_id, length in first_10.items():
        print(f"Doc ID: {doc_id} | Length: {length}")

# אם זה רשימה (List)
elif isinstance(obj, list):
    print("First 10 items in list:")
    for item in obj[:10]:
        print(item)