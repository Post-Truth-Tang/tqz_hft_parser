import datetime
import os
import sqlite3 as db
import matplotlib.pyplot as pyplot

from tqz_hft_parser_app.tqz_extern.tools.pandas_operator.pandas_operator import pandas
from tqz_hft_parser_app.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
from tqz_hft_parser_app.hft_parser_path import TQZHftParserPath

class TQZHftTradePictureKit:

    __database_all_path = TQZFilePathOperator.grandfather_path(source_path=__file__) + f'/tqzpy_futures_database/.vntrader/database.db'
    __picture_fold = f'pictures'

    # --- api part ---
    @classmethod
    def tqz_create_trade_pictures(cls, parser_trade_result_fold):

        for file_name in os.listdir(cls.__picture_fold):
            os.remove(path=f'{cls.__picture_fold}/{file_name}')

        if os.path.exists(path=parser_trade_result_fold):
            for csv_path in os.listdir(path=parser_trade_result_fold):
                TQZHftTradePictureKit.__create_picture(
                    csv_path_name=csv_path
                )

    # --- private part ---
    @classmethod
    def __create_picture(cls, csv_path_name: str):
        """
        Create trade_tick picture with symbol.
        """
        symbol = cls.__tqz_get_symbolString(csv_path_name=csv_path_name)
        today_begin = f'{datetime.date.today()} 08:30:00'
        today_end = f'{datetime.date.today()} 16:00:00'

        content = cls.__readFronSqllite(cls.__database_all_path, f"SELECT * FROM dbtickdata WHERE symbol=='{symbol}' and datetime>='{today_begin}' and datetime<'{today_end}';")
        content_dataframe = pandas.DataFrame(content)

        time_x_list = content_dataframe[3].astype(str).values.tolist()  # [3]: time stamp
        time_x = []
        for timeItem in time_x_list:
            time_x.append(timeItem.split(" ")[1])
        content_dataframe['time_x'] = time_x

        # get symbol trade dataframe.
        csv_all_path = TQZHftParserPath.parser_trade_result_fold() + f'/{csv_path_name}'
        symbol_trade_dataframe = pandas.read_csv(csv_all_path)
        symbol_openPositions_dataframe = symbol_trade_dataframe.loc[(symbol_trade_dataframe['order_type'] == 'buy_order') | (symbol_trade_dataframe['order_type'] == 'short_order')]
        symbol_closePositions_dataframe = symbol_trade_dataframe.loc[(symbol_trade_dataframe['order_type'] == 'sell_order') | (symbol_trade_dataframe['order_type'] == 'cover_order')]

        # filter symbol time(ms)
        symbol_time_openPosition_list = symbol_openPositions_dataframe['receive_trade_time'].values.tolist()
        symbol_time_openPosition_filter_list = []
        for symbol_time_item in symbol_time_openPosition_list:
            hour_minute_second = symbol_time_item.split('.')[0]
            if hour_minute_second not in time_x:
                time_x.append(hour_minute_second)
            symbol_time_openPosition_filter_list.append(hour_minute_second)

        symbol_time_closePosition_list = symbol_closePositions_dataframe['receive_trade_time'].values.tolist()
        symbol_time_closePosition_filter_list = []
        for symbol_time_item in symbol_time_closePosition_list:
            hour_minute_second = symbol_time_item.split('.')[0]
            if hour_minute_second not in time_x:
                time_x.append(hour_minute_second)
            symbol_time_closePosition_filter_list.append(hour_minute_second)

        time_x.sort()
        clean_time_dataframe = pandas.DataFrame({"time_x": time_x})
        clean_time_dataframe.set_index("time_x", inplace=True)
        temp_content_dataframe = content_dataframe.set_index("time_x", inplace=False)
        clean_time_dataframe['price'] = temp_content_dataframe[7]
        clean_time_dataframe.fillna(method="ffill", inplace=True)
        clean_time_dataframe.reset_index(inplace=True)

        pyplot.figure(figsize=(15, 10))
        pyplot.title(f'{symbol}   {datetime.date.today()}')
        pyplot.gca().get_xaxis().set_visible(False)  # 必须为 False, 否则卡死
        # pyplot.plot(content_dataframe['time_x'], content_dataframe[7], alpha=0.75)  # [7]: last_tick
        pyplot.plot(clean_time_dataframe['time_x'], clean_time_dataframe['price'], alpha=0.75)  # [7]: last_tick
        pyplot.scatter(symbol_time_openPosition_filter_list, symbol_openPositions_dataframe['receive_trade_price'].values.tolist(), c='r', marker='o')
        pyplot.scatter(symbol_time_closePosition_filter_list, symbol_closePositions_dataframe['receive_trade_price'].values.tolist(), c='g', marker='x')
        pyplot.savefig(f'pictures/{symbol}.png')


    @staticmethod
    def __tqz_get_symbolString(csv_path_name):
        symbol = csv_path_name.split('.')[0]

        exchange_string = symbol.split('_')[0]
        sym_string = symbol.split('_')[1]
        yearMonth_string = symbol.split('_')[2]

        if exchange_string == "CZCE":
            symbol_string = f'{sym_string}{int(yearMonth_string) % 1000}'
        else:
            symbol_string = f'{sym_string}{yearMonth_string}'

        return symbol_string

    # 从SQLite文件中读取数据
    @classmethod
    def __readFronSqllite(cls, db_path, exectCmd):
        conn = db.connect(db_path)  # 该 API 打开一个到 SQLite 数据库文件 database 的链接，如果数据库成功打开，则返回一个连接对象
        cursor = conn.cursor()  # 该例程创建一个 cursor，将在 Python 数据库编程中用到。
        conn.row_factory = db.Row  # 可访问列信息
        cursor.execute(exectCmd)  # 该例程执行一个 SQL 语句
        return cursor.fetchall()  # 该例程获取查询结果集中所有（剩余）的行，返回一个列表。当没有可用的行时，则返回一个空的列表。


if __name__=="__main__":
    # parser_trade_result_fold_test = "C:\\Users\\HIAPAD\\Desktop\\create_hft_trade_picture\\tqz_hft_parser_app/parser_result_fold/parser_trade_result_20211231"

    TQZHftTradePictureKit.tqz_create_trade_pictures(
        parser_trade_result_fold=TQZHftParserPath.parser_trade_result_fold()
    )

    """
    # 测试数据库是否实时录入数据
    database_path = TQZFilePathOperator.grandfather_path(source_path=__file__) + f'/tqzpy_futures_database/.vntrader/database.db'
    content = readFronSqllite_test(db_path=database_path, exectCmd=f"SELECT * FROM dbtickdata WHERE symbol=='al2203' and datetime>='2022-01-21 08:30:00' and datetime<'2022-01-21 16:00:00';")
    print("content: " + str(content))
    print("lens: " + str(len(content)))
    """

"""
# 测试数据库是否实时录入数据
from tqz_hft_parser_app.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
def readFronSqllite_test(db_path, exectCmd):
    conn = db.connect(db_path)  # 该 API 打开一个到 SQLite 数据库文件 database 的链接，如果数据库成功打开，则返回一个连接对象
    cursor = conn.cursor()  # 该例程创建一个 cursor，将在 Python 数据库编程中用到。
    conn.row_factory = db.Row  # 可访问列信息
    cursor.execute(exectCmd)  # 该例程执行一个 SQL 语句
    return cursor.fetchall()  # 该例程获取查询结果集中所有（剩余）的行，返回一个列表。当没有可用的行时，则返回一个空的列表。
"""


""" discard code...
# 从SQLite文件中读取数据
def readFronSqllite(db_path, exectCmd):
    conn = db.connect(db_path)  # 该 API 打开一个到 SQLite 数据库文件 database 的链接，如果数据库成功打开，则返回一个连接对象
    cursor=conn.cursor()        # 该例程创建一个 cursor，将在 Python 数据库编程中用到。
    conn.row_factory=db.Row     # 可访问列信息
    cursor.execute(exectCmd)    # 该例程执行一个 SQL 语句
    return cursor.fetchall()      # 该例程获取查询结果集中所有（剩余）的行，返回一个列表。当没有可用的行时，则返回一个空的列表。
    #  print(rows[0][2]) # 选择某一列数据

def demo():
    rows = readFronSqllite('C:\\Users\\HIAPAD\\Desktop\\tick数据落地与读取\\database.db', "SELECT * FROM dbtickdata WHERE symbol=='i2205';")
    lineIndex = 100
    readLines = 120
    while lineIndex < readLines:
        row = rows[lineIndex]  # 获取某一行的数据,类型是tuple
        print(row)
        lineIndex += 1
"""
