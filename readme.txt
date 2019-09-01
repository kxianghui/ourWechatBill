微信账单脚本生成：
    每天消费折线图
    消费top10饼图

运行环境：
    python:3.7.4
    ide:pycharm

运行脚本需要先安装：
    configparser  //pip install configparser命令安装
    不想安装configparser，自己修改配置解析亦可

other:
    执行命令：python wechat_bill.py [param1] [param2] 例如：python wechat_bill.py c:\test.csv c:\
    第一个参数param1为微信账单文件全路径，第二个参数为生成的html文件路径(不写文件名则为wechatBill.html)
    config目录下保存读取配置
    template目录下保存html模板

没做特殊情况考虑，完成基本功能
