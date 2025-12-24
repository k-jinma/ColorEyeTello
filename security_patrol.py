from djitellopy import Tello
import cv2
import numpy as np
import time
import os
import urllib.request
from datetime import datetime
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
time.sleep(5)

# OpenCVで直接UDPストリームをキャプチャ
cap = cv2.VideoCapture('udp://0.0.0.0:11111', cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FPS, 30)

print("Opening video stream...")
time.sleep(2)

print("Waiting for video stream... (Security Patrol Mode)")

try:
    frame_count = 0
    no_frame_count = 0
    skip_frames = 10
    
    # 離陸とカメラのセットアップフラグ
    is_flying = False
    initial_rotation_done = False
    last_rotation_time = time.time()
    current_direction = 0
    intruder_detected = False
    
    # 連続検出カウンター
    consecutive_face_count = 0
    CONSECUTIVE_FRAMES_REQUIRED = 5
    
    # パトロール開始時刻を記録
    patrol_start_time = None
    MAX_PATROL_TIME = 60  # 最大パトロール時間（秒）- ストリーム安定性のため短縮
    
    while True:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            no_frame_count += 1
            if no_frame_count <= 30:  # 初期待機を短縮
                if no_frame_count % 10 == 0:
                    print(f"Waiting for stream to stabilize... ({no_frame_count})")
                time.sleep(0.2)
                continue
            elif no_frame_count > 60:  # より早く切断を検出
                print("\n[WARNING] Stream connection lost!")
                print(f"Lost frames: {no_frame_count}")
                if is_flying:
                    print("Emergency landing due to lost video stream...")
                    try:
                        tello.land()
                        time.sleep(3)
                    except:
                        pass
                break
            time.sleep(0.1)
            continue
        
        no_frame_count = 0
        frame_count += 1
        
        # 最初の数フレームはスキップ
        if frame_count <= skip_frames:
            continue
        
        if frame_count == skip_frames + 1:
            print("Video stream stabilized!")
            print("Starting security patrol...")
            print("Press 'q' to quit.")
            
            # バッテリー残量チェック
            try:
                battery = tello.get_battery()
                print(f"Battery level: {battery}%")
                if battery < 20:
                    print("WARNING: Battery too low (<20%). Aborting takeoff.")
                    break
            except Exception as e:
                print(f"Could not check battery: {e}")
            
            # 離陸
            print("Taking off...")
            try:
                tello.takeoff()
                print("Takeoff complete.")
                print("Waiting for IMU to stabilize...")
                time.sleep(5)
                is_flying = True
                patrol_start_time = time.time()
            except Exception as e:
                print(f"Takeoff failed: {e}")
                break
            
            # カメラを反対向きにセット
            print("Rotating 180 degrees (camera facing away from pilot)...")
            try:
                print("  Rotating 90 degrees...")
                tello.rotate_clockwise(90)
                time.sleep(3)
                print("  Rotating another 90 degrees...")
                tello.rotate_clockwise(90)
                time.sleep(3)
                current_direction = 180
                print("Initial rotation complete. Starting patrol...")
                initial_rotation_done = True
                last_rotation_time = time.time()
            except Exception as e:
                print(f"Rotation failed: {e}")
                print("Landing for safety...")
                tello.land()
                is_flying = False
                break
        
        # 最大パトロール時間チェック
        if patrol_start_time and (time.time() - patrol_start_time) > MAX_PATROL_TIME:
            print(f"\nMaximum patrol time ({MAX_PATROL_TIME}s) reached.")
            print("Landing...")
            if is_flying:
                tello.land()
                time.sleep(3)
            break
        
        # リサイズ
        frame = cv2.resize(frame, (640, 480))
        
        # グレースケールに変換
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 顔を検出
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=8,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # フィルタリング
        valid_faces = []
        for (x, y, w, h) in faces:
            aspect_ratio = w / float(h)
            if 0.75 <= aspect_ratio <= 1.3:
                if y < frame.shape[0] * 0.66:
                    valid_faces.append((x, y, w, h))
        
        faces = valid_faces
        face_count = len(faces)
        
        # 連続検出カウンター更新
        if face_count > 0:
            consecutive_face_count += 1
            if consecutive_face_count % 5 == 0:
                print(f"Face detected for {consecutive_face_count} consecutive frames...")
        else:
            consecutive_face_count = 0
        
        # 侵入者検知
        if consecutive_face_count >= CONSECUTIVE_FRAMES_REQUIRED and is_flying and not intruder_detected:
            intruder_detected = True
            print(f"\n!!! INTRUDER DETECTED !!! ({face_count} face(s) found)")
            print(f"Confirmed after {consecutive_face_count} consecutive detections")
            
            # 矩形描画
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 3)
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                frame = put_japanese_text(frame, f"侵入者: {w}x{h}px", 
                                         (x, y - 10),
                                         font_size=18, color=(0, 0, 255))
            
            # 警告表示
            frame = put_japanese_text(frame, f"!!! 侵入者検出 !!! {face_count}人", 
                                     (10, 10),
                                     font_size=28, color=(0, 0, 255))
            
            # 写真保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intruder_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Photo saved: {filename}")
            
            # 着陸
            print("Landing immediately...")
            try:
                tello.land()
                time.sleep(3)
                print("Landing complete.")
            except:
                pass
            break
        
        # パトロールモード: 5秒ごとに90度回転
        if is_flying and initial_rotation_done and not intruder_detected:
            current_time = time.time()
            elapsed = current_time - last_rotation_time
            
            if elapsed >= 5.0:
                print(f"Rotating 90 degrees clockwise... (from {current_direction}°)")
                try:
                    tello.rotate_clockwise(90)
                    current_direction = (current_direction + 90) % 360
                    print(f"Now facing {current_direction}° direction")
                    last_rotation_time = current_time
                    time.sleep(2)
                except Exception as e:
                    print(f"Rotation error: {e}")
        
        # ステータスログ（60フレームごとに表示して処理負荷を軽減）
        if is_flying and frame_count % 60 == 0:
            elapsed_patrol = int(time.time() - patrol_start_time) if patrol_start_time else 0
            remaining = MAX_PATROL_TIME - elapsed_patrol
            status_text = f"Patrolling ({elapsed_patrol}s/{MAX_PATROL_TIME}s remaining: {remaining}s) | Direction: {current_direction}° | Detected: {consecutive_face_count} frames"
            print(status_text)
        
        # キー入力チェック
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            print("\nManual stop requested.")
            if is_flying:
                print("Landing...")
                try:
                    tello.land()
                    time.sleep(3)
                except:
                    pass
            break

except KeyboardInterrupt:
    print("\nStopping...")
    if is_flying:
        print("Emergency landing...")
        try:
            tello.land()
            time.sleep(3)
        except:
            pass

finally:
    try:
        cap.release()
    except:
        pass
    
    try:
        tello.streamoff()
    except:
        print("Stream already off or connection lost.")
    
    try:
        tello.end()
    except:
        pass
    
    print("Cleanup completed.")


"""
セキュリティパトロールモードの動作:
1. 離陸後、カメラをパイロットと反対方向（180度）に設定
2. 5秒ごとに90度ずつ時計回りに回転してパトロール
3. 顔を5フレーム連続で検出したら即座に着陸（侵入者検知）
4. 最大パトロール時間は120秒（安全のため）
5. qキーまたはEscキーで手動終了可能

改善点:
- ストリーム切断時の緊急着陸処理
- 最大パトロール時間の設定
- エラーハンドリングの強化
"""
