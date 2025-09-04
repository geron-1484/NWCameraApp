"""
NetworkCamera 親クラス
"""
from dataclasses import dataclass
from typing import Optional, List
from onvif import ONVIFCamera
import requests
from requests.auth import HTTPDigestAuth
import os


@dataclass
class CameraProfile:
    token: str
    name: str


class NetworkCamera:
    def __init__(
        self,
        host: str,
        port: int = 80,
        username: Optional[str] = None,
        password: Optional[str] = None,
        wsdl_dir: Optional[str] = None,
        device_service_path: str = "/onvif/device_service",
        request_timeout: float = 5.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.wsdl_dir = wsdl_dir
        self.device_service_path = device_service_path
        self.request_timeout = request_timeout

        self._dev = None
        self._media = None
        self._ptz = None
        self._profiles: List[CameraProfile] = []
        self._active_profile: Optional[CameraProfile] = None

    def connect(self) -> None:
        url = self._device_service_url()
        self._dev = ONVIFCamera(
            host=self.host,
            port=self.port,
            user=self.username,
            passwd=self.password,
            wsdl_dir=self.wsdl_dir,
            trans_protocol="HTTP",
            path=url,
        )
        self._media = self._dev.create_media_service()
        self._ptz = self._dev.create_ptz_service()

        self._profiles = []
        for p in self._media.GetProfiles():
            self._profiles.append(CameraProfile(token=p.token, name=getattr(p, "Name", p.token)))

        if self._profiles:
            self._active_profile = self._profiles[0]

    def disconnect(self) -> None:
        self._dev = None
        self._media = None
        self._ptz = None
        self._profiles = []
        self._active_profile = None

    def get_snapshot_uri(self, profile: Optional[CameraProfile] = None) -> str:
        self._ensure_media()
        prof = profile or self._require_active_profile()
        uri = self._media.GetSnapshotUri({"ProfileToken": prof.token}).Uri
        return uri

    def save_snapshot(self, filepath: str, profile: Optional[CameraProfile] = None) -> str:
        uri = self.get_snapshot_uri(profile)
        auth = None
        if self.username and self.password:
            auth = HTTPDigestAuth(self.username, self.password)

        resp = requests.get(uri, auth=auth, timeout=self.request_timeout, stream=True)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return filepath

    def ptz_absolute(
        self,
        pan: float,
        tilt: float,
        zoom: Optional[float] = None,
        spd_pan: float = 0.5,
        spd_tilt: float = 0.5,
        spd_zoom: float = 0.5,
        profile: Optional[CameraProfile] = None,
    ) -> None:
        self._ensure_ptz()
        prof = profile or self._require_active_profile()

        req = self._ptz.create_type("AbsoluteMove")
        req.ProfileToken = prof.token
        req.Position = {"PanTilt": {"x": pan, "y": tilt}}
        if zoom is not None:
            req.Position["Zoom"] = {"x": zoom}
        req.Speed = {"PanTilt": {"x": spd_pan, "y": spd_tilt}, "Zoom": {"x": spd_zoom}}
        self._ptz.AbsoluteMove(req)

    def get_current_ptz_position(self):
        """
        現在のPTZ位置を取得（正規化座標 -1〜1）
        """
        self._ensure_ptz()
        prof = self._require_active_profile()
        status = self._ptz.GetStatus({"ProfileToken": prof.token})
        pos = status.Position
        pan = pos.PanTilt.x
        tilt = pos.PanTilt.y
        zoom = pos.Zoom.x if hasattr(pos, "Zoom") else None
        return pan, tilt, zoom

    def _device_service_url(self) -> str:
        if self.device_service_path.startswith("http"):
            return self.device_service_path
        return f"http://{self.host}:{self.port}{self.device_service_path}"

    def _require_active_profile(self) -> CameraProfile:
        if not self._active_profile:
            raise RuntimeError("No active profile selected.")
        return self._active_profile

    def _ensure_media(self) -> None:
        if self._media is None:
            raise RuntimeError("Not connected. Call connect() first.")

    def _ensure_ptz(self) -> None:
        if self._ptz is None:
            raise RuntimeError("Not connected or PTZ not available. Call connect() first.")
