from djitellopy import Tello
import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

def put_japanese_text(img, text, position, font_size=20, color=(255, 255, 255)):
    """
    OpenCV画像に日本語テキストを描画
    
    Parameters:
    - img: OpenCV画像 (numpy array)
    - text: 表示するテキスト
    - position: (x, y) 座標
    - font_size: フォントサイズ
    - color: BGR色
    """
    # OpenCV画像をPIL画像に変換
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # フォントを読み込み（Windowsの標準日本語フォント）
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", font_size)
        except:
            font = ImageFont.truetype("arial.ttf", font_size)
    
    # RGBに変換（PILはRGB）
    color_rgb = (color[2], color[1], color[0])
    draw.text(position, text, font=font, fill=color_rgb)
    
    # PIL画像をOpenCV画像に戻す
    img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return img_bgr

def detect_shape(contour):
    """
    輪郭から形状を判定する関数
    
    Returns:
    - shape: 形状名 ("circle", "triangle", "square", "rectangle", "pentagon", "polygon")
    - vertices: 頂点数
    """
    # 輪郭の周長を計算
    perimeter = cv2.arcLength(contour, True)
    # 輪郭を近似（頂点数を減らす）
    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
    
    vertices = len(approx)
    
    # 頂点数で形状を判定
    if vertices == 3:
        return "triangle", vertices
    elif vertices == 4:
        # 矩形の場合、正方形か長方形かを判定
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h
        if 0.95 <= aspect_ratio <= 1.05:
            return "square", vertices
        else:
            return "rectangle", vertices
    elif vertices == 5:
        return "pentagon", vertices
    elif vertices > 5:
        # 円形の判定（頂点が多い場合）
        area = cv2.contourArea(contour)
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity > 0.8:
            return "circle", vertices
        else:
            return "polygon", vertices
    else:
        return "unknown", vertices

# ========== 形状検出の設定 ==========

# 検出の閾値
MIN_AREA = 500  # この面積以上の領域を検出
CANNY_THRESHOLD1 = 50  # Cannyエッジ検出の閾値1
CANNY_THRESHOLD2 = 150  # Cannyエッジ検出の閾値2

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

print("Waiting for video stream... (Detecting shapes)")

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
            print("Video stream stabilized! Detecting shapes...")
            print("Press 'q' to quit.")
        
        # リサイズ
        frame = cv2.resize(frame, (640, 480))
        original = frame.copy()
        
        # グレースケールに変換
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # ガウシアンブラーでノイズ除去
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Cannyエッジ検出
        edges = cv2.Canny(blurred, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        
        # 輪郭検出
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        detected_shapes = {}  # {形状名: 個数}
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > MIN_AREA:
                # 形状を検出
                shape, vertices = detect_shape(contour)
                
                # 形状カウント
                if shape in detected_shapes:
                    detected_shapes[shape] += 1
                else:
                    detected_shapes[shape] = 1
                
                # 輪郭を描画
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                
                # バウンディングボックス
                x, y, w, h = cv2.boundingRect(contour)
                
                # 中心点を計算
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    center_x = int(M["m10"] / M["m00"])
                    center_y = int(M["m01"] / M["m00"])
                else:
                    center_x = x + w // 2
                    center_y = y + h // 2
                
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                
                # 形状名を日本語に変換
                shape_names = {
                    "circle": "円形",
                    "triangle": "三角形",
                    "square": "正方形",
                    "rectangle": "長方形",
                    "pentagon": "五角形",
                    "polygon": "多角形",
                    "unknown": "不明"
                }
                shape_jp = shape_names.get(shape, shape)
                
                # 日本語で形状名と頂点数を表示
                frame = put_japanese_text(frame, f"{shape_jp} ({vertices}頂点)", 
                                         (center_x - 40, center_y - 30),
                                         font_size=18, color=(255, 255, 0))
                frame = put_japanese_text(frame, f"面積: {int(area)}", 
                                         (center_x - 40, center_y - 5),
                                         font_size=16, color=(255, 255, 255))
        
        # 検出結果をフレームに日本語で表示
        frame = put_japanese_text(frame, "検出された形状:", (10, 10),
                                 font_size=22, color=(0, 255, 255))
        
        y_offset = 40
        shape_names = {
            "circle": "円形", "triangle": "三角形", "square": "正方形",
            "rectangle": "長方形", "pentagon": "五角形", 
            "polygon": "多角形", "unknown": "不明"
        }
        
        for shape, count in detected_shapes.items():
            shape_jp = shape_names.get(shape, shape)
            frame = put_japanese_text(frame, f"{shape_jp}: {count}個", (10, y_offset),
                                     font_size=18, color=(0, 255, 0))
            y_offset += 30
        
        # 元の映像、エッジ検出、結果を表示
        cv2.imshow("Tello Camera - Shape Detection", frame)
        cv2.imshow("Edges", edges)
        
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
形状検出の設定:
- MIN_AREA: 検出する最小面積(ピクセル数)
- CANNY_THRESHOLD1, CANNY_THRESHOLD2: エッジ検出の感度調整

検出可能な形状:
- 円形 (circle): 滑らかな曲線の物体
- 三角形 (triangle): 3つの頂点
- 正方形 (square): 4つの頂点で縦横比が1に近い
- 長方形 (rectangle): 4つの頂点で縦横比が1から離れている
- 五角形 (pentagon): 5つの頂点
- 多角形 (polygon): 6つ以上の頂点

調整方法:
- MIN_AREAを大きくすると小さい物体を無視
- CANNY_THRESHOLDを調整してエッジ検出の感度を変更
"""
