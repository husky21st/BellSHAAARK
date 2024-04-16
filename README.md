# Deep Monte-CarloによるUNO AI feat. RLCard
## 概要
NTT東日本主催のプログラミングコンテスト第一回に参加した時のUNO対戦プログラム
### 対戦ロジック
相手の手札が見えない不確定性の高いUNOという対戦ゲームにおいてDeep Monte-Carloによる強化学習を行い、手札と相手の枚数、出されたカードの状況から行動を決定する

参考にした論文はこちら
[DouZero: Mastering DouDizhu with Self-Play Deep Reinforcement Learning (arXiv, 2021)](https://arxiv.org/abs/2106.06135)

### 開発
強化学習フレームワークとゲーム環境は[RLCard](https://github.com/datamllab/rlcard)
(UNOの特殊ルールなどは自前で実装する必要がある)

#### モデルトレーニング
環境構築(>=3.8.6)
```
pip install -r requirements.txt
```
学習
```python
python src/run_dmc.py
```
