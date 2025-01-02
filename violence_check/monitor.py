import os
import time
import torch
from torchvision import transforms
from PIL import Image
from model import ViolenceClassifier
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

    def classify_single_image(self, image_path):
        # 预处理图像
        image = self.transforms(Image.open(image_path).convert('RGB'))
        tensor = image.unsqueeze(0)  # 添加批次维度

        # 分类
        prediction = self.classify(tensor)
        return prediction[0]

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, classifier, valid_extensions=('.png', '.jpg', '.jpeg')):
        super().__init__()
        self.classifier = classifier
        self.valid_extensions = valid_extensions
        self.processed_files = set()

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in self.valid_extensions:
            print(f"忽略非图像文件: {file_path}")
            return

        # 等待文件完全写入
        time.sleep(1)

        if file_path in self.processed_files:
            print(f"文件已处理: {file_path}")
            return

        print(f"检测到新文件: {file_path}")

        try:
            prediction = self.classifier.classify_single_image(file_path)
            print(f"文件 {file_path} 的分类结果: {prediction}")

            if prediction == 1:
                os.remove(file_path)
                print(f"文件 {file_path} 被删除，因为分类结果为1。")
            else:
                print(f"文件 {file_path} 被保留，因为分类结果为{prediction}。")

            self.processed_files.add(file_path)
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

def main():
    # 模型检查点路径
    log_name = "train_logs/resnet50_pretrain_test"
    checkpoint_path = os.path.join(
        log_name,
        "version_6",
        "checkpoints",
        "resnet50_pretrain_test-epoch=16-val_loss=0.06.ckpt"
    )  # 替换为你的模型检查点路径

    # 创建分类器实例
    violence_classifier = ViolenceClass(checkpoint_path, batch_size=16)

    # 要监视的目录路径
    watch_directory = "/Users/w.jerry/ICE3608-01-violence_checker/OnlineChat/media/message_images"

    # 创建事件处理器
    event_handler = NewFileHandler(violence_classifier)

    # 创建观察者
    observer = Observer()
    observer.schedule(event_handler, path=watch_directory, recursive=False)

    # 启动观察者
    observer.start()
    print(f"开始监视目录: {watch_directory}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("停止监视。")

    observer.join()

if __name__ == "__main__":
    main()


