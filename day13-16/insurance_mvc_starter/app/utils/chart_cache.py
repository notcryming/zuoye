"""图表缓存：EDA/ML 可视化预渲染后的 base64 存放地

【目的】38 万行数据每次进入可视化界面都重新画图（hist/bar 聚合、matplotlib
中文字体初始化、png 编码、BytesIO 往返）很慢。把渲染好的 base64 存下来，
下次打开直接读取，秒出图。

【存储位置】instance/chart_cache/<namespace>.json
- namespace = eda：上传数据后预渲染的 4 张 EDA 图
- namespace = ml：模型训练完成后渲染的 4 张 ML 评估图（每个模型 + 对比图）
用 SQLite 旁边的 instance 目录（已 docker-compose 挂载为持久化卷），重启后仍在。

【失效策略】
- 上传 Excel 成功 → 清空并重建 eda 缓存（4 图），清空 ml 缓存（数据变了旧图无效）
- 训练完成 → 清空并重建 ml 缓存（ROC/混淆矩阵/特征重要性/指标对比）
- 无缓存或缓存损坏 → 可视化接口回退到实时渲染（保证功能不挂）

【key 格式】
- eda:  response_distribution | gender_response | age_distribution | premium_distribution
- ml:   roc_curve:<model_name> | confusion_matrix:<model_name> |
        feature_importance:<model_name> | metrics_comparison

【注意】纯文件读写 + json，不用 Redis/外部依赖，保持项目零新增依赖。
"""
import hashlib
import json
import os
import threading
import time
from app.core.config import settings

_LOCK = threading.Lock()

# ====================================================================
#  底层文件读写
# ====================================================================

def _cache_dir() -> str:
    """缓存根目录：instance/chart_cache（与 DB 文件同级，持久化）"""
    d = os.path.join("instance", "chart_cache")
    os.makedirs(d, exist_ok=True)
    return d


def _namespace_path(namespace: str) -> str:
    # 只保留安全字符，避免路径注入
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in namespace)
    return os.path.join(_cache_dir(), f"{safe}.json")


def _load_namespace(namespace: str) -> dict:
    path = _namespace_path(namespace)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 文件损坏直接清空重来，不阻塞主流程
        return {}


def _save_namespace(namespace: str, data: dict) -> None:
    path = _namespace_path(namespace)
    tmp = path + ".tmp"
    try:
        with _LOCK:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, path)
    except Exception:
        # 缓存写失败不影响主流程
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


# ====================================================================
#  对外 API：get / set / clear / invalidate_namespace
# ====================================================================

def get_cached_chart(namespace: str, key: str, max_age_seconds: float = None) -> str | None:
    """读缓存；命中且未过期（若指定 max_age_seconds）返回 base64，否则 None

    Args:
        namespace: eda / ml
        key:       具体图表标识
        max_age_seconds: 最大允许的缓存秒数（None = 不限，由业务事件触发失效）
    """
    ns = _load_namespace(namespace)
    entry = ns.get(key)
    if not entry:
        return None
    if max_age_seconds is not None:
        if (time.time() - entry.get("ts", 0)) > max_age_seconds:
            return None
    return entry.get("base64")


def set_cached_chart(namespace: str, key: str, base64: str) -> None:
    """写缓存（覆盖）"""
    if base64 is None:
        return
    ns = _load_namespace(namespace)
    ns[key] = {"ts": time.time(), "base64": base64}
    _save_namespace(namespace, ns)


def batch_set(namespace: str, items: dict[str, str]) -> None:
    """批量写缓存（一次落盘，避免多次 I/O）"""
    if not items:
        return
    ns = _load_namespace(namespace)
    ts = time.time()
    for k, v in items.items():
        if v is not None:
            ns[k] = {"ts": ts, "base64": v}
    _save_namespace(namespace, ns)


def clear_namespace(namespace: str) -> None:
    """清空某个命名空间的所有缓存（例如上传新数据后 clear eda + ml）"""
    path = _namespace_path(namespace)
    try:
        with _LOCK:
            if os.path.exists(path):
                os.remove(path)
    except Exception:
        pass


def invalidate_key(namespace: str, key: str) -> None:
    """清除单个 key（精细失效，如仅删除 metrics_comparison）"""
    ns = _load_namespace(namespace)
    if key in ns:
        ns.pop(key, None)
        _save_namespace(namespace, ns)
