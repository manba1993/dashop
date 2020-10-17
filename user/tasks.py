from ddshop11.celery import app
from django.core.mail import send_mail
from django.conf import settings

@app.task    #变成具体的celery 的任务，套上之后就可以推到队列让worker执行
def send_active_email_celery(email_address,verify_url):
    subject ='dashop11激活邮件'
    html_message ='''
    <P>  尊敬的用户 您好</p>
    <p> 您的激活链接为<a href="%s" target ="_blank">点击激活链接</a></p>
    '''%(verify_url)
    send_mail(subject,"",settings.EMAIL_HOST_USER,[email_address],html_message =html_message)  #引入from django.core.mail import send_mail