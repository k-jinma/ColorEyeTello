from djitellopy import Tello
import cv2
import time

tello = Tello(retry_count=1)
print("Attempting to connect to Tello...")

try:
    tello.connect(wait_for_state=False)
    print("Connected.")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

tello.streamon()
print("Stream started, waiting for frames...")
time.sleep(3)  # 待機時間を増やす

# OpenCVで直接UDPストリームをキャプチャ
cap = cv2.VideoCapture('udp://0.0.0.0:11111', cv2.CAP_FFMPEG)

# FFMPEGオプションを設定してエラーを減らす
cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
cap.set(cv2.CAP_PROP_FPS, 30)

print("Waiting for video stream...")

try:
    frame_count = 0
    no_frame_count = 0
    skip_frames = 5  # 最初の数フレームをスキップ
    
    while True:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            no_frame_count += 1
            if no_frame_count % 10 == 0:
                print(f"Waiting for frame... ({no_frame_count})")
            if no_frame_count > 100:
                print("Too many failed attempts. Exiting.")
                break
            time.sleep(0.1)
            continue
        
        no_frame_count = 0
        frame_count += 1
        
        # 最初の数フレームをスキップ(初期化中)
        if frame_count <= skip_frames:
            continue
            
        if frame_count == skip_frames + 1:
            print("Video stream stabilized! Press 'q' to quit.")
        
        # リサイズして表示
        frame = cv2.resize(frame, (640, 480))
        cv2.imshow("Tello Camera", frame)
        
        # qキーで終了
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    tello.streamoff()
    tello.end()
    print("Cleanup completed.")


"""
| ライブラリ名            | 用途                     | インストール方法                    |
| ----------------- | ---------------------- | --------------------------- |
| **djitellopy**    | Telloの制御(離陸・着陸・映像取得など) | `pip install djitellopy`    |
| **opencv-python** | 映像処理、色認識(HSV変換やマスク処理)  | `pip install opencv-python` |
| **numpy**         | 画像データ処理、配列計算           | `pip install numpy`         |
"""