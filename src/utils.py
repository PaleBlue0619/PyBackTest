import os,glob,json,json5
import pandas as pd
from typing import Dict, List
from joblib import Parallel, delayed # 多进程

class fromJson:
    def __init__(self, jsonPath: str):   # 默认是一个jsonPath下以日期命名的文件
        self.jsonPath = jsonPath

    @staticmethod
    def getNameList(jsonPath) -> List[str]:
        """获取当前文件目录下有多少指定格式的文件，返回其文件名称"""
        return os.path.basename([i for i in glob.glob(rf"{jsonPath}\*.json")])

    def loadBar(self, symbolCol: str, dateCol: str, timeCol: str, openCol: str, highCol: str, lowCol: str, closeCol: str, volCol: str) -> Dict:
        """批量K线数据导入"""


    def loadInfo(self, symbolCol: str, dateCol: str, openCol: str, highCol: str, lowCol: str, closeCol: str, startDateCol: str, endDateCol: str,
                 fixedStartDate: pd.Timestamp = None, fixedEndDate: pd.Timestamp = None) -> Dict:
        """允许指定fixedStartDate与fixedEndDate进行导入(此时startDateCol与endDateCol均填为空)"""
