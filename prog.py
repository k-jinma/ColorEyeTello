from djitellopy import Tello
import cv2

tello = Tello()
tello.connect(wait_for_state=False)
print("Connected (no state packet check).")

tello.streamon()

# OpenCVで直接受信
cap = cv2.VideoCapture("udp://@0.0.0.0:11111")

while True:
    ret, frame = cap.read()
    if not ret:
        print("No frame received...")
        continue
    frame = cv2.resize(frame, (480, 360))
    cv2.imshow("Tello Camera", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

tello.streamoff()
cap.release()
cv2.destroyAllWindows()




"""
| ライブラリ名            | 用途                     | インストール方法                    |
| ----------------- | ---------------------- | --------------------------- |
| **djitellopy**    | Telloの制御（離陸・着陸・映像取得など） | `pip install djitellopy`    |
| **opencv-python** | 映像処理、色認識（HSV変換やマスク処理）  | `pip install opencv-python` |
| **numpy**         | 画像データ処理、配列計算           | `pip install numpy`         |

"""