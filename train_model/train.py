import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. โหลดข้อมูลจาก CSV
df = pd.read_csv('dataset\pose_dataset.csv')

# 2. แยก X (พิกัด 34 ค่า) และ y (Label ชื่อท่าทาง)
X = df.drop(columns=['label'])
y = df['label']

# 3. แบ่งข้อมูลเป็น Train Set และ Test Set (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. เลือกใช้โมเดล Classifier (ในที่นี้ใช้ Random Forest ซึ่งเหมากับการแยกพิกัดโครงกระดูก)
clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, y_train)

# 5. ทดสอบความแม่นยำ
y_pred = clf.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print(classification_report(y_test, y_pred))

# 6. เซฟโมเดลที่เทรนเสร็จแล้วเก็บไว้ใช้ในกล้อง Real-time ต่อไป
joblib.dump(clf, 'pose_classifier.pkl')
print("เซฟโมเดล 'pose_classifier.pkl' เรียบร้อย!")