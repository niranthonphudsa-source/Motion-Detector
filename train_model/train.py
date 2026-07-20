import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import yaml
# ตัวอย่างในไฟล์ main_gui.py หรือสคริปต์หลักของคุณ
import tkinter as tk
from train_gui import TrainGUI # 👈 Import หน้าต่างเทรนที่เราเพิ่งสร้างไว้เข้ามา

def open_train_window():
    """ฟังก์ชันเปิดหน้าต่างเทรนแยกออกมาอีกบานหนึ่ง"""
    train_window = tk.Toplevel() # เปิดเป็นหน้าต่างย่อย (Toplevel) ไม่ให้รบกวนหน้าต่างหลัก
    app = TrainGUI(train_window)
    

with open(r"setting\config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)   

dataset = config["global"]["dataset_path"]
print(dataset)

# 1. โหลดข้อมูลจาก CSV
df = pd.read_csv(dataset)

# 2. แยก X (พิกัด 34 ค่า) และ y (Label ชื่อท่าทาง)
X = df.drop(columns=['label'])
y = df['label']

# 3. แบ่งข้อมูลเป็น Train Set และ Test Set (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. เลือกใช้โมเดล Classifier (ในที่นี้ใช้ Random Forest ซึ่งเหมากับการแยกพิกัดโครงกระดูก)
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# 5. ทดสอบความแม่นยำ
y_pred = clf.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print(classification_report(y_test, y_pred))

# 6. เซฟโมเดลที่เทรนเสร็จแล้วเก็บไว้ใช้ในกล้อง Real-time ต่อไป
joblib.dump(clf, 'pose_classifier_1.pkl')
print("เซฟโมเดล 'pose_classifier.pkl_1' เรียบร้อย!")