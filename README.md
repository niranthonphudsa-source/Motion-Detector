# Motion-Detector

install visual studio
install SQL Server Manager Studio
install project
---setting---
1. install python  3.10.x
2. new floder project
3. make venv
----open command promt
----cd "path floder project"
----run python -m venv venv
-----run venv\Scripts\activate.bat
-----install library----
pip install opencv-python Pillow PyYAML pyodbc 
pip install ultralytics pandas joblib pyserial 
pip install tkcalendar 
pip install shutil scikit-learn
pip install openvino
pip install openpyxl

-----make file .json in cmd-----
(venv) C:\(path project)\type nul > db_config.json
(venv) C:\(path project)\notepad db_config.json

copy pase
{
    "server": "localhost",
    "database": "databasename",
    "auth_type": "SQL Server Authentication",
    "username": "username",
    "password": "password",
    "driver": "ODBC Driver 18 for SQL Server"
}

---install OBDC for connect database
Invoke-WebRequest -Uri "https://go.microsoft.com/fwlink/?linkid=2249006" -OutFile "msodbcsql18.msi"; Start-Process msiexec.exe -ArgumentList '/i msodbcsql18.msi /qn IACCEPTMSODBCSQLLICENSETERMS=YES' -Wait; Remove-Item "msodbcsql18.msi"