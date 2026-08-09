import cv2
# แสดงสถานะโหมดใช้งานบน UI    
def showModeDisplay(frame, current_mode, fps, fps_per_sec):
    mode_names = {0: "NORMAL", 1: "DRAW POLYGON", 2: "MARK POINT 1 (START)", 3: "MARK POINT 2 (REVERSE)", 0: "Save Config"}
    status_text = f"MODE: {mode_names.get(current_mode, 'NORMAL')} ------- FPS_LIMT: {fps} -- Fps_per_Sec: {fps_per_sec}"
    cv2.putText(frame, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "1=Polygon | 3=Start Pt | 4=Reverse Pt | 2=Save Config | C=Clear", 
                (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
    cv2.putText(frame, "o=open_database_gui | d=open_stats_gui | S=Settings | Q=Exit", 
            (15, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)