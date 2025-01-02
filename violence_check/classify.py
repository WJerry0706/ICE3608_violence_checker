# ContentReview/middleware.py
import re
from django.http import HttpResponseForbidden
from django.conf import settings
from .sensitive_words import SENSITIVE_WORDS, load_sensitive_words
from .classify import ViolenceClass
from PIL import Image
import io
import torch

class SensitiveWordsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # 在中间件初始化时加载敏感词
        self.sensitive_words = load_sensitive_words('ContentReview/sensitive_words.txt')

        # 加载本地图像审查模型
        checkpoint_path = getattr(settings, 'VIOLENCE_MODEL_CHECKPOINT', '/OnlineChat/media/message_images')
        self.violence_classifier = ViolenceClass(checkpoint_path, batch_size=16)

    def __call__(self, request):
        if request.method == "POST":
            # 处理 POST 数据中的敏感词
            mutable_post = request.POST.copy()

            for key, value in mutable_post.items():
                if isinstance(value, str):
                    mutable_post[key] = self.censor_content(value)

            # 替换原始不可变 POST 数据
            request.POST = mutable_post

            # 处理上传的图片文件
            if request.FILES:
                for file_key, file in request.FILES.items():
                    if self.is_image(file):
                        if not self.censor_image(file):
                            return HttpResponseForbidden("上传的图片包含不允许的内容。")

        return self.get_response(request)

    def censor_content(self, content):
        for word in self.sensitive_words:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            content = pattern.sub('**', content)
        return content

    def is_image(self, file):
        # 简单检查文件的内容类型
        return file.content_type.startswith('image/')

    def censor_image(self, file):
        try:
            # 读取图片内容
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            preprocessed_image = self.violence_classifier.transforms(image)
            tensor = preprocessed_image.unsqueeze(0)  # 添加批次维度

            # 使用模型进行预测
            predictions = self.violence_classifier.classify(tensor)

            # 假设预测结果 1 表示暴力，0 表示非暴力
            is_violent = any(pred == 1 for pred in predictions)

            return not is_violent
        except Exception as e:
            # 处理异常情况，例如日志记录
            print(f"图片审查失败: {e}")
            # 根据需求决定是拒绝请求还是允许通过
            return False
        finally:
            # 重置文件指针，以便后续处理
            file.seek(0)