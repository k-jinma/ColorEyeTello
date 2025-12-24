from djitellopy import Tello
import cv2
import numpy as np
import time
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def put_japanese_text(img, text, position, font_size=20, color=(255, 255, 255)):
    """
    OpenCV画像に日本語テキストを描画
    """
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", font_size)
                except:
                    font = ImageFont.load_default()
    
    color_rgb = (color[2], color[1], color[0])
    draw.text(position, text, font=font, fill=color_rgb)
    
    img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return img_bgr
# ローカルのXMLファイルパス
cascade_file = 'haarcascade_frontalface_default.xml'

# ローカルにファイルがない場合はダウンロード
if not os.path.exists(cascade_file):
    print("Downloading Haar Cascade file...")
    url = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'
    try:
        urllib.request.urlretrieve(url, cascade_file)
        print(f"Downloaded: {cascade_file}")
    except Exception as e:
        print(f"Failed to download: {e}")
        exit(1)

# 分類器を読み込み
face_cascade = cv2.CascadeClassifier(cascade_file)

# 分類器が正しく読み込まれたか確認
if face_cascade.empty():
    print(f"Error: Failed to load cascade classifier from {cascade_file}")
    print("Please check the XML file.")
    exit(1)
else:
    print(f"Successfully loaded cascade from {cascade_file}")

# Telloに接続
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
time.sleep(3)

# OpenCVで直接UDPストリームをキャプチャ
cap = cv2.VideoCapture('udp://0.0.0.0:11111', cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
cap.set(cv2.CAP_PROP_FPS, 30)

print("Waiting for video stream... (Detecting faces)")

try:
    frame_count = 0
    no_frame_count = 0
    skip_frames = 5
    
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
        
        if frame_count <= skip_frames:
            continue
            
        if frame_count == skip_frames + 1:
            print("Video stream stabilized! Detecting faces...")
            print("Press 'q' to quit.")
        
        # リサイズ
        frame = cv2.resize(frame, (640, 480))
        
        # グレースケールに変換（顔検出のため）
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 顔を検出
        # scaleFactor: 画像スケールの縮小率（1.1が一般的）
        # minNeighbors: 検出の信頼度（値が大きいほど厳密）
        # minSize: 検出する顔の最小サイズ
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # 検出された顔の数
        face_count = len(faces)
        
        # 各顔に対して処理
        for (x, y, w, h) in faces:
            # 顔の周りに矩形を描画
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # 顔の中心点を計算
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # 顔のサイズ情報を表示
            frame = put_japanese_text(frame, f"顔: {w}x{h}px", 
                                     (x, y - 10),
                                     font_size=18, color=(0, 255, 0))
        
        # 検出結果をフレームに表示
        frame = put_japanese_text(frame, f"検出された顔: {face_count}個", 
                                 (10, 10),
                                 font_size=22, color=(0, 255, 255))
        
        # 映像を表示
        cv2.imshow("Tello Camera - Face Detection", frame)
        
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
顔検出の設定:
- scaleFactor: 1.1〜1.3（小さいほど精度向上、処理は重くなる）
- minNeighbors: 3〜6（大きいほど誤検出減少、検出漏れ増加）
- minSize: 検出する最小顔サイズ（デフォルト30x30ピクセル）

調整方法:
- 検出漏れが多い → minNeighborsを小さく、scaleFactor を小さく
- 誤検出が多い → minNeighborsを大きく
- 遠くの顔を検出したい → minSizeを小さく
"""
