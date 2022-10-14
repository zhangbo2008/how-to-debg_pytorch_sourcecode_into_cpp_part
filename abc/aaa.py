import torch

import time

x = torch.Tensor(5, 3)
y = torch.Tensor(5, 3)

start = time.time()
res_1 = x + y
print(": \n",res_1)
print(":")
print( time.time() - start)
