import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import TensorDataset, random_split, DataLoader
import warnings
warnings.filterwarnings("ignore")


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(2, 1)

    def forward(self, x):
        x = self.fc1(x)
        return x


# 设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = Net().to(device)
torch.manual_seed(42)

# 1. 生成数据集
X = torch.randn(1000, 2)
X1 = X[:, 0]
X2 = X[:, 1]
epsilon = 0.1 * torch.randn(1000)
Y = 3 * X1 - 2 * X2 + 1 + epsilon
Y = Y.reshape(-1, 1)

dataset = TensorDataset(X, Y)
train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
train_data, test_data = random_split(dataset, [train_size, test_size])

train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

# 损失,优化器
loss_fn = nn.MSELoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.5)

epochs = 200
for epoch in range(epochs):
    net.train()
    train_loss_sum = 0.0
    for inputs, labels in train_loader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = net(inputs)
        loss = loss_fn(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss_sum += loss.item()
    # 每轮平均训练损失
    avg_train_loss = train_loss_sum / len(train_loader)
    print(f'[epoch{epoch+1:3d}] train_loss: {avg_train_loss:.4f}')

net.eval()
test_loss_sum = 0.0
with torch.no_grad():
    for inputs, labels in test_loader:
        inputs = inputs.to(device)
        labels = labels.to(device)
        outputs = net(inputs)
        loss = loss_fn(outputs, labels)
        test_loss_sum += loss.item()

avg_test_loss = test_loss_sum / len(test_loader)
print(f"\n测试集平均MSE损失: {avg_test_loss:.4f}")

print(net.fc1.state_dict())