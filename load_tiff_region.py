import matplotlib.pyplot as plt
import numpy as np
import tifffile
import zarr

path = '/n/files/HiTS/lsp-analysis/cycif-production/133-abval/p133e53/LSP13004/registration/LSP13004.ome.tif'

print ('Loading image metadata...')
pyramid = zarr.open(tifffile.imread(path, aszarr=True))
zimg = pyramid[0]
c, h, w = zimg.shape
print('Image details:')
print(f'  dimensions: W={w} H={h} C={c}')
print(f'  pyramid levels: {len(pyramid)}')

channels = [0, 3, 7]
window = 2048
x1 = w // 2 - window // 2
y1 = h // 2 - window // 2
x2 = x1 + window
y2 = y1 + window
print('Loading image crop...')
crop = zimg[channels, y1:y2, x1:x2]

print('Displaying crop')
vmin, vmax = np.percentile(crop, [1, 99], axis=[1, 2])[:, :, None, None]
plt.imshow(np.clip((crop - vmin) / (vmax - vmin), 0, 1).transpose(1, 2, 0))
plt.show()
