from json import load, dump
from subprocess import run
from time import sleep

from screen_objects import device_config, run_adb

from src.paths import INSTANCES_PATH, REDROID_DIR #, WAO_APK_PATH

with open(INSTANCES_PATH, "r", encoding="utf-8") as f:
    data = load(f)

i = 0
while f"wao-{i}" in data:
  i += 1

instance_name = f"wao-{i}"
adb_port = 5555 + i
serial = f"127.0.0.1:{adb_port}"
data_dir = REDROID_DIR / instance_name / "data"

print(f"Starting instance: {instance_name}")
print(f"ADB Port: {serial}")
print(f"Data directory: {data_dir}")

docker_cmd = [
    "docker",
    "run",
    "-itd",
    "--privileged",
    "--name",
    instance_name,
    "--security-opt",
    "label=disable",
    "--shm-size=512m",
    "-p",
    f"{adb_port}:5555",
    "-v",
    f"{data_dir}:/data",
    "whojk/redroid:12.0.0_mindthegapps_ndk",
    "androidboot.redroid_width=720",
    "androidboot.redroid_height=1280",
    "androidboot.redroid_dpi=320",
    "androidboot.redroid_fps=15",
    "androidboot.use_memfd=true",
    "androidboot.redroid_gpu_mode=host",
    "androidboot.redroid_gpu_node=/dev/dri/renderD128",
    "ro.product.cpu.abilist=x86_64,arm64-v8a,x86,armeabi-v7a,armeabi",
    "ro.product.cpu.abilist64=x86_64,arm64-v8a",
    "ro.product.cpu.abilist32=x86,armeabi-v7a,armeabi",
    "ro.dalvik.vm.isa.arm=x86",
    "ro.dalvik.vm.isa.arm64=x86_64",
    "ro.enable.native.bridge.exec=1",
    "ro.dalvik.vm.native.bridge=libndk_translation.so",
    "ro.ndk_translation.version=0.2.3",
    "ro.vendor.enable.native.bridge.exec=1",
    "ro.vendor.enable.native.bridge.exec64=1",
    "debug.sf.hw=1",
    "dalvik.vm.heapgrowthlimit=512m",
    "dalvik.vm.heapsize=1024m",
    "ro.product.brand=google",
    "ro.product.manufacturer=Google",
    "ro.product.model=Pixel 5",
]

run(docker_cmd).check_returncode()

sleep(1)
device_config(serial=serial)


run_adb(["shell", "pm", "disable-user", "--user", "0", "com.google.android.setupwizard"], check=True)
run_adb(["shell", "pm", "disable-user", "--user", "0", "com.google.android.provision"], check=True)

run_adb(["shell", "settings", "put", "global", "device_provisioned", "1"], check=True)
run_adb(["shell", "settings", "put", "secure", "user_setup_complete", "1"], check=True)



run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "market://details?id=com.camelgames.superking"], check=True)
# code, _, err = run_adb(["adb", "-s", serial, "install", WAO_APK_PATH])

data[instance_name] = serial
with open(INSTANCES_PATH, "w", encoding="utf-8") as f:
    dump(data, f, indent=2)

print("-" * 50)
print(f"Successfully created instance: {instance_name}, assigned to {serial}")
