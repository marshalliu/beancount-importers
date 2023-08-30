# -*- coding: UTF-8 -*-
#!/usr/bin/env python

"""Importer for 微信
"""
__copyright__ = "Copyright (C) 2019  He Yeshuang"
__license__ = "GNU GPLv2"

import csv
import datetime
import logging
import re
import sys
from enum import Enum
from os import path
from typing import Dict

from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import ZERO, D
from beancount.ingest import importer
from dateutil.parser import parse
# from smart_importer import PredictPostings, PredictPayees

_COMMENTS_STR = "收款方备注:二维码收款付款方留言:"

class WechatImporter(importer.ImporterProtocol):
    """An importer for Wechat CSV files."""

    def __init__(self, account="Assets:Flow:EBank:WeChat", accountDict: Dict=None):
        # print(file_type)
        self.account = account
        self.accountDict = accountDict
        self.default_set = frozenset({"wechat"})
        self.currency = "CNY"
        self.source="微信支付"
        pass

    def identify(self, file):
        # Match if the filename is as downloaded and the header has the unique
        # fields combination we're looking for.
        return re.match(r"微信支付账单\(\d{8}-\d{8}\).csv", path.basename(file.name))

    def file_name(self, file):
        return 'wechat.{}'.format(path.basename(file.name))

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

        with open(file.name, encoding="utf-8") as f:
            for _ in range(16):
                next(f)
            for index, row in enumerate(csv.DictReader(f)):
                dt = parse(row["交易时间"])
                if "转入零钱通" in row["交易类型"]:
                    continue  # skip the transfer to wechat

                flag = flags.FLAG_WARNING
                dt = parse(row["交易时间"])
                raw_amount = D(row['金额(元)'].lstrip("¥"))
                isExpense = True if (row['收/支'] == '支出' or row['收/支'] == '/') else False
                if isExpense:
                    raw_amount = -raw_amount
                amount = Amount(raw_amount, self.currency)
                payee = row['交易对方']
                narration = row['商品']
                if narration.startswith(_COMMENTS_STR):
                    narration = narration.replace(_COMMENTS_STR, "")
                if narration == "/":
                    narration = ""

                account_1_text = row['支付方式']
                account_1 = 'Assets.FIXME'
                for asset_k, asset_v in self.accountDict.items():
                    if asset_k in account_1_text:
                        account_1 = asset_v
                        flag = flags.FLAG_OKAY

                # Insert a final balance check.
                postings = [data.Posting(account_1, amount, None, None, None, None)]

                if row["当前状态"] == "充值完成":
                    postings.insert(
                        0,
                        data.Posting(self.account, -amount, None, None, None, None),
                    )
                    narration = "微信零钱充值"
                    payee = None

                meta = data.new_metadata(
                    file.name, index, kvlist={
                        "merchantId": row["商户单号"].rstrip("\t"),
                        "method":account_1_text.rstrip("\t"),
                        "orderId": row["交易单号"].rstrip("\t"),
                        "payTime": row["交易时间"].rstrip("\t"),
                        "source": self.source.rstrip("\t"),
                        "status": row["当前状态"].rstrip("\t"),
                        "txType": row["交易类型"].rstrip("\t"),
                        "type": row['收/支'].rstrip("\t")
                        }
                )

                logging.debug("amount=%s", row['金额(元)'])

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


# @PredictPostings()
# @PredictPayees()
# class SmartWechatImporter(WechatImporter):
#     pass
