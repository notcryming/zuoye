import json
import random

global power
global intelligence
global agile
global end
role_data = {"力量": 5, "智力": 5, "敏捷": 5}
with open("role_json.json", "w", encoding="utf-8") as f:
    json.dump(role_data, f, ensure_ascii=False)
with open("role_json.json", "r", encoding="utf-8") as f:
    load_data = json.load(f)
# 三维属性由字典键值对访问
power = load_data["力量"]
intelligence = load_data["智力"]
agile = load_data["敏捷"]
# 加点数
point = 0
# 信号
sign = 10
end = 1
# 操作数
op = 0
ops = 0


# 异常捕获装饰器
def error_capture(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print('请勿输入非数字内容', e)

    return wrapper


# 操作问询
def opask():
    print("请问你要进行的操作是(输入数字序号即可)：\n1.加点\n2.职业检定\n3.攻击\n4.结束\n")


# 选择加点属性
def switchask():
    print("请问你要加点哪一项属性(输入数字序号即可)：\n1.力量\n2.智力\n3.敏捷\n")


# 播报当前属性值
def attrlist():
    print(f"你目前的属性是：\n力量：{power}\n智力：{intelligence}\n敏捷：{agile}\n")


# 属性加点计算
def add_attr(shuxing, add_num=5):
    '''属性加点计算'''
    return shuxing + add_num


# 属性加点
@error_capture
def add_swictch():
    global power
    global intelligence
    global agile
    flag = 1
    while flag:
        switchask()
        ops = int(input())
        while ops not in range(1, 4):
            print("输入数字不合法，请重试！")
            switchask()
            ops = int(input())
        print("请问你要增加几点属性(输入数字即可)：\n")
        point = int(input())
        if point in [x for x in range(1, 11)]:
            if ops == 1:
                power = add_attr(power, point)
            elif ops == 2:
                intelligence = add_attr(intelligence, point)
            else:
                agile = add_attr(agile, point)
            print("加点成功！\n")
            if point > 4:
                get_buff()
        else:
            print("加点需在1-10点之间！")
        attrlist()
        print("输入数字0退出加点，输入其他内容继续\n")
        sign = int(input())
        if sign == 0:
            flag = 0
    save_data()


# 判断职业
def judge():
    if power >= 10 and intelligence >= 10 and agile >= 10:
        print("职业定位：均衡大师")
    elif power >= 10 and agile >= 10:
        print("职业定位：狂战士")
    elif power >= 10 and intelligence >= 10:
        print("职业定位：战斗法师")
    elif agile >= 10 and intelligence >= 10:
        print("职业定位：奥术法师")
    elif power >= 10:
        print("职业定位：战士")
    elif intelligence >= 10:
        print("职业定位：法师")
    elif agile >= 10:
        print("职业定位：盗贼")
    else:
        print("职业定位：学徒")


# 存储数据
def save_data():
    role_text = {'力量': power, '智力': intelligence, '敏捷': agile}
    # role_text = "{"+f"'力量': {power}, '智力': {intelligence}, '敏捷': {agile}"+"}"  直接存字典就可以了，一开始只考虑到存字典格式反而想太多
    with open("role_json.json", "w", encoding="utf-8") as f:
        json.dump(role_text, f, ensure_ascii=False)
        print("属性已保存！\n")
    with open("role_json.json", "r", encoding="utf-8") as f:
        print("读取存储结果：")
        load_data = json.load(f)
        print(load_data)


# 攻击模式选择
@error_capture
def attackmode():
    print("选择攻击方式：\n1.普通攻击\n2.猛烈打击\n3.火球术\n")
    ops = int(input())
    while ops not in range(1, 4):
        print("输入操作不合法，请重试！")
        print("选择攻击方式：\n1.普通攻击\n2.猛烈打击\n3.火球术\n")
        ops = int(input())
    if ops == 1:
        attack = lambda x: x - 1
        print(f"造成了{attack(power)}点伤害！")
    elif ops == 2:
        print(f"造成了{attack_physics(power, agile)}点伤害！")
    else:
        print(f"造成了{attack_magic(intelligence, agile)}点伤害！")


# buff生成器
def buff_generator():
    buffs = {'power': "力量增幅+", 'intelligence': "智力增幅+", 'agile': "敏捷增幅+"}
    buffs_key = list(buffs.keys())
    while True:
        num = random.randint(1, 5)  # 随机生成1-5的数值
        type = random.choice(buffs_key)  # 随机选择buff类型
        buff = buffs[type] + str(num)  # 键值对访问拼在一起
        yield buff, num, type


# 获得buff
def get_buff():
    global power
    global intelligence
    global agile
    buff, num, type = next(g)
    print(type)
    print("由于加点提升巨大，获得buff：", buff)
    if type == 'power':
        power = add_attr(power, num)
    elif type == 'intelligence':
        intelligence = add_attr(intelligence, num)
    else:
        agile = add_attr(agile, num)
    print(f"猛烈打击将造成{attack_physics(power, agile)}点伤害！")
    print(f"火球术将造成{attack_magic(intelligence, agile)}点伤害！")


# 双倍伤害装饰器
def double_effect(func):
    def wrapper(*args, **kwargs):
        print("魔法特效：双倍伤害！")
        res = func(*args, **kwargs)
        return res * 2

    return wrapper


# 绑定装饰器的技能伤害函数
@double_effect
def attack_physics(power, agile):
    return int(power * agile / 10 + power)


@double_effect
def attack_magic(intelligence, agile):
    return int(intelligence * agile / 6)


# 主程序
@error_capture
def main():
    global end
    opask()
    op = int(input())
    while op not in range(1, 5):
        print("输入操作不合法，请重试！")
        opask()
        op = int(input())
    if op == 1:
        add_swictch()
    elif op == 2:
        judge()
    elif op == 3:
        attackmode()
    else:
        end = 0


if __name__ == "__main__":
    attrlist()
    g = buff_generator()
    while end:
        main()
    save_data()