from djitellopy import Tello
import cv2
import numpy as np

# --- ドローン初期化 ---
tello = Tello()
tello.connect()
print("Battery:", tello.get_battery())

# --- 映像取得開始 ---
tello.streamon()
frame_read = tello.get_frame_read()

while True:
    frame = frame_read.frame
    frame = cv2.resize(frame, (480, 360))

    # --- HSV空間に変換 ---
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # --- 赤色の範囲を指定（例）---
    lower_red = np.array([0, 100, 100])
    upper_red = np.array([10, 255, 255])
    mask = cv2.inRange(hsv, lower_red, upper_red)

    # --- 検出部分を可視化 ---
    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("Tello Camera", frame)
    cv2.imshow("Red Detection", result)

    # --- qキーで終了 ---
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

tello.streamoff()
cv2.destroyAllWindows()



"""
| ライブラリ名            | 用途                     | インストール方法                    |
| ----------------- | ---------------------- | --------------------------- |
| **djitellopy**    | Telloの制御（離陸・着陸・映像取得など） | `pip install djitellopy`    |
| **opencv-python** | 映像処理、色認識（HSV変換やマスク処理）  | `pip install opencv-python` |
| **numpy**         | 画像データ処理、配列計算           | `pip install numpy`         |

"""