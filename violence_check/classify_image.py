import torch
from torchvision import transforms
from PIL import Image
from model import ViolenceClassifier

class ImageClassifier:
    def __init__(self, checkpoint_path):
        """
        初始化分类器
        :param checkpoint_path: 模型检查点路径
        """
        # 加载预训练模型
        self.model = ViolenceClassifier.load_from_checkpoint(checkpoint_path)
        self.model.eval()  # 设置模型为评估模式

        # 移动到 GPU（如果可用）
        if torch.cuda.is_available():
            self.model.cuda()

        # 定义图像预处理
        self.transforms = transforms.Compose([
            transforms.Resize((224, 224)),  # 假设模型需要224x224大小的输入
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # 标准化
        ])

    def classify_image(self, image_path):
        """
        对单张图片进行分类
        :param image_path: 图片文件路径
        :return: 分类结果（int，0或1等）
        """
        # 打开图像并预处理
        image = Image.open(image_path).convert('RGB')
        input_tensor = self.transforms(image).unsqueeze(0)  # 添加 batch 维度

        # 移动到 GPU（如果可用）
        if torch.cuda.is_available():
            input_tensor = input_tensor.cuda()

        # 使用模型进行预测
        with torch.no_grad():
            logits = self.model(input_tensor)
            prediction = torch.argmax(logits, dim=1).item()  # 返回预测类别

        return prediction