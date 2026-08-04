"""
Day2-05 Self-Attention 从零实现 
================================
练习目标：
  1. 掌握缩放点积注意力 (Scaled Dot-Product Attention) 的核心计算公式
  2. 理解多头注意力 (Multi-Head Attention) 的拆分与拼接机制
  3. 理解并实现 Decoder 中的因果掩码 (Causal Mask)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 一、缩放点积注意力
# ============================================================

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    计算缩放点积注意力。

    参数:
        Q:    Query 张量, 形状 (batch, heads, seq_len, d_k)
        K:    Key 张量,   形状 (batch, heads, seq_len, d_k)
        V:    Value 张量, 形状 (batch, heads, seq_len, d_v)
        mask: 可选掩码, 形状可广播到 (batch, heads, seq_len, seq_len)

    返回:
        output:     注意力输出, 形状同 V
        attn_weights: 注意力权重, 形状 (batch, heads, seq_len, seq_len)
    """
    d_k = Q.size(-1)

    # 1. 计算 Q 和 K 的点积并缩放
    # TODO: 计算 Q 和 K 的点积，并除以 math.sqrt(d_k) 进行缩放
    # 提示: K 需要进行转置以匹配矩阵乘法维度，可使用 K.transpose(-2, -1) 或 K.mT
    scores = torch.matmul(Q, K.mT) / math.sqrt(d_k)
    raise NotImplementedError("TODO 1: 请实现缩放点积的计算公式")

    # 2. 应用掩码（如有）
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))

    # 3. Softmax 归一化得到注意力权重
    # TODO: 沿最后一个维度 (dim=-1) 对 scores 应用 softmax 得到 attn_weights
    attn_weights = F.softmax(scores)
    raise NotImplementedError("TODO 2: 请实现 Softmax 归一化")

    # 4. 用权重加权求和 Value
    # TODO: 使用计算出的 attn_weights 对 V 进行加权求和（矩阵乘法）
    output = torch.matmul(attn_weights, V)
    raise NotImplementedError("TODO 3: 请实现对 V 的加权求和")

    return output, attn_weights


# ============================================================
# 二、多头注意力 (Multi-Head Attention)
# ============================================================

class MultiHeadAttention(nn.Module):
    """
    多头注意力模块。

    将 d_model 维空间拆成 head_count 个子空间，
    每个子空间独立做缩放点积注意力，最后拼接并线性变换。
    """

    def __init__(self, d_model=512, head_count=8, dropout=0.1):
        super().__init__()
        assert d_model % head_count == 0, "d_model 必须能被 head_count 整除"

        self.d_model = d_model
        self.head_count = head_count
        self.d_k = d_model // head_count  # 每个头的维度

        # TODO: 定义 Q, K, V 的线性投影层以及输出层
        # 提示: 使用 nn.Linear，输入和输出维度均为 d_model
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        raise NotImplementedError("TODO 4: 请定义多头注意力所需的线性映射层")

        self.dropout = nn.Dropout(dropout)

    def _split_heads(self, x, batch_size):
        """将最后一个维度拆成 (heads, d_k)"""
        # TODO: 将输入张量 x 的形状从 (batch, seq_len, d_model) 拆分成 (batch, heads, seq_len, d_k)
        # 提示: 1. 先用 view() 变成 (batch_size, -1, self.head_count, self.d_k)
        #       2. 再用 transpose(1, 2) 交换序列长度和头数的维度
        x = x.view(batch_size, -1, self.head_count, self.d_k)
        return x.transpose(1, 2)
        raise NotImplementedError("TODO 5: 请实现多头维度的拆分操作")

    def forward(self, query, key, value, mask=None):
        """
        参数:
            query: (batch, seq_len_q, d_model)
            key:   (batch, seq_len_k, d_model)
            value: (batch, seq_len_k, d_model)
            mask:  可选掩码

        返回:
            output:       (batch, seq_len_q, d_model)
            attn_weights: (batch, heads, seq_len_q, seq_len_k)
        """
        batch_size = query.size(0)

        # 1. 线性投影
        # TODO: 对 query, key, value 分别进行线性投影
        Q = self.w_q(query)
        K = self.w_k(key)
        V = self.w_v(value)
        raise NotImplementedError("TODO 6: 请完成前向传播中的线性投影步骤")

        # 2. 拆成多头
        Q = self._split_heads(Q, batch_size)
        K = self._split_heads(K, batch_size)
        V = self._split_heads(V, batch_size)

        # 3. 对每个头做缩放点积注意力
        # TODO: 调用上面实现的 scaled_dot_product_attention 函数计算注意力
        attn_output, attn_weights = scaled_dot_product_attention(Q, K, V, mask)
        raise NotImplementedError("TODO 7: 请调用缩放点积注意力函数")

        # 4. 拼接多头结果
        # TODO: 将多头结果拼接回 (batch, seq_len, d_model) 形状
        # 提示: 1. 先用 transpose(1, 2) 把头的维度换回去
        #       2. 使用 contiguous() 保证内存连续
        #       3. 用 view(batch_size, -1, self.d_model) 恢复成 d_model 维度
        attn_output = attn_output.transpose(1,2)
        attn_output = attn_output.contiguous()
        raise NotImplementedError("TODO 8: 请实现多头结果的拼接")

        # 5. 最终线性变换
        output = self.w_o(attn_output)
        output = self.dropout(output)

        return output, attn_weights


# ============================================================
# 三、注意力权重可视化 (已提供，无需修改)
# ============================================================

def visualize_attention(attn_weights, head_idx=0, sample_idx=0, tokens=None):
    """
    用颜色方块打印注意力权重热力图（纯文本版，不依赖 matplotlib）。
    """
    weights = attn_weights[sample_idx, head_idx].detach()
    seq_len = weights.size(0)

    if tokens is None:
        tokens = [f"Tok{i}" for i in range(seq_len)]

    print(f"\n=== 注意力权重热力图 (头 {head_idx}) ===")
    print("      " + " ".join(f"{t:>6s}" for t in tokens))

    for i in range(seq_len):
        row = ""
        for j in range(seq_len):
            w = weights[i, j].item()
            # 用 Unicode 方块表示权重大小
            bar_len = int(w * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            row += f" {bar}"
        print(f"{tokens[i]:>4s} {row}")


# ============================================================
# 四、验证与测试
# ============================================================

if __name__ == "__main__":
    torch.manual_seed(42)

    try:
        # --- 示例 1: 缩放点积注意力 ---
        print("=" * 50)
        print("测试 1: 缩放点积注意力")
        print("=" * 50)

        batch_size, seq_len, d_k = 2, 4, 8
        Q = torch.randn(batch_size, 1, seq_len, d_k)
        K = torch.randn(batch_size, 1, seq_len, d_k)
        V = torch.randn(batch_size, 1, seq_len, d_k)

        output, attn_weights = scaled_dot_product_attention(Q, K, V)
        print(f"  [成功] 注意力输出形状: {output.shape}")
        print(f"  [成功] 样本 0 的注意力权重:\n{attn_weights[0, 0]}")

        # --- 示例 2: 多头注意力 ---
        print("\n" + "=" * 50)
        print("测试 2: 多头注意力 (Multi-Head Attention)")
        print("=" * 50)

        d_model = 64
        head_count = 4
        seq_len = 6

        mha = MultiHeadAttention(d_model=d_model, head_count=head_count)
        dummy_input = torch.randn(2, seq_len, d_model)
        output, attn_weights = mha(dummy_input, dummy_input, dummy_input)

        print(f"  [成功] 多头注意力输出形状: {output.shape}")

        # --- 示例 3: 带掩码的注意力（模拟 Decoder 场景）---
        print("\n" + "=" * 50)
        print("测试 3: 带因果掩码的自注意力（Decoder 场景）")
        print("=" * 50)

        seq_len = 4
        # TODO: 创建一个下三角因果掩码矩阵
        # 提示: 使用 torch.ones(seq_len, seq_len) 创建全1矩阵，然后使用 torch.tril() 取下三角部分
        #       最后使用 unsqueeze(0).unsqueeze(0) 增加 batch 和 head 维度
        # causal_mask = ...
        raise NotImplementedError("TODO 9: 请创建下三角因果掩码")
        
        print("  因果掩码矩阵:\n", causal_mask[0, 0].int())

        masked_input = torch.randn(1, seq_len, d_model)
        masked_output, masked_attn = mha(masked_input, masked_input, masked_input, mask=causal_mask)
        
        print(f"  [成功] 被掩码位置权重示例 (位置 0 对位置 1): {masked_attn[0, 0, 0, 1]:.6f}")
        print("  [提示] 如果输出接近 0.000000，说明掩码生效！")

    except NotImplementedError as e:
        print(f"\n[待完成] {e}")
    except Exception as e:
        print(f"\n[运行出错] 代码存在错误: {e}")
