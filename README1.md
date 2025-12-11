# ColorEyeTello

Tello EDUドローンのカメラ映像をリアルタイムで表示するプログラムです。

## 必要なライブラリ

| ライブラリ名 | 用途 | インストール方法 |
|------------|------|----------------|
| **djitellopy** | Telloの制御(離陸・着陸・映像取得など) | `pip install djitellopy` |
| **opencv-python** | 映像処理、色認識(HSV変換やマスク処理) | `pip install opencv-python` |
| **numpy** | 画像データ処理、配列計算 | `pip install numpy` |

## セットアップ

### 1. 仮想環境の作成とアクティベート

#### Windows
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
pip install djitellopy opencv-python numpy
```

## ファイアウォール設定

### Windows

Telloからの映像ストリーム(UDPポート11111)を受信するために、Windowsファイアウォールの設定が必要です。

#### 方法1: PowerShellで設定(推奨)

**管理者権限でPowerShell**を開いて以下を実行:

```powershell
New-NetFirewallRule -DisplayName "Tello Video Stream" -Direction Inbound -Protocol UDP -LocalPort 11111 -Action Allow
```

#### 方法2: Windows Defenderファイアウォールで手動設定

1. 「コントロールパネル」→「Windows Defenderファイアウォール」を開く
2. 「詳細設定」をクリック
3. 左側の「受信の規則」をクリック
4. 右側の「新しい規則」をクリック
5. 「ポート」を選択→「次へ」
6. 「UDP」を選択、「特定のローカルポート」に`11111`と入力→「次へ」
7. 「接続を許可する」を選択→「次へ」
8. すべてのプロファイルにチェック→「次へ」
9. 名前を「Tello Video Stream」と入力→「完了」

### macOS

macOSでは通常、ファイアウォール設定は不要ですが、有効にしている場合は以下を確認:

1. 「システム環境設定」→「セキュリティとプライバシー」→「ファイアウォール」
2. 「ファイアウォールオプション」をクリック
3. Pythonまたはターミナルアプリに対して「着信接続を許可」を設定

## 使い方

### 1. TelloのWiFiに接続

- Telloの電源を入れる(電源ボタン長押し)
- PCのWiFi設定から`TELLO-XXXXXX`のネットワークに接続
- パスワードは不要

### 2. プログラムの実行

```bash
python prog.py
```

### 3. 操作方法

- **映像表示**: プログラム実行後、別ウィンドウ「Tello Camera」が開き、リアルタイム映像が表示されます
- **終了**: `q`キーを押すか、`Ctrl+C`でプログラムを終了

## トラブルシューティング

### 映像が表示されない

#### 1. WiFi接続を確認

```cmd
# Windows
ipconfig

# macOS / Linux
ifconfig
```

IPアドレスが`192.168.10.xxx`になっているか確認してください。

#### 2. Telloへの接続をテスト

```cmd
# Windows/macOS/Linux
ping 192.168.10.1
```

応答があるか確認してください。

#### 3. ポートの使用状況を確認

```cmd
# Windows
netstat -ano | findstr :11111

# macOS / Linux
lsof -i :11111
```

他のプログラムが11111ポートを使用している場合は終了してください。

### H264デコードエラーが表示される

以下のようなエラーメッセージが表示されることがありますが、映像は正常に表示されます:

```
[h264 @ ...] non-existing PPS 0 referenced
[h264 @ ...] decode_slice_header error
```

これはTelloの映像ストリームでよくある現象で、映像表示には影響しません。

### "Did not receive a state packet from the Tello" エラー

このエラーが発生する場合:

1. TelloのWiFiに正しく接続されているか確認
2. 他のデバイスがTelloに接続していないか確認
3. Telloを再起動してみる(電源ボタン長押しでオフ→オン)

### PyAVのエラー (Error 10014)

WindowsでPyAVのエラーが発生する場合:

```bash
pip uninstall av -y
pip install av
```

それでも解決しない場合は、特定のバージョンをインストール:

```bash
pip install av==10.0.0
```

## プログラムの仕様

- **映像解像度**: 640x480ピクセル(元の映像からリサイズ)
- **フレームレート**: 約30fps
- **通信プロトコル**: 
  - コマンド送信: UDP 8889ポート
  - 映像受信: UDP 11111ポート
- **Tello IPアドレス**: 192.168.10.1

## 注意事項

- Telloは一度に1つのデバイスからしか操作できません
- バッテリー残量が少ない場合、映像が不安定になることがあります
- WiFiの電波状況により、映像が途切れることがあります
- プログラムを正常に終了しない場合、Telloへの接続が残ることがあります(Telloを再起動してください)

## 開発環境

- Python 3.8以上
- Windows 10/11, macOS 10.15以上
- DJI Tello / Tello EDU

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 参考リンク

- [djitellopy ドキュメント](https://djitellopy.readthedocs.io/)
- [OpenCV ドキュメント](https://docs.opencv.org/)
- [Tello SDK](https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf)
