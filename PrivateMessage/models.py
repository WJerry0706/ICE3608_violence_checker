from django.db import models
from UserAuth.models import User  # 导入自定义 User 模型

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)  # 内容字段，允许为空
    image = models.ImageField(upload_to='message_images/', blank=True, null=True)  # 上传图片字段
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} at {self.timestamp}"