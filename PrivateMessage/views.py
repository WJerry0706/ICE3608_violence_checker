from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Message
from .forms import MessageForm
from django.core.paginator import Paginator, EmptyPage
from django.utils.functional import SimpleLazyObject
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime

import re
import os
from django.conf import settings
from UserAuth.models import User
from django.http import HttpResponse
from django.db.models import Q, Count, Max
from django.http import JsonResponse


# 在 views.py 文件中初始化分类器
# from .classify_image import ImageClassifier  # 替换为实际文件路径
from django.conf import settings

# 初始化分类器
# classifier = ImageClassifier(settings.MODEL_CHECKPOINT_PATH)

# 获取用户头像的帮助函数
def get_matching_files(request):
    pattern = re.compile(str(request.session['UserInfo'].get("id")) + r'.*')
    file_names = os.listdir(settings.PROFILE_ROOT)
    matching_files = []
    for file_name in file_names:
        if pattern.match(file_name):
            matching_files.append(file_name)
    # 没有上传就用默认的
    if not matching_files:
        matching_files.append('default.jpeg')
    return matching_files[0]

# 收件箱视图
# @login_required
def inbox(request):
    # 获取当前用户的ID
    user_id = request.session['UserInfo'].get('id')
    current_user = User.objects.get(id=user_id)

    # 获取当前用户收到的所有消息和发送的消息
    received_messages = Message.objects.filter(recipient=current_user).order_by('-timestamp')
    sent_messages = Message.objects.filter(sender=current_user).order_by('-timestamp')

    # 分页功能
    messages_per_page = 10
    paginator = Paginator(received_messages, messages_per_page)
    page_number = request.GET.get('page')

    try:
        current_page = paginator.get_page(page_number)
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)

    context = {
        'matching_files': get_matching_files(request),  # 用户头像
        'received_messages': current_page,
        'sent_messages': sent_messages,
    }
    return render(request, 'PrivateMessage/inbox.html', context)

# 发送消息视图
# @login_required
def send_message(request):
    user_info = request.session.get('UserInfo', {})
    user_id = user_info.get('id')

    # 验证用户登录状态
    if not user_id:
        return redirect('login')  # 未登录用户重定向

    current_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES or None)  # 处理上传文件
        if form.is_valid():
            recipient_id = request.POST.get('recipient')
            recipient = get_object_or_404(User, id=recipient_id)

            # 保存消息
            message = form.save(commit=False)
            message.sender = current_user
            message.recipient = recipient
            message.save()

            # 发送消息后重定向到对话页面
            return redirect(reverse('PrivateMessage:conversation_with_user', args=[current_user.id, recipient.id]))
    else:
        form = MessageForm()

    # 获取所有用户列表，包括当前用户
    users = User.objects.all()

    return render(request, 'PrivateMessage/send_message.html', {
        'form': form,
        'users': users,
    })

# 查看消息详情视图
# @login_required

def view_message(request, message_id):
    user_id = request.session['UserInfo'].get('id')
    current_user = User.objects.get(id=user_id)

    message = get_object_or_404(Message, Q(id=message_id) & (Q(recipient=current_user) | Q(sender=current_user)))

    message.is_read = True  # 将消息标记为已读
    message.save()

    context = {
        'message': message,
        'matching_files': get_matching_files(request),
    }
    return render(request, 'PrivateMessage/view_message.html', context)

# @login_required
def reply_message(request, message_id):
    user_id = request.session['UserInfo'].get('id')
    current_user = User.objects.get(id=user_id)

    original_message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)  # 添加 request.FILES
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = current_user
            reply.recipient = original_message.sender
            reply.save()

            return redirect('PrivateMessage:conversation', current_user_id=current_user.id, selected_user_id=original_message.sender.id)
    else:
        form = MessageForm()

    context = {
        'form': form,
        'matching_files': get_matching_files(request),
        'original_message': original_message,
    }
    return render(request, 'PrivateMessage/reply_message.html', context)

# @login_required
from .forms import MessageForm
from django.shortcuts import redirect

# @login_required
from django.utils import timezone

from django.utils.timezone import localtime

def conversation_view(request, current_user_id, selected_user_id):
    # 获取当前用户和选定用户
    current_user = get_object_or_404(User, id=current_user_id)
    selected_user = get_object_or_404(User, id=selected_user_id)

    # 标记前50条未读消息为已读，避免性能问题
    # 获取前 50 条未读消息的 ID
    unread_messages = Message.objects.filter(
        sender=selected_user, recipient=current_user, is_read=False
    ).order_by('timestamp')[:50].values_list('id', flat=True)

    # 批量更新这些消息
    Message.objects.filter(id__in=unread_messages).update(is_read=True)
    # 获取与选定用户的最近50条消息
    messages = Message.objects.filter(
        (Q(sender=current_user) & Q(recipient=selected_user)) |
        (Q(sender=selected_user) & Q(recipient=current_user))
    ).order_by('-timestamp')[:50]  # 降序，显示最近的消息

    # 格式化时间戳
    messages_data = []
    for message in messages:
        messages_data.append({
            'sender_id': message.sender.id,
            'content': message.content,
            'image_url': request.build_absolute_uri(message.image.url) if message.image else None,
            'timestamp': localtime(message.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        })

    # 初始化消息表单
    form = MessageForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        new_message = form.save(commit=False)
        new_message.sender = current_user
        new_message.recipient = selected_user
        new_message.save()

        # 返回刚发送的消息数据（JSON响应）
        new_message_data = {
            'sender_id': new_message.sender.id,
            'content': new_message.content,
            'image_url': request.build_absolute_uri(new_message.image.url) if new_message.image else None,
            'timestamp': localtime(new_message.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        }

        # 检查是否为 AJAX 请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'new_message': new_message_data})

        # 如果不是 AJAX 请求，重定向
        return redirect('PrivateMessage:conversation_with_user', current_user_id=current_user.id, selected_user_id=selected_user.id)

    return render(request, 'PrivateMessage/conversation.html', {
        'contact_users': User.objects.exclude(id=current_user.id),
        'messages': reversed(messages),  # 消息反序显示
        'selected_user': selected_user,
        'current_user': current_user,
        'form': form,
    })

def fetch_new_messages(request, current_user_id, selected_user_id):
    current_user = get_object_or_404(User, id=current_user_id)
    selected_user = get_object_or_404(User, id=selected_user_id)

    messages = Message.objects.filter(
        (Q(sender=current_user) & Q(recipient=selected_user)) |
        (Q(sender=selected_user) & Q(recipient=current_user))
    ).order_by('timestamp')

    message_data = []
    for message in messages:
        # 构建 image_url 并打印路径
        image_url = request.build_absolute_uri(message.image.url) if message.image else None
        # print("DEBUG: image_url =", image_url)  # 临时调试输出
        message_data.append({
            'sender_id': message.sender.id,
            'content': message.content,
            'image_url': image_url,
            'timestamp': timezone.localtime(message.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        })

    return JsonResponse({'messages': message_data})
from django.shortcuts import get_object_or_404, redirect
from UserAuth.models import User

def search_user(request):
    # 获取输入的用户ID或用户名
    username = request.GET.get('user_id')  # 假设通过用户名搜索
    current_user_id = request.session['UserInfo'].get('id')

    # 查找目标用户
    target_user = get_object_or_404(User, username=username)  # 根据用户名查找用户

    # 使用 redirect 跳转到 conversation_view
    return redirect('PrivateMessage:conversation_with_user', current_user_id=current_user_id, selected_user_id=target_user.id)