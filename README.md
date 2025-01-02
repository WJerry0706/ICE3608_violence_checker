运行网站命令：

`python manage.py makemigrations
python manage.py migrate
python manage.py runserver`

.ckpt文件由于传不下了,又不好放huggingface,就传到了交大云盘中: [https://jbox.sjtu.edu.cn/v/list/self/1804178151677366278](https://jbox.sjtu.edu.cn/l/w1gOPw)

下载完`resnet50_pretrain_test-epoch=16-val_loss=0.06.ckpt`文件后,放到`train_logs/resnet50_pretrain_test/version_6/checkpoints`目录下.

将待分类的图片放置到`violence/test`目录下，然后在`/violence_check_sjtu22/`目录下命令行调用`classify.py`。

运行`monitor.py`即可开始监控。

模型配置：详见`requirements.txt`。若缺失依赖，建议在conda环境下：

```pip install -r requirements.txt```