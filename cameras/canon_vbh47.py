"""
CanonVBH47 サブクラス
"""
from .network_camera import NetworkCamera
from .utils import pixel_to_pt_angle, hfov_vfov_from_zoom

class CanonVBH47(NetworkCamera):
    def move_to_image_point_auto(
        self,
        x: float,
        y: float,
        image_width: int,
        image_height: int
    ):
        """
        現在のPTZ位置とズームからHFOV/VFOVを計算し、
        画像上の座標にカメラを向ける
        """
        # 現在のPTZ位置（正規化座標）
        pan_norm, tilt_norm, zoom_norm = self.get_current_ptz_position()

        # ズーム値からHFOV/VFOVを取得
        hfov_deg, vfov_deg = hfov_vfov_from_zoom(zoom_norm or 0.0)

        # 正規化座標→度数（-1〜1 → -180〜180）
        current_pan_deg = pan_norm * 180.0
        current_tilt_deg = tilt_norm * 180.0

        # 座標→角度オフセット
        pan_offset, tilt_offset = pixel_to_pt_angle(
            x, y, image_width, image_height, hfov_deg, vfov_deg
        )

        target_pan_deg = current_pan_deg + pan_offset
        target_tilt_deg = current_tilt_deg + tilt_offset

        # 度→正規化座標
        def deg_to_norm(v_deg):
            return v_deg / 180.0

        self.ptz_absolute(
            pan=deg_to_norm(target_pan_deg),
            tilt=deg_to_norm(target_tilt_deg),
            zoom=zoom_norm
        )
