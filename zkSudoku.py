
import numpy as np
import json
import gzip
from hashUtils import hashObject, str_to_int
from Commitment import CommitmentValues
from interactiveSudoku import secretGrid, makeManyHiddenSudokus, checkDigits


def makeProofOfWork(commitsRoot, nonce):
    return hashObject(str(commitsRoot) + str(nonce))

def searchProofOfWork(commitsRoot):
    nonce = 0
    while makeProofOfWork(commitsRoot, nonce) < difficulty:
        nonce += 1
    return nonce

def makeChallenges(commitsRoot, PoW):
    seed = str_to_int(hashObject(str(commitsRoot) + PoW)) % 2**32
    rd = np.random.RandomState(seed)
    #选择一条线、一列和一个块来挑战
    return rd.randint(27, size=nChallenges)

def getResponse(grid, challenge):
    cType = challenge // 9
    cChoice = challenge % 9
    if cType == 0: return grid[cChoice, :]  # Row 行
    if cType == 1: return grid[:, cChoice]  # Column 列
    if cType == 2:                          # Block块
        y = (cChoice // 3) * 3
        x = (cChoice % 3) * 3
        return grid[y:y+3, x:x+3].flatten()


def getSquareIds(gridI, challenge):
    gridOffset = gridI * idGrid.size
    idsInGrid = getResponse(idGrid, challenges[gridI])
    return idsInGrid + gridOffset

if __name__ == "__main__":

  nChallenges = 256           #  交互协议的安全系数
  difficulty4bits = 16//4     #  具有工作证明的额外安全系数（以4位为增量）

  #第一阶段:数独产生及变换并作出整体承诺
  keys, grids = makeManyHiddenSudokus(secretGrid, nChallenges)
  committer = CommitmentValues(nbits=4)
  commitsRoot = committer.commitValues(grids.flatten())

  #第二阶段: 工作量证明
  difficulty = "f" * difficulty4bits
  print("Proof-of-work difficulty:", len(difficulty) * 4, "bits")
  nonce = searchProofOfWork(commitsRoot)



  #第三阶段：从承诺和工作证明中得出伪随机挑战。

  PoW = makeProofOfWork(commitsRoot, nonce)
  assert PoW >= difficulty
  #从随机数据中获取挑战
  challenges = makeChallenges(commitsRoot, PoW)


  #第四阶段：作出承诺·
  responses = np.zeros((nChallenges,  9), dtype=int)
  idGrid = np.arange(9 * 9).reshape(9, 9)
  responseIds = []
  #收集所有挑战的答案和索引
  for gridI in range(len(challenges)):
    challenge = challenges[gridI]
    response = getResponse(grids[gridI], challenge)
    responses[gridI] = response
    responseIds.extend(getSquareIds(gridI, challenge))

  assert len(responseIds) == len(set(responseIds)) == responses.size

  proofOfCommitment = committer.proveValues(responseIds)


  #第五阶段：把证据打包成一条信息

  proof = {
    "commitment to set": commitsRoot,
    "proof-of-work nonce": nonce,
    "responses to challenges": responses.tolist(),
    "proof that responses were committed": proofOfCommitment,
    "nBits": committer.nbits,
     }
  serializedProof = gzip.compress(json.dumps(proof).encode("utf8"))
  print("Proof size: %.0fK for %i challenges." % (len(serializedProof) / 1024, nChallenges))

  v_proof = json.loads(gzip.decompress(serializedProof).decode("utf8"))
  assert v_proof == proof


  #阶段6：验证
  v_commitsRoot = v_proof["commitment to set"]
  v_PoW = makeProofOfWork(v_commitsRoot, v_proof["proof-of-work nonce"])
  assert v_PoW >= difficulty, "Too little difficulty."

  #重新计算PoW数据带来的挑战
  v_challenges = makeChallenges(v_commitsRoot, v_PoW)
  assert len(v_challenges) >= nChallenges, "Too few challenges."

  v_responses = v_proof["responses to challenges"]
  assert len(v_challenges) == len(v_responses)

  v_responseValues = np.array(v_responses).flatten()
  v_responseIds = []

  for gridI in range(len(v_challenges)):
    challenge = v_challenges[gridI]
    response = v_responses[gridI]
    v_responseIds.extend(getSquareIds(gridI, challenge))
    # 验证解决方案是否来自有效的数独游戏：
    # *每组必须全部为1-9位数。
    # *或者，检查拼图约束（在这种情况下，它也是1-9位数）。
    assert checkDigits(np.array(response) - 1), "The response is not a valid solution."

  v_committer = CommitmentValues(nbits=v_proof["nBits"])
  v_proofOfResponse = v_proof["proof that responses were committed"]
  v_wasCommitted = v_committer.verifyValues(v_responseIds, v_responseValues, v_proofOfResponse, v_commitsRoot)
  assert v_wasCommitted, "The responses are not all included in the commitment."

  print("Proof verified!")

