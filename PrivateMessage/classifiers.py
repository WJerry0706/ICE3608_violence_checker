import os
import torch
from torchvision import transforms
from PIL import Image
from .model import ViolenceClassifier  # 确保 model.py 在正确的路径下
from django.conf import settings

class ViolenceClass:
    def __init__(self, checkpoint_path, batch_size=16):
        # 加载模型
        self.model = ViolenceClassifier.load_from_checkpoint(checkpoint_path)
        self.model.eval()  # 设置模型为评估模式
        self.batch_size = batch_size

        # 如果有GPU，移动模型到GPU
        if torch.cuda.is_available():
            self.model.cuda()

        # 定义图像预处理
        self.transforms = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])

    def classify(self, tensor):
        # 确保输入是PyTorch Tensor
        assert isinstance(tensor, torch.Tensor), "Input must be a PyTorch Tensor"
        assert tensor.size(1) == 3 and tensor.size(2) == 224 and tensor.size(
            3) == 224, "Tensor shape must be n*3*224*224"

        # 如果有GPU，移动输入到GPU
        if torch.cuda.is_available():
            tensor = tensor.cuda()

        # 使用模型进行预测
        with torch.no_grad():
            logits = self.model(tensor)
            predictions = torch.argmax(logits, dim=1)

        # 将预测结果转换为Python列表
        return predictions.tolist()

    def classify_image(self, image_path):
        image = self.transforms(Image.open(image_path).convert('RGB'))
        tensor = image.unsqueeze(0)  # 添加批次维度
        return self.classify(tensor)[0]

# 初始化分类器实例（单例模式）
checkpoint_path = os.path.join(
    "/OnlineChat/violence_check/train_logs/resnet50_pretrain_test/version_6/checkpoints/resnet50_pretrain_test-epoch=16-val_loss=0.06.ckpt")
violence_classifier = ViolenceClass(checkpoint_path, batch_size=16)