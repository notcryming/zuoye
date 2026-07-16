# goods/__init__.py
# 包标识文件：标记 goods 文件夹为 Python 包，使外部可通过 from goods.xxx 导入
# 此文件可为空白，此处使用进阶简化导入写法，预导入所有饮品类
# 外部可直接 from goods import FruitTea, MilkCapTea, Coffee, BaseDrink

from goods.base_drink import BaseDrink
from goods.fruit_tea import FruitTea
from goods.milk_cap import MilkCapTea
from goods.coffee import Coffee
