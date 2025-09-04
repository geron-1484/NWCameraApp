import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os
from cameras.canon_vbh47 import CanonVBH47
from cameras.utils import pixel_to_pt_angle, hfov_vfov_from_zoom

SNAPSHOT_PATH = "snapshots/gui_snapshot.jpg"

class CameraGUI:
    def __init__(self, master, camera: CanonVBH47, auto_refresh_after_click=True):
        self.master = master
        self.cam = camera
        self.image_label = None
        self.tk_img = None
        self.marker_pos = None
        self.auto_refresh_after_click = auto_refresh_after_click

        self.master.title("クリックでPTZ制御 - Canon VB-H47")
        self.frame = tk.Frame(self.master)
        self.frame.pack()

        self.refresh_btn = tk.Button(self.frame, text="更新", command=self.update_snapshot)
        self.refresh_btn.pack()

        self.image_label = tk.Label(self.frame)
        self.image_label.pack()
        self.image_label.bind("<Button-1>", self.on_click)

        self.update_snapshot()

    def update_snapshot(self):
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        self.cam.save_snapshot(SNAPSHOT_PATH)
        self.marker_pos = None
        self.display_image(SNAPSHOT_PATH)
        print(f"Snapshot updated: {self.image_width}x{self.image_height}")

    def display_image(self, path):
        img = Image.open(path)
        self.image_width, self.image_height = img.size

        if self.marker_pos:
            draw = ImageDraw.Draw(img)
            x, y = self.marker_pos
            marker_size = 10
            color = (255, 0, 0)
            draw.line((x - marker_size, y, x + marker_size, y), fill=color, width=2)
            draw.line((x, y - marker_size, x, y + marker_size), fill=color, width=2)

        self.tk_img = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.tk_img)

    def on_click(self, event):
        self.marker_pos = (event.x, event.y)
        print(f"Clicked at: {self.marker_pos}")
        self.display_image(SNAPSHOT_PATH)

        # 現在のPTZ位置とズーム取得
        pan_norm, tilt_norm, zoom_norm = self.cam.get_current_ptz_position()
        hfov_deg, vfov_deg = hfov_vfov_from_zoom(zoom_norm or 0.0)
        current_pan_deg = pan_norm * 180.0
        current_tilt_deg = tilt_norm * 180.0

        # クリック座標からターゲット角度計算
        pan_offset, tilt_offset = pixel_to_pt_angle(
            event.x, event.y, self.image_width, self.image_height, hfov_deg, vfov_deg
        )
        target_pan_deg = current_pan_deg + pan_offset
        target_tilt_deg = current_tilt_deg + tilt_offset

        # カメラ移動
        self.cam.ptz_absolute(
            pan=target_pan_deg / 180.0,
            tilt=target_tilt_deg / 180.0,
            zoom=zoom_norm
        )
        print("Camera moved to clicked point.")

        # 移動距離に応じて待ち時間を計算
        distance_deg = ((pan_offset) ** 2 + (tilt_offset) ** 2) ** 0.5
        wait_time_ms = int(min(max(distance_deg * 50, 1000), 3000))  # 1°=50ms, 最低1秒, 最大3秒
        print(f"Waiting {wait_time_ms} ms before auto-refresh.")

        if self.auto_refresh_after_click:
            self.master.after(wait_time_ms, self.refresh_with_marker)

    def refresh_with_marker(self):
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        self.cam.save_snapshot(SNAPSHOT_PATH)
        print("Auto-refreshed snapshot after movement.")
        self.display_image(SNAPSHOT_PATH)

