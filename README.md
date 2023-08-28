## importers

[smart_importer](https://github.com/beancount/smart_importer) needs to be installed to import smartly.我还添加了jieba分词，对中文也许有作用。

### 微信

数据来源：`支付-钱包-账单-常见问题-下载账单-用作个人对账`

```bash
bean-extract importers/wechat.import documents.tmp/微信支付账单(xxxxxxxx-xxxxxxxx).csv -e 你的参考账本.bean> test.bean 
```

### 中国银行借记卡

数据来源：中国银行网上银行（网页版）~~，需要将UTF-16转换成UTF-8~~，现在不需要了。`他们终于找到了按钮！`

```bash
bean-extract importers/boc.import documents.tmp/test.csv -e 你的参考账本.bean> test.bean
```
### 招商银行信用卡

1. `cmb_eml.import`数据源为信用卡账单电子邮件。需要在招行网银上将账单邮寄方式改为“电子邮件（含明细）”，然后在邮件客户端上下载“招商银行信用卡电子账单xxx.eml”

2. `cmb_json.import`数据源为[招商银行信用卡中心](https://xyk.cmbchina.com/credit-express/bill)移动网页，需要保存这个网页与服务器之间`XMLHttpRequest`通信。我写了一篇[blog](https://blog.heysh.xyz/2022/01/21/new-method-to-get-cmb-bill/)来搞到这个。需要将通信内容保存为`.json`文件。
要是一个不行的话可以试试另外一个。

```bash
## EML方法
bean-extract importers/cmb_eml.import documents.tmp/招商银行信用卡电子账单xxx.eml -e 你的参考账本.bean> test.bean

## JSON方法
bean-extract importers/cmb_json.import documents.tmp/xxx.json -e 你的参考账本.bean > test.bean
```

### 民生银行借记卡

在手机网上银行上可以导出PDF格式的民生银行借记卡账单。通过`Camelot-py`读取PDF。

>注意，这种方法是按照PDF的绝对位置取数值的，如果你有超大额支出的话请务必核对。我就没有这种烦恼啦~

```bash
bean-extract importers/cmbc_pdf.import documents.tmp/pdf_mxXXXXXX.pdf -e 你的参考账本.bean> test.bean
```

### 使用bean-file归档

```bash
bean-file -o documents importers/XXXX.import documents.tmp/XXXX 
```

## 可能出现的问题

- 在Windows的CMD下，通过`>`输出的文件编码可能有误，需要在运行命令前设置环境变量：

```CMD
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8:surrogateescape
```

或者一劳永逸，在控制面版的“区域设置”中勾选“使用UTF-8提供全球语言支持”。See https://www.tutorialexample.com/set-windows-powershell-to-utf-8-encoding-to-fix-gbk-codec-can-not-encode-character-error-powershell-tutorial/
