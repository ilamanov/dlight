import torch.nn as nn
import torch.nn.functional as F


class SimpleConvnet(nn.Module):
    def __init__(self):
        super(SimpleConvnet, self).__init__()

        self.conv1 = nn.Conv2d(1, 8, kernel_size=5, stride=1, padding=2)
        self.conv2 = nn.Conv2d(8, 16, kernel_size=5, stride=1, padding=2)
        self.conv3 = nn.Conv2d(16, 24, kernel_size=5, stride=1, padding=0)
        self.fc4 = nn.Linear(1 * 1 * 24, 16)
        self.fc5 = nn.Linear(16, 10)

    def forward(self, x):
        return self.partial_forward(x, "fc5_softmax")

    def partial_forward(self, x, node_name):
        # x (1, 28, 28)
        x = self.conv1(x)
        # x (8, 28, 28)
        if node_name == "conv1":
            return x
        x = F.relu(x)
        if node_name == "conv1_relu":
            return x
        x = F.max_pool2d(x, kernel_size=2, stride=2, padding=0)
        # x (8, 14, 14)
        if node_name == "conv1_pool":
            return x

        x = self.conv2(x)
        # x (16, 14, 14)
        if node_name == "conv2":
            return x
        x = F.relu(x)
        if node_name == "conv2_relu":
            return x
        x = F.max_pool2d(x, kernel_size=2, stride=2, padding=0)
        # x (16, 7, 7)
        if node_name == "conv2_pool":
            return x

        x = self.conv3(x)
        # x (24, 3, 3)
        if node_name == "conv3":
            return x
        x = F.relu(x)
        if node_name == "conv3_relu":
            return x
        x = F.max_pool2d(x, kernel_size=3, stride=3, padding=0)
        # x (24, 1, 1)
        if node_name == "conv3_pool":
            return x

        x = x.view(-1, 1 * 1 * 24)
        # x (, 24)
        if node_name == "conv3_flattened":
            return x

        x = self.fc4(x)
        # x (, 16)
        if node_name == "fc4":
            return x
        x = F.relu(x)
        if node_name == "fc4_relu":
            return x
            
        x = self.fc5(x)
        # x (, 10)
        if node_name == "fc5":
            return x

        x = F.log_softmax(x, dim=1)
        if node_name == "fc5_softmax":
            return x

        raise ValueError("Invalid node_name= " + node_name)
