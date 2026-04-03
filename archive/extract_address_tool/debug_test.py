"""Debug script for address extraction."""
import re

PREFECTURES = [
    "北海道",
    "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県",
    "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]

text = "長野県下高井郡山ノ内町と群馬県吾妻郡草津町があります。"

prefecture_pattern = '|'.join(re.escape(pref) for pref in PREFECTURES)
city_name = r'(?:(?!と|や|及び|、|。)[ぁ-んァ-ヶー一-龠々\d])+'
pattern = f'({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(市)({city_name}区)?|({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(区|町|村)'

print(f"Text: {text}")
print(f"\nPattern: {pattern[:200]}...")
print(f"\nMatches:")

matches = re.finditer(pattern, text)
for i, match in enumerate(matches, 1):
    print(f"\nMatch {i}:")
    print(f"  Full match: {match.group(0)}")
    print(f"  Start: {match.start()}, End: {match.end()}")
    print(f"  Groups: {match.groups()}")
