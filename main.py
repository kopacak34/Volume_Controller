import serial
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import POINTER, cast
import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
from PIL import Image, ImageDraw
import pystray
import threading
import time

running = False
volume_labels = {}
master_label = None
pot_mapping = {}
app_sessions = {}
master_volume = None
stop_event = threading.Event()

# Ziskani aktivnich aplikaci
def get_running_audio_apps():
    sessions = AudioUtilities.GetAllSessions()
    apps = []
    for session in sessions:
        if session.Process:
            apps.append(session.Process.name())
    return sorted(set(apps))

# Hlavní logika ovládání hlasitosti

def volume_loop():
    global running
    while not stop_event.is_set():
        if running and arduino.in_waiting > 0:
            data = arduino.readline().decode('utf-8').strip()
            try:
                pot1, pot2, pot3, pot4 = map(int, data.split(","))
                volumes = [pot1, pot2, pot3]

                sessions = AudioUtilities.GetAllSessions()
                for i, pot in enumerate(["pot1", "pot2", "pot3"]):
                    app_name = pot_mapping.get(pot)
                    for session in sessions:
                        if session.Process and session.Process.name().lower() == app_name.lower():
                            try:
                                volume_control = session._ctl.QueryInterface(ISimpleAudioVolume)
                                volume_level = volumes[i] / 100.0
                                volume_control.SetMasterVolume(volume_level, None)
                            except Exception as e:
                                print(f"Chyba nastavovani hlasitosti pro {app_name}: {e}")

                master_volume_level = pot4 / 100.0
                try:
                    master_volume.SetMasterVolumeLevelScalar(master_volume_level, None)
                except Exception as e:
                    print(f"Chyba nastavovani master volume: {e}")
            except ValueError:
                print("Neplatna data z Arduina:", data)
        time.sleep(0.05)

# GUI aplikace

def configure_mapping():
    def update_comboboxes():
        current_apps = get_running_audio_apps()
        for cb in [selectbox1, selectbox2, selectbox3]:
            current_value = cb.get()
            cb['values'] = current_apps
            if current_value not in current_apps:
                cb.set('')
        window.after(5000, update_comboboxes)

    def update_volume_labels():
        for key, label in volume_labels.items():
            app_name = pot_mapping.get(key)
            if not app_name:
                label.config(text="Volume: ?")
                continue
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name() and session.Process.name().lower() == app_name.lower():
                    try:
                        volume = session._ctl.QueryInterface(ISimpleAudioVolume).GetMasterVolume() * 100
                        label.config(text=f"{app_name} Volume: {int(volume)}%")
                        break
                    except:
                        label.config(text=f"{app_name} Volume: ?")
        try:
            master = master_volume.GetMasterVolumeLevelScalar() * 100
            master_label.config(text=f"Master Volume: {int(master)}%")
        except:
            master_label.config(text="Master Volume: ?")
        window.after(1000, update_volume_labels)

    def save_config():
        pot_mapping["pot1"] = selectbox1.get()
        pot_mapping["pot2"] = selectbox2.get()
        pot_mapping["pot3"] = selectbox3.get()
        print("Konfigurace ulozena:", pot_mapping)

    def start_app():
        global running
        running = True
        print("Spusteno")

    def pause_app():
        global running
        running = False
        print("Pozastaveno")

    def quit_app():
        stop_event.set()
        if tray_icon:
            tray_icon.stop()
        window.destroy()

    def create_image():
        img = Image.new('RGB', (64, 64), color='black')
        d = ImageDraw.Draw(img)
        d.rectangle((10, 10, 54, 54), fill="green")
        return img

    def on_show(icon, item):
        window.after(0, window.deiconify)

    def on_hide():
        window.withdraw()

    global tray_icon
    tray_icon = pystray.Icon("VolumeApp", create_image(), "Volume Controller", menu=pystray.Menu(
        pystray.MenuItem("Zobrazit", on_show),
        pystray.MenuItem("Ukoncit", lambda icon, item: quit_app())
    ))
    threading.Thread(target=tray_icon.run, daemon=True).start()

    # === DESIGN ===
    window = tk.Tk()
    window.title("Volume Controller")
    window.geometry("420x500")
    window.configure(bg="#2b2b2b")
    window.protocol("WM_DELETE_WINDOW", on_hide)

    style = ttk.Style()
    style.theme_use("default")
    style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10), padding=6)
    style.configure("TCombobox", padding=5)

    def make_label(text):
        lbl = ttk.Label(window, text=text)
        lbl.pack(pady=5)
        return lbl

    def make_combobox():
        cb = ttk.Combobox(window, state="readonly", width=30)
        cb.pack(pady=2)
        return cb

    make_label("Potentiometer 1:")
    selectbox1 = make_combobox()

    make_label("Potentiometer 2:")
    selectbox2 = make_combobox()

    make_label("Potentiometer 3:")
    selectbox3 = make_combobox()

    ttk.Button(window, text="💾 Uložit konfiguraci", command=save_config).pack(pady=8)
    ttk.Button(window, text="▶️ Spustit", command=start_app).pack(pady=4)
    ttk.Button(window, text="⏸️ Pozastavit", command=pause_app).pack(pady=4)
    ttk.Button(window, text="❌ Ukončit aplikaci", command=quit_app).pack(pady=10)

    volume_labels["pot1"] = ttk.Label(window, text="Volume: ?")
    volume_labels["pot1"].pack(pady=2)
    volume_labels["pot2"] = ttk.Label(window, text="Volume: ?")
    volume_labels["pot2"].pack(pady=2)
    volume_labels["pot3"] = ttk.Label(window, text="Volume: ?")
    volume_labels["pot3"].pack(pady=2)

    global master_label
    master_label = ttk.Label(window, text="Master Volume: ?")
    master_label.pack(pady=10)

    update_comboboxes()
    update_volume_labels()
    window.mainloop()


# Inicializace Arduina

def najdi_arduino_port():
    porty = serial.tools.list_ports.comports()
    for port in porty:
        if "Arduino" in port.description or "CH340" in port.description:
            return port.device
    return None

arduino_port = najdi_arduino_port()

if arduino_port:
    arduino = serial.Serial(arduino_port, 9600)
    print(f"Arduino pripojeno na portu {arduino_port}")
else:
    print("Arduino nebylo nalezeno.")
    exit()  

# Inicializace master volume

device = AudioUtilities.GetSpeakers()
interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
master_volume = cast(interface, POINTER(IAudioEndpointVolume))

# Spustit hlavní GUI a smyčku v jiném vlákně
threading.Thread(target=volume_loop, daemon=True).start()
configure_mapping()
