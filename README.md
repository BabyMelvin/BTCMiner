# 理解工作量证明
工作量证明算法`PoW`表述了区块链中新区块是如何创建或者挖出来的。`PoW`的目的是寻找符合特定规则的数字。
对网络中任何人来说，从计算的角度上看，该数字必须**难以寻找，易于验证**。

###例子说明
不妨规定某整数x乘以另一个y的哈希必须以0结尾，也就是hash(x*y)=ac23...0
```python
#假设x=5
from hashlib import sha256
x=5
y=0 # we don't know what y should be yet...
while sha256(f'{x*y'.encode()).hexdigest()[-1]!="0":
    y+=1
print(f'The solution is y={y}')
```
解是`y=21`因为这样得到的结尾就是0:

比特币工作量算法叫做Hashcash.和上面很类似。矿工们争相求解这个算法以便创建新块。总体而言，难度大小取决于要字符串中寻找到多少特定字符。
矿工给出答案报酬就是在交易中得到比特币。而网络可以轻松验证答案。
