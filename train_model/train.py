import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# โหลด CSV
df = pd.read_csv("pose_coordinates.csv")

# ✅ แยก features และ labels
X = df.drop("label", axis=1).values   # เฉพาะตัวเลข X,Y
y = df["label"].values                # label เช่น "Right", "Normal"

# แบ่ง train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# เทรนโมเดล
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# ทดสอบ
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# ใช้งานจริง
new_pose = [X_test[0]]  # ตัวอย่างใช้ข้อมูลจาก test set
prediction = clf.predict(new_pose)
print("ท่าทางที่ตรวจจับได้:", prediction[0])
