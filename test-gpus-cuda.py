import os
import six
import tensorflow as tf
import torch
import pynvml as nv

print("CUDA_VISIBLE_DEVICES=" + os.getenv('CUDA_VISIBLE_DEVICES', "<unset>"))
print()

print("NVML")
nv.nvmlInit()
gpu_count = nv.nvmlDeviceGetCount()
for i in range(gpu_count):
    handle = nv.nvmlDeviceGetHandleByIndex(i)
    print(f"device {i}:")
    try:
        name = six.ensure_str(nv.nvmlDeviceGetName(handle))
        memory = nv.nvmlDeviceGetMemoryInfo(handle)
        total = memory.total / 2 ** 30
        used = round(memory.used / memory.total * 100, 1)
        print(f"    NAME: {name}")
        print(f"    VRAM: {total} GB (used: {used}%)")
    except nv.NVMLError as e:
        print("   ", e)

print()
print("TENSORFLOW")
for i, d in enumerate(tf.config.list_logical_devices('GPU')):
    print(f"    device {i}: {d}")

print()
print("TORCH")
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print(f"    device {i}: {props.name} -- {props.uuid}")

print()
print("===========")
print()
print("Tensorflow execution test:")

for d in tf.config.list_logical_devices('GPU'):
    with tf.device(d):
        print(f"device {i}")
        a = tf.constant([1, 5, 2, 8])
        b = tf.constant([3, 2, 7, 4])
        m = tf.math.minimum(a, b)
        print("   ", m)
        print("   ", m.device)

print()
print("===========")
print()
print("Torch execution test:")

for i in range(torch.cuda.device_count()):
    with torch.device(f"cuda:{i}"):
        print(f"device {i}")
        print("    torch.cuda.current_device:", torch.cuda.current_device())
        a = torch.tensor([1, 5, 2, 8])
        b = torch.tensor([3, 2, 7, 4])
        m = torch.minimum(a, b)
        print("   ", m)
        print("   ", m.device)
