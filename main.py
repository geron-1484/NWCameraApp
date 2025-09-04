from cameras.canon_vbh47 import CanonVBH47
from gui_click_ptz import CameraGUI

def main():
    cam = CanonVBH47(
        host="192.168.1.100",
        username="admin",
        password="pass"
    )
    cam.connect()

    root = tk.Tk()
    app = CameraGUI(root, cam, auto_refresh_after_click=True)
    root.mainloop()

    cam.disconnect()


if __name__ == "__main__":
    main()