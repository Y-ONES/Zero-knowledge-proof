#生成一个秘密数独秘密网格
import os
import struct
import numpy as np


def checkDigits(block):
    return np.all(np.sort(block.flatten()) == r)

def assertIsSudoku(grid):
    for i in range(9):
        assert checkDigits(grid[i,:])
        assert checkDigits(grid[:,i])
    for i in range(3):
        for j in range(3):
            assert checkDigits(grid[3*i:3*i+3, 3*j:3*j+3])

#加密
#每轮重新重置，以减轻numpy随机的弱点。
def reseed():
    np.random.seed(struct.unpack("I", os.urandom(4))[0])

def makeHiddenSudoku(grid):
    reseed()
    #选择一个随机的数字映射
    key = np.random.permutation(r)
    #加密
    encrypted = key[grid]
    assertIsSudoku(encrypted)
    return key, encrypted

def makeManyHiddenSudokus(grid, nChallenges):
    keys  = np.zeros((nChallenges, 9), dtype=int)
    grids = np.zeros((nChallenges, 9, 9), dtype=int)

    for i in range(nChallenges):
        key, encrypted = makeHiddenSudoku(grid)
        #以1-9之间的数字存储
        keys[i] = key + 1
        grids[i] = encrypted + 1
    return keys, grids

secretGrid = np.zeros((9, 9), dtype=int)
r = np.arange(9)

# First group of 3 rows
secretGrid[0] = np.roll(r, 0)
secretGrid[1] = np.roll(r, -3)
secretGrid[2] = np.roll(r, -6)
# Second group of 3 rows
secretGrid[3:6] = np.roll(secretGrid[0:3], -1, axis=1)
# Third group of 3 rows
secretGrid[6:9] = np.roll(secretGrid[0:3], -2, axis=1)
assertIsSudoku(secretGrid)
print(secretGrid+1)

