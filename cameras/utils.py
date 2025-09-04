"""
座標→角度変換などの共通関数
"""
import math

def pixel_to_pt_angle(x, y, image_width, image_height, hfov_deg, vfov_deg):
    """
    画像座標から中心基準のパン・チルト角度オフセットを計算
    """
    cx = image_width / 2
    cy = image_height / 2
    dx = x - cx
    dy = cy - y  # 上方向を正にするため反転

    deg_per_px_x = hfov_deg / image_width
    deg_per_px_y = vfov_deg / image_height

    pan_offset = dx * deg_per_px_x
    tilt_offset = dy * deg_per_px_y

    return pan_offset, tilt_offset


def hfov_vfov_from_zoom(zoom_norm):
    """
    ズーム正規化値(0.0=ワイド端, 1.0=テレ端)からHFOV/VFOVを推定
    Canon VB-H47の仕様値を線形補間（例）
    ※ 実機の仕様書に合わせて値を調整してください
    """
    # ワイド端（zoom=0.0）の画角
    HFOV_wide = 61.2
    VFOV_wide = 37.0
    # テレ端（zoom=1.0）の画角
    HFOV_tele = 2.9
    VFOV_tele = 1.6

    hfov = HFOV_wide + (HFOV_tele - HFOV_wide) * zoom_norm
    vfov = VFOV_wide + (VFOV_tele - VFOV_wide) * zoom_norm
    return hfov, vfov
