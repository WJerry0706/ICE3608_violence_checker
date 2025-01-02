# ContentReview/middleware.py
import re
from .sensitive_words import SENSITIVE_WORDS
from .sensitive_words import load_sensitive_words

# ContentReview/middleware.py
class SensitiveWordsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # 在中间件初始化时加载敏感词
        self.sensitive_words = load_sensitive_words('ContentReview/sensitive_words.txt')

    def __call__(self, request):
        if request.method == "POST":
            # 复制 POST 数据，使其可变
            mutable_post = request.POST.copy()

            for key, value in mutable_post.items():
                if isinstance(value, str):
                    mutable_post[key] = self.censor_content(value)

            # 替换原始不可变 POST 数据
            request.POST = mutable_post

        return self.get_response(request)

    def censor_content(self, content):
        for word in SENSITIVE_WORDS:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            content = pattern.sub('**', content)
        return content