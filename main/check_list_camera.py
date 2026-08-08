import cv2

def count_total_cameras(max_to_check=10):
    """
    Loops through hardware ports to find the total number of working cameras.
    """
    detected_indices = []
    
    for index in range(max_to_check):
        # Open camera stream
        cap = cv2.VideoCapture(index)
        
        # Verify the camera is opened and working
        if cap.isOpened():
            is_reading, _ = cap.read()
            if is_reading:
                detected_indices.append(index)
            cap.release()
            
    total_cameras = len(detected_indices)
    
    print(f"--- Scan Results ---")
    print(f"Active Camera Indices: {detected_indices}")
    print(f"Total Cameras Found   : {total_cameras}")
    
    return total_cameras

# Run the counter
count_total_cameras()
