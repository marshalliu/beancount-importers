# -*- coding: UTF-8 -*-
#!/usr/bin/env python

"""Importer for 微信
"""
__copyright__ = "Copyright (C) 2013  Marshal Liu"
__license__ = "GNU GPLv2"

import csv
import datetime
import logging
import re
from os import path
from typing import Dict

from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import ZERO, D
from beancount.ingest import importer
from dateutil.parser import parse

class AlipayImporter(importer.ImporterProtocol):
    """An importer for Alipay CSV files."""

    def __init__(self, account="Assets:Flow:EBank:Alipay", accountDict: Dict=None, expenseDict: Dict=None):
        # print(file_type)
        self.account = account
        self.accountDict = accountDict
        self.expenseDict = expenseDict
        self.default_set = frozenset({"Alipay"})
        self.currency = "CNY"
        self.source="支付宝支付"
        pass

    def identify(self, file):
        # Match if the filename is as downloaded and the header has the unique
        # fields combination we're looking for.
        return re.match(r"alipay_record_\d{8}_\d{6}.csv", path.basename(file.name))

    def file_name(self, file):
        return 'alipay.{}'.format(path.basename(file.name))

    def file_account(self, _):
        return self.account

    def file_date(self, file):
        # Extract the statement date from the filename.
        return datetime.datetime.strptime(path.basename(file.name).split("-")[-1],
                                          '%Y%m%d).csv').date()

    def extract(self, file, existing_entries=None):
        # Open the CSV file and create directives.
        entries = []
        index = 0
        with open(file.name, encoding="gbk") as f:
            for _ in range(24):
                next(f)
            for index, row in enumerate(csv.DictReader(f)):
            
                if  '交易关闭' in row['交易状态'] and '不计收支' in row['收/支']:
                    continue
                if '冻结成功'in row['交易状态']:
                    continue

                dt = parse(row["交易时间"])
                flag = flags.FLAG_WARNING
                raw_amount = D(row['金额'])
                isExpense = True if (row['收/支'] == '支出') else False
                if isExpense:
                    raw_amount = -raw_amount
                amount = Amount(raw_amount, self.currency)
                payee = row['交易对方']
                narration = row['商品说明']

                account_1_text = row['收/付款方式']
                account_1 = 'Assets.FIXME'
                for asset_k, asset_v in self.accountDict.items():
                    if asset_k in account_1_text:
                        account_1 = asset_v

                account_2 = None
                for asset_k, asset_v in self.expenseDict.items():
                    if asset_k.find(",") > -1:
                        for asset_k1 in asset_k.split(","):
                            if asset_k1 in payee or asset_k1 in narration:
                                account_2 = asset_v
                                flag = flags.FLAG_OKAY
                    elif asset_k in payee or asset_k in narration:
                        account_2 = asset_v
                        flag = flags.FLAG_OKAY
                
               # if row["当前状态"] == "":
               #     postings.insert(
               #         0,
               #         data.Posting(self.account, -amount, None, None, None, None),
               #     )
               #     narration = "微信零钱充值"
               #     payee = None
               # elif row["交易类型"] == "微信红包" and account_1_text.rstrip("\t") == "/":
               #     account_2 = self.accountDict["微信红包"]
               #     flag = flags.FLAG_OKAY

                # Insert a final balance check.
                if (account_2 != None):
                    postings = [data.Posting(account_1, amount, None, None, None, None),
                                data.Posting(account_2, -amount, None, None, None, None)]
                else: 
                    postings = [data.Posting(account_1, amount, None, None, None, None)]

                #交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注,
                meta = data.new_metadata(
                    file.name, index, kvlist={
                        "merchantId": row["商家订单号"].rstrip("\t"),
                        "method": payee,
                        "orderId": row["交易订单号"].rstrip("\t"),
                        "payTime": row["交易时间"],
                        "source": "支付宝支付",
                        "status": row["交易状态"],
                        "txType": row["交易分类"],
                        "type": row["收/支"]
                        }
                )
                #logging.warn("%s:%s:%s", payee, narration, account_2)

                txn = data.Transaction(
                    meta,
                    dt.date(),
                    flag,
                    payee,
                    narration,
                    self.default_set,
                    data.EMPTY_SET,
                    postings,
                )

                entries.append(txn)

        return entries