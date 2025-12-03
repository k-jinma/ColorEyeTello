from djitellopy import Tello
import cv2
import numpy as np
import time

def hex_to_rgb(hex_color):
    """HEXカラーコード(#RRGGBB)をRGBタプルに変換"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsv_range(rgb, hue_range=15, sat_range=100, val_range=100):
    """
    RGBカラーからHSV検出範囲を自動生成
    
    Parameters:
    - rgb: (R, G, B) タプル (0-255)
    - hue_range: 色相の許容範囲 (±度) デフォルト15度
    - sat_range: 彩度の下限値 (0-255) デフォルト100
    - val_range: 明度の下限値 (0-255) デフォルト100
    """
    # RGBをBGRに変換してからHSVへ
    bgr = np.uint8([[rgb[::-1]]])  # (B, G, R)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[0][0]
    
    h, s, v = hsv
    
    # HSV範囲を計算
    lower_h = max(0, h - hue_range)
    upper_h = min(180, h + hue_range)
    lower_s = max(0, sat_range)
    upper_s = 255
    lower_v = max(0, val_range)
    upper_v = 255
    
    # 赤色の特殊処理(Hが0または180付近)
    if h < hue_range or h > 180 - hue_range:
        return {
            'lower1': np.array([0, lower_s, lower_v]),
            'upper1': np.array([hue_range, upper_s, upper_v]),
            'lower2': np.array([180 - hue_range, lower_s, lower_v]),
            'upper2': np.array([180, upper_s, upper_v]),
            'is_red': True
        }
    else:
        return {
            'lower': np.array([lower_h, lower_s, lower_v]),
            'upper': np.array([upper_h, upper_s, upper_v]),
            'is_red': False
        }

# ========== 色検出の設定 ==========

# 方法1: HEXカラーコードで指定(推奨)
TARGET_COLOR_HEX = "#FF0044"  # オレンジ色の例
# その他の例:
# "#FF0000"  # 赤
# "#00FF00"  # 緑
# "#0000FF"  # 青
# "#FFFF00"  # 黄色
# "#FFA500"  # オレンジ
# "#800080"  # 紫
# "#FFC0CB"  # ピンク
# "#8B4513"  # 茶色

# 方法2: RGBで指定する場合
# TARGET_COLOR_RGB = (255, 140, 0)  # オレンジ色 (R, G, B)

# カラーコードからHSV範囲を生成
if 'TARGET_COLOR_HEX' in locals():
    rgb = hex_to_rgb(TARGET_COLOR_HEX)
    print(f"検出色: {TARGET_COLOR_HEX} (RGB: {rgb})")
else:
    rgb = TARGET_COLOR_RGB
    print(f"検出色: RGB{rgb}")

# HSV範囲を自動生成
# hue_range: 色相の許容範囲(大きいほど似た色も検出)
# sat_range: 彩度の最小値(小さいほど薄い色も検出)
# val_range: 明度の最小値(小さいほど暗い色も検出)
COLOR_RANGE = rgb_to_hsv_range(
    rgb, 
    hue_range=20,      # ±20度の色相範囲
    sat_range=80,      # 彩度80以上
    val_range=80       # 明度80以上
)

# 検出の閾値(ピクセル数)
MIN_AREA = 500  # この面積以上の色領域を検出

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

print(f"Waiting for video stream... (Detecting color {TARGET_COLOR_HEX})")

try:
    frame_count = 0
    no_frame_count = 0
    skip_frames = 5
    color_detected = False
    detection_count = 0  # 連続検出回数
    
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
            print(f"Video stream stabilized! Detecting color {TARGET_COLOR_HEX}...")
            print("Press 'q' to quit.")
        
        # リサイズ
        frame = cv2.resize(frame, (640, 480))
        
        # HSV色空間に変換
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 色の範囲でマスクを作成
        if COLOR_RANGE.get('is_red', False):
            # 赤色は2つの範囲が必要
            mask1 = cv2.inRange(hsv, COLOR_RANGE['lower1'], COLOR_RANGE['upper1'])
            mask2 = cv2.inRange(hsv, COLOR_RANGE['lower2'], COLOR_RANGE['upper2'])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, COLOR_RANGE['lower'], COLOR_RANGE['upper'])
        
        # ノイズ除去
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        # 輪郭検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # 色を検出したかチェック
        found = False
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > MIN_AREA:
                found = True
                # 輪郭を描画
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # 中心点を計算
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                
                # 面積を表示
                cv2.putText(frame, f"Area: {int(area)}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 連続して検出された場合のみ「見つけた」と表示
        if found:
            detection_count += 1
            if detection_count >= 3 and not color_detected:  # 3フレーム連続で検出
                print(f"★ 見つけた! ({TARGET_COLOR_HEX}色を検出)")
                color_detected = True
        else:
            if detection_count >= 3 and color_detected:
                print(f"  見失いました...")
            detection_count = 0
            color_detected = False
        
        # 検出状態を画面に表示
        status_text = f"Detecting {TARGET_COLOR_HEX}"
        if color_detected:
            status_text += " - FOUND!"
            cv2.putText(frame, "FOUND!", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        else:
            cv2.putText(frame, "Searching...", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # 元の映像とマスクを表示
        cv2.imshow("Tello Camera", frame)
        cv2.imshow("Color Mask", mask)
        
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
色検出の設定:
- TARGET_COLOR: 検出したい色('red', 'blue', 'green', 'yellow')
- MIN_AREA: 検出する最小面積(ピクセル数)
- HSV範囲: COLOR_RANGES辞書で各色の範囲を定義

HSV値の調整方法:
- H (色相): 0-180 (赤=0/180, 緑=60, 青=120)
- S (彩度): 0-255 (低いと白っぽい、高いと鮮やか)
- V (明度): 0-255 (低いと暗い、高いと明るい)
"""