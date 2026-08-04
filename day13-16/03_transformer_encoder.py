"""
Day2-06 Transformer Encoder 完整实现
======================================
演示内容：
  1. 正弦位置编码 (Positional Encoding)
  2. EncoderLayer（多头注意力 + 前馈网络 + 残差连接 + 层归一化）
  3. TransformerEncoder（词嵌入 + 位置编码 + 多层 Encoder）
  4. 使用虚拟文本数据示例
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


# ============================================================
# 一、正弦位置编码 (Sinusoidal Positional Encoding)
# ============================================================

class PositionalEncoding(nn.Module):
    """
    使用正弦/余弦函数的位置编码，无需学习参数。

    PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

    优点：能外推到训练时未见过的序列长度。
    """

    def __init__(self, d_model, max_len=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # 预计算位置编码矩阵 (max_len, d_model)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float)
            * (-math.log(10000.0) / d_model)
        )

        # 偶数维度用 sin，奇数维度用 cos
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        # 增加 batch 维度: (1, max_len, d_model)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        """
        参数:
            x: (batch, seq_len, d_model) 词嵌入
        返回:
            (batch, seq_len, d_model) 加入位置编码后的表示
        """
        # 截取实际序列长度的位置编码
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


# ============================================================
# 二、前馈网络 (Feed-Forward Network)
# ============================================================

class PositionwiseFeedForward(nn.Module):
    """
    逐位置前馈网络：Linear -> ReLU -> Linear -> Dropout
    相当于在每个位置上独立应用同一个 MLP。
    """

    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # x: (batch, seq_len, d_model)
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


# ============================================================
# 三、多头注意力（复用精简版，完整版见 05_self_attention_impl.py）
# ============================================================

class MultiHeadAttention(nn.Module):
    """精简版多头注意力"""

    def __init__(self, d_model, head_count, dropout=0.1):
        super().__init__()
        assert d_model % head_count == 0
        self.d_model = d_model
        self.head_count = head_count
        self.d_k = d_model // head_count

        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def _split_heads(self, x, batch_size):
        return x.view(batch_size, -1, self.head_count, self.d_k).transpose(1, 2)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)
        Q = self._split_heads(self.w_q(query), batch_size)
        K = self._split_heads(self.w_k(key), batch_size)
        V = self._split_heads(self.w_v(value), batch_size)

        d_k = Q.size(-1)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        attn_weights = F.softmax(scores, dim=-1)
        attn_output = torch.matmul(attn_weights, V)

        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.w_o(attn_output)


# ============================================================
# 四、Encoder Layer
# ============================================================

class EncoderLayer(nn.Module):
    """
    Transformer 单个编码器层，包含：
      1. 多头自注意力 + 残差 + LayerNorm
      2. 前馈网络 + 残差 + LayerNorm
    """

    def __init__(self, d_model, head_count, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, head_count, dropout)
        self.feed_forward = PositionwiseFeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        """
        参数:
            x:    (batch, seq_len, d_model)
            mask: 可选掩码
        返回:
            (batch, seq_len, d_model)
        """
        # --- 子层 1: 多头自注意力 ---
        # Pre-LN 结构: Norm -> Attention -> Add -> Dropout
        residual = x
        x = self.norm1(x)
        attn_output = self.self_attn(x, x, x, mask)
        x = residual + self.dropout(attn_output)

        # --- 子层 2: 前馈网络 ---
        residual = x
        x = self.norm2(x)
        ff_output = self.feed_forward(x)
        x = residual + self.dropout(ff_output)

        return x


# ============================================================
# 五、完整 Transformer Encoder
# ============================================================

class TransformerEncoder(nn.Module):
    """
    完整的 Transformer 编码器栈：
      词嵌入 -> 位置编码 -> N 个 EncoderLayer -> 输出
    """

    def __init__(
        self,
        vocab_size,
        d_model=512,
        head_count=8,
        d_ff=2048,
        num_layers=6,
        max_len=5000,
        dropout=0.1,
        padding_idx=0,
    ):
        super().__init__()
        self.d_model = d_model

        # 词嵌入层，乘以 sqrt(d_model) 与位置编码量级对齐
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=padding_idx)
        self.positional_encoding = PositionalEncoding(d_model, max_len, dropout)

        # 堆叠多个 EncoderLayer
        self.layers = nn.ModuleList([
            EncoderLayer(d_model, head_count, d_ff, dropout)
            for _ in range(num_layers)
        ])
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(self, src, mask=None):
        """
        参数:
            src:  (batch, seq_len) 词索引
            mask: (batch, seq_len) 可选掩码
        返回:
            (batch, seq_len, d_model) 编码输出
        """
        # 1. 词嵌入并缩放
        x = self.embedding(src) * math.sqrt(self.d_model)

        # 2. 加入位置编码
        x = self.positional_encoding(x)

        # 3. 逐层编码
        for layer in self.layers:
            x = layer(x, mask)

        return self.layer_norm(x)


# ============================================================
# 六、示例用法
# ============================================================

if __name__ == "__main__":
    torch.manual_seed(42)

    # --- 示例 1: 位置编码可视化 ---
    print("=" * 50)
    print("示例 1: 位置编码")
    print("=" * 50)

    d_model = 128
    pos_enc = PositionalEncoding(d_model, max_len=100)
    dummy_pos = torch.zeros(1, 10, d_model)
    encoded = pos_enc(dummy_pos)

    print(f"  词嵌入维度 d_model = {d_model}")
    print(f"  输入形状: {dummy_pos.shape}")
    print(f"  输出形状: {encoded.shape}")

    # 查看前 3 个位置在维度 0,1 上的编码值
    print(f"\n  位置 0 的编码值 (前4维): {encoded[0, 0, :4].tolist()}")
    print(f"  位置 1 的编码值 (前4维): {encoded[0, 1, :4].tolist()}")
    print(f"  位置 2 的编码值 (前4维): {encoded[0, 2, :4].tolist()}")

    # --- 示例 2: 单个 EncoderLayer ---
    print("\n" + "=" * 50)
    print("示例 2: 单个 EncoderLayer")
    print("=" * 50)

    encoder_layer = EncoderLayer(d_model=128, head_count=4, d_ff=256)
    dummy_seq = torch.randn(2, 10, 128)  # (batch=2, seq_len=10, d_model=128)
    output = encoder_layer(dummy_seq)
    print(f"  输入形状: {dummy_seq.shape}")
    print(f"  输出形状: {output.shape}")

    # --- 示例 3: 完整 TransformerEncoder ---
    print("\n" + "=" * 50)
    print("示例 3: 完整 TransformerEncoder")
    print("=" * 50)

    # 配置参数（缩小版用于演示）
    vocab_size = 1000
    d_model = 64
    head_count = 4
    d_ff = 128
    num_layers = 3

    model = TransformerEncoder(
        vocab_size=vocab_size,
        d_model=d_model,
        head_count=head_count,
        d_ff=d_ff,
        num_layers=num_layers,
        dropout=0.1,
    )

    # 模拟一批输入（词索引）
    batch_size = 4
    seq_len = 8
    src = torch.randint(1, vocab_size, (batch_size, seq_len))
    print(f"  词表大小: {vocab_size}")
    print(f"  编码器层数: {num_layers}")
    print(f"  输入形状 (batch, seq_len): {src.shape}")

    output = model(src)
    print(f"  输出形状 (batch, seq_len, d_model): {output.shape}")

    # --- 示例 4: 带 padding 掩码 ---
    print("\n" + "=" * 50)
    print("示例 4: 带 Padding 掩码的处理")
    print("=" * 50)

    src = torch.tensor([
        [1, 2, 3, 4, 5, 0, 0, 0],  # 0 是 padding
        [6, 7, 8, 9, 10, 11, 12, 0],
    ])
    mask = (src != 0).unsqueeze(1).unsqueeze(2)  # (batch, 1, 1, seq_len)
    print(f"  输入: {src.shape}")
    print(f"  掩码: {mask.shape}")

    small_model = TransformerEncoder(
        vocab_size=100, d_model=64, head_count=4, d_ff=128, num_layers=2
    )
    output = small_model(src, mask=mask)
    print(f"  输出形状: {output.shape}")

    # 验证 padding 位置输出差异（有掩码 vs 无掩码）
    output_no_mask = small_model(src, mask=None)
    padding_diff = (output[0, 5] - output_no_mask[0, 5]).abs().mean().item()
    print(f"  Padding 位置输出差异均值: {padding_diff:.6f}")

    # --- 示例 5: 参数量统计 ---
    print("\n" + "=" * 50)
    print("示例 5: 模型参数量统计")
    print("=" * 50)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  总参数量: {total_params:,}")
    print(f"  可训练参数量: {trainable_params:,}")
    print(f"  模型大小约: {total_params * 4 / 1024:.1f} KB (FP32)")
