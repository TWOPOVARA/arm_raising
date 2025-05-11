from PyInstaller.utils.hooks import collect_data_files
import os

datas = collect_data_files('mediapipe', includes=['**/*.binarypb', '**/*.tflite'])

block_cipher = None

a = Analysis(
    ['arm_player_gui.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'mediapipe.python.solutions.pose',
        'mediapipe.modules.pose_landmark',
        'mediapipe.modules.pose_detection',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ArmAudioApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='ArmAudioApp'
)

app = BUNDLE(
    coll,
    name='ArmAudioApp.app',
    icon=None,
    bundle_identifier='com.yourname.armaudioapp',
    info_plist={
        'NSCameraUsageDescription': 'This app needs access to your camera to detect your arm movement.',
    }
)