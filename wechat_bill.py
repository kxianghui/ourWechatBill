# coding=utf-8
# !/usr/bin/python

import csv
import sys
import json
import configparser
import traceback


class WeChatBill:
    """
    wechat bill analysis
    """

    def __init__(self, path, create_file_path):
        self.path = path
        if create_file_path.endswith('\\') or create_file_path.endswith('//'):
            create_file_path += 'wechatBill.html'
        self.create_file_path = create_file_path
        self.config_dict = \
            self.read_configuration_file("./config/config.ini")['csv']

    def read_configuration_file(self, path):
        """
        读取配置
        :param path: 配置文件路径
        :return: [section_name:{xx:xx,xx:xx...}]
        """
        config = configparser.ConfigParser()
        config.read(path)
        config_section = config.sections()
        config_dict = dict()
        for section_name in config_section:
            option_keys = config.options(section_name)
            config_section_dict = dict()
            for key in option_keys:
                value = config.get(section_name, key)
                config_section_dict[key] = value
            config_dict[section_name] = config_section_dict
        return config_dict

    def resolve_bill_content(self, row, title_list):
        """
        处理每条交易内容
        :param row:
        :param title_list:
        :return:
        """
        content_dict = dict()
        cell_index = 0
        for title in title_list:
            value = row[cell_index]
            if title == 'price':
                value = row[cell_index].replace('¥', '')
            content_dict[title] = value
            cell_index += 1
        return content_dict

    def resolve_bill_csv(self, readers):
        """
        解析csv，按固定规则，需要解码utf-8
        :return:
        """
        data_dict = dict()
        content_list = []
        title_list = ["dealTime", 'dealType', 'payForName', 'name', 'incomeOrPay', 'price', 'payMethod', 'status']
        row_index = 1
        for row in readers:
            # per cell
            cell_index = 1
            # before bill content
            if row_index < 18:
                for cell in row:
                    if cell.strip() == '':
                        continue
                    key = "%s,%s" % (str(cell_index), str(row_index))
                    value = self.config_dict.get(key)
                    if value is not None:
                        data_dict[value] = cell
                    cell_index += 1
            else:
                # resolve bill content
                content_dict = self.resolve_bill_content(row, title_list)
                content_list.append(content_dict)
            row_index += 1
        if len(content_list) != 0:
            data_dict['content'] = content_list
        return data_dict

    def read_file(self):
        """
        读取文件内容，解析格式化内容
        :return:
        """
        with open(self.path, "r", encoding='utf-8') as f:
            readers = csv.reader(f)
            self.data_dict = self.resolve_bill_csv(readers)

    def per_day_spend(self):
        """
        每天花费，不计算小数点
        :return: {time:xxxx,time:xxxx...}
        """
        if self.data_dict is not None:
            self.per_day_spend_dict = dict()
            content_list = self.data_dict.get("content")
            for content_dict in content_list:
                if not (content_dict['incomeOrPay'] == '支出' and content_dict['status'] == '支付成功'):
                    continue
                deal_time = content_dict['dealTime'].split()[0].strip()
                price = round(float(content_dict['price']))
                value = self.per_day_spend_dict.get(deal_time)
                if value is not None:
                    value = int(value)
                    self.per_day_spend_dict[deal_time] = value + price
                else:
                    self.per_day_spend_dict[deal_time] = price
            self.per_day_spend_key_list = list(self.per_day_spend_dict.keys())
            self.per_day_spend_value_list = list(self.per_day_spend_dict.values())

    def top_10_where_spend(self):
        """
        消费前10
        :return:
        """
        if self.data_dict is not None:
            self.top_10_dict = dict()
            content_list = self.data_dict.get("content")
            for content_dict in content_list:
                if not (content_dict['incomeOrPay'] == '支出' and content_dict['status'] == '支付成功'):
                    continue
                payForName = content_dict['payForName'].strip()
                price = round(float(content_dict['price']))
                value = self.top_10_dict.get(payForName)
                if value is not None:
                    value = int(value)
                    self.top_10_dict[payForName] = value + price
                else:
                    self.top_10_dict[payForName] = price
            self.top_10_dict_sort_list = sorted(self.top_10_dict, key=self.top_10_dict.__getitem__, reverse=True)
            self.top_10_dict_legend = []
            self.top_10_series_data_list = []
            count = 1
            for key in self.top_10_dict_sort_list:
                temp_data_dict = dict()
                value = self.top_10_dict[key]
                temp_data_dict['name'] = key
                temp_data_dict['value'] = value
                self.top_10_dict_legend.append(key)
                self.top_10_series_data_list.append(temp_data_dict)
                if count > 10:
                    break
                count+=1

    def format_replace(self, format_str, *args):
        """
        格式化替换模板
        :param format_str:
        :param args:
        :return:
        """
        count = 0
        for arg in args:
            format_count = '${%s}' % count
            format_str = format_str.replace(format_count, arg)
            count+=1
        return format_str

    def create_file_by_template(self):
        with open("./template/per_day_spend", 'r', encoding='utf-8') as per_day_spend:
            per_day_spend_option = per_day_spend.read()
            per_day_spend_option = self.format_replace(per_day_spend_option, json.dumps(self.per_day_spend_key_list),
                                                       json.dumps(self.per_day_spend_value_list))
        with open("./template/top_10_option", 'r', encoding='utf-8') as top_10_spend:
            top_10_spend_option = top_10_spend.read()
            top_10_spend_option = self.format_replace(top_10_spend_option, json.dumps(self.top_10_dict_legend),
                                                       json.dumps(self.top_10_series_data_list))
        with open("./template/template.html", 'r', encoding='utf-8') as template_file:
            template = template_file.read()
            name = self.data_dict['name']
            time = self.data_dict['time']
            total_record = self.data_dict['totalRecord']
            income = self.data_dict['income']
            pay = self.data_dict['pay']
            template = self.format_replace(template, name, time, total_record, income, pay,
                                           per_day_spend_option,top_10_spend_option)
        with open(self.create_file_path, 'w', encoding='utf-8') as result_file:
            result_file.write(template)

    def resolve_wechat_bill_operation(self):
        try:
            # 读取文件
            print('read wechat bill csv file...')
            self.read_file()
            print('per day spend caculate...')
            # 每天花费
            self.per_day_spend()
            print('top 10 where spend caculate...')
            # 消费前10
            self.top_10_where_spend()
            print('create html file by template...')
            # create file
            self.create_file_by_template()
            print('create over...')
        except:
            print('resolve defeat...')
            print(traceback.format_exc())


if __name__ == '__main__':
    # 从控制台获取路径参数
    # bill文件全路径
    data_file_path = sys.argv[1]
    # # 生成文件路径
    create_file_path = sys.argv[2]
    wechat_bill = WeChatBill(data_file_path, create_file_path)
    wechat_bill.resolve_wechat_bill_operation()