import baostock as bs
import pandas as pd
from typing import Optional, Dict, Any
import sys
import re

class BaoStockAPI:
    def __init__(self):
        self.bs = bs
        self._initialized = False
    
    async def init(self):
        """异步初始化"""
        if not self._initialized:
            self._login()
            # 测试连接是否正常
            try:
                rs = self.bs.query_stock_basic(code="sh.600000")
                if rs.error_code != '0':
                    raise RuntimeError(f"BaoStock API 测试失败: {rs.error_msg}")
                self._initialized = True
            except Exception as e:
                self._logout()
                raise RuntimeError(f"BaoStock API 初始化失败: {str(e)}")
    
    def _login(self):
        """登录系统"""
        lg = self.bs.login()
        if lg.error_code != '0':
            raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

    def _logout(self):
        """退出登录"""
        self.bs.logout()
    
    def __del__(self):
        """退出登录"""
        if sys is not None and sys.meta_path is not None:
            try:
                print("logout")
                self.bs.logout()
            except Exception as e:
                print(f"Exception during logout: {e}")

    def _validate_stock_code(self, code: str) -> str:
        """
        验证并修正股票代码格式
        正确格式示例：
        - 股票代码：sh.600000, sz.000001
        - 指数代码：sh.000001 (上证指数), sz.399106 (深证综指)
        """
        if not code:
            raise ValueError("代码不能为空")
            
        # 移除所有空白字符
        code = re.sub(r'\s+', '', code)
        
        # 如果已经是正确的格式（sh.或sz.开头，后面跟6位数字），直接返回
        if re.match(r'^(sh|sz)\.\d{6}$', code):
            return code
            
        # 如果只有数字，根据规则添加前缀
        if re.match(r'^\d{6}$', code):
            # 指数代码规则
            if code.startswith('000') or code.startswith('880'):  # 上证指数
                return f'sh.{code}'
            elif code.startswith('399'):  # 深证指数
                return f'sz.{code}'
            # 股票代码规则
            elif code.startswith(('600', '601', '603', '688')):  # 上海证券交易所
                return f'sh.{code}'
            elif code.startswith(('000', '002', '300')):  # 深圳证券交易所
                return f'sz.{code}'
                
        raise ValueError(f"无效的代码格式: {code}。正确格式示例：sh.600000（股票）或sh.000001（指数）")

    def _check_initialized(self):
        """检查是否已初始化"""
        if not self._initialized:
            self._login()

    def get_stock_basic(self, code: str) -> Dict[str, Any]:
        """
        获取证券基本资料
        
        参数:
            code: 股票代码，格式：sh.600000 或 sz.000001
                 上海证券交易所股票代码以sh.开头，深圳证券交易所股票代码以sz.开头
        
        返回:
            包含以下字段的字典:
            code: 证券代码
            code_name: 证券名称
            ipoDate: 上市日期
            outDate: 退市日期
            type: 证券类型，其中1：股票，2：指数，3：其它
            status: 上市状态，其中1：上市，0：退市
            industry: 所属行业
            industryClassification: 行业分类
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        rs = self.bs.query_stock_basic(code=code)
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        self._logout()
        return pd.DataFrame(data_list, columns=rs.fields).to_dict('records')[0]

    def get_history_k_data(self, code: str, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          frequency: str = 'd',
                          adjustflag: str = '3') -> pd.DataFrame:
        """
        获取历史K线数据
        
        参数:
            code: 股票代码，格式：sh.600000 或 sz.000001
                 上海证券交易所股票代码以sh.开头，深圳证券交易所股票代码以sz.开头
            start_date: 开始日期，格式YYYY-MM-DD，默认为None
            end_date: 结束日期，格式YYYY-MM-DD，默认为None
            frequency: 数据类型，默认为d日线
                      d=日k线
                      w=周k线
                      m=月k线
                      5=5分钟线
                      15=15分钟线
                      30=30分钟线
                      60=60分钟线
            adjustflag: 复权类型，默认3
                       1：后复权
                       2：前复权
                       3：不复权
        
        返回:
            包含以下字段的DataFrame：
            date: 交易所行情日期
            code: 证券代码
            open: 开盘价
            high: 最高价
            low: 最低价
            close: 收盘价
            volume: 成交量（累计 单位：股）
            amount: 成交额（单位：人民币元）
            adjustflag: 复权状态(1：后复权，2：前复权，3：不复权）
            turn: 换手率
            tradestatus: 交易状态(1：正常交易，0：停牌）
            pctChg: 涨跌幅（百分比）
            peTTM: 滚动市盈率
            pbMRQ: 市净率
            psTTM: 滚动市销率
            pcfNcfTTM: 滚动市现率
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        fields = "date,code,open,high,low,close,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM"
        rs = self.bs.query_history_k_data_plus(code=code,
                                             fields=fields,
                                             start_date=start_date,
                                             end_date=end_date,
                                             frequency=frequency,
                                             adjustflag=adjustflag)
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields)

    def get_industry_classified(self, code: str = "") -> pd.DataFrame:
        """
        获取行业分类数据
        
        参数:
            code: 股票代码，格式：sh.600000 或 sz.000001
                 上海证券交易所股票代码以sh.开头，深圳证券交易所股票代码以sz.开头
                 默认为空字符串，表示获取所有股票的行业分类数据
        
        返回:
            包含以下字段的DataFrame：
            updateDate: 更新日期
            code: 证券代码
            code_name: 证券名称
            industry: 所属行业
            industryClassification: 行业分类（例如：Industry、Finance等）
        """
        self._check_initialized()
        if code:
            code = self._validate_stock_code(code)
        rs = self.bs.query_stock_industry(code=code)
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields)

    def get_dividend_data(self, code: str, year: str = "", yearType: str = "report") -> pd.DataFrame:
        """
        获取分红派息数据
        
        参数:
            code: 股票代码，格式：sh.600000 或 sz.000001
                 上海证券交易所股票代码以sh.开头，深圳证券交易所股票代码以sz.开头
            year: 年份，格式YYYY，为空时默认全部年份
            yearType: 年份类型，默认为"report"
                     "report":预案公告年份
                     "operate":除权除息年份
                     "dividend":分红年份
        
        返回:
            包含以下字段的DataFrame：
            code: 证券代码
            dividPreNoticeDate: 预批露公告日期
            dividAgmPumDate: 股东大会公告日期
            dividPlanAnnounceDate: 预案公告日期
            dividPlanDate: 预案公告日
            dividRegistDate: 股权登记日期
            dividOperateDate: 除权除息日期
            dividPayDate: 派息日期
            dividStockMarketDate: 红股上市日期
            dividCashPsBeforeTax: 每股股利税前(元)
            dividCashPsAfterTax: 每股股利税后(元)
            dividStocksPs: 每股送股比例
            dividCashStock: 每股转增比例
            dividReserveToStockPs: 每股公积金转增比例
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        rs = self.bs.query_dividend_data(code=code, year=year, yearType=yearType)
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields)

    def get_profit_data(self, code: str, year: int, quarter: int) -> pd.DataFrame:
        """
        获取季度盈利能力数据
        
        参数:
            code: 股票代码，格式：sh.600000 或 sz.000001
                 上海证券交易所股票代码以sh.开头，深圳证券交易所股票代码以sz.开头
            year: 年份，如：2023
            quarter: 季度，可选值：1,2,3,4
                    1表示第一季度财报
                    2表示半年度财报
                    3表示第三季度财报
                    4表示年度财报
        
        返回:
            包含以下字段的DataFrame：
            code: 证券代码
            pubDate: 公司发布财报的日期
            statDate: 财报统计的季度的最后一天
            roeAvg: 净资产收益率(平均)(%)
            npMargin: 销售净利率(%)
            gpMargin: 销售毛利率(%)
            netProfit: 净利润(万元)
            epsTTM: 每股收益TTM(元)
            MBRevenue: 主营营业收入(万元)
            totalShare: 总股本(万股)
            liqaShare: 流通股本(万股)
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        rs = self.bs.query_profit_data(code=code, year=year, quarter=quarter)
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields)

    def get_operation_data(self, code: str, year: int, quarter: int) -> pd.DataFrame:
        """
        获取季度营运能力数据
        
        参数:
            code: 股票代码，格式：sh.600000 或 sz.000001
                 上海证券交易所股票代码以sh.开头，深圳证券交易所股票代码以sz.开头
            year: 年份，如：2023
            quarter: 季度，可选值：1,2,3,4
                    1表示第一季度财报
                    2表示半年度财报
                    3表示第三季度财报
                    4表示年度财报
        
        返回:
            包含以下字段的DataFrame：
            code: 证券代码
            pubDate: 公司发布财报的日期
            statDate: 财报统计的季度的最后一天
            NRTurnRatio: 应收账款周转率(次)
            NRTurnDays: 应收账款周转天数(天)
            INVTurnRatio: 存货周转率(次)
            INVTurnDays: 存货周转天数(天)
            CATurnRatio: 流动资产周转率(次)
            AssetTurnRatio: 总资产周转率(次)
            
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        rs = self.bs.query_operation_data(code=code, year=year, quarter=quarter)
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields)

    def get_growth_data(self, code: str, year: int, quarter: int) -> pd.DataFrame:
        """
        获取季度成长能力数据
        
        参数:
            code: 股票代码，格式：sh.600000 或 sz.000001
                 上海证券交易所股票代码以sh.开头，深圳证券交易所股票代码以sz.开头
            year: 年份，如：2023
            quarter: 季度，可选值：1,2,3,4
                    1表示第一季度财报
                    2表示半年度财报
                    3表示第三季度财报
                    4表示年度财报
        
        返回:
            包含以下字段的DataFrame：
            code: 证券代码
            pubDate: 公司发布财报的日期
            statDate: 财报统计的季度的最后一天
            YOYEquity: 净资产同比增长率(%)
            YOYAsset: 总资产同比增长率(%)
            YOYNI: 净利润同比增长率(%)
            YOYEPSBasic: 基本每股收益同比增长率(%)
            YOYPNI: 归属母公司股东净利润同比增长率(%)
            YOYOperation: 营业总收入同比增长率(%)
        
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        rs = self.bs.query_growth_data(code=code, year=year, quarter=quarter)
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields)

    def get_index_data(self, 
                      code: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      frequency: str = 'd') -> pd.DataFrame:
        """
        获取指数K线数据
        
        参数:
            code: 指数代码，格式示例：
                 sh.000001 (上证指数)
                 sh.000016 (上证50)
                 sh.000300 (沪深300)
                 sh.000905 (中证500)
                 sz.399001 (深证成指)
                 sz.399106 (深证综指)
                 注：指数代码以sh.或sz.开头，后面接6位数字
            start_date: 开始日期，格式YYYY-MM-DD，默认为None
                       如：2023-01-01，不指定则获取2015年至今数据
            end_date: 结束日期，格式YYYY-MM-DD，默认为None
                     如：2023-12-31，不指定则获取至最新交易日数据
            frequency: 数据类型，默认为'd'日线
                      可选值：
                      'd'：日K线
                      'w'：周K线
                      'm'：月K线
                      注：指数数据不提供分钟线级别数据
        
        返回:
            包含以下字段的DataFrame：
            date: 交易所行情日期（格式：YYYY-MM-DD）
            code: 证券代码
            open: 开盘价（精确到小数点后4位）
            high: 最高价（精确到小数点后4位）
            low: 最低价（精确到小数点后4位）
            close: 收盘价（精确到小数点后4位）
            preclose: 前收盘价（精确到小数点后4位）
            volume: 成交量（单位：股）
            amount: 成交额（单位：人民币元）
            pctChg: 涨跌幅（精确到小数点后4位，单位：%）
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        
        # 指数数据字段
        fields = "date,code,open,high,low,close,preclose,volume,amount,pctChg"
        
        # 获取指数K线数据
        rs = self.bs.query_history_k_data_plus(code=code,
                                             fields=fields,
                                             start_date=start_date,
                                             end_date=end_date,
                                             frequency=frequency)
        
        if rs.error_code != '0':
            raise RuntimeError(f"获取指数数据失败: {rs.error_msg}")
            
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
            
        return pd.DataFrame(data_list, columns=rs.fields)

    def get_valuation_data(self,
                          code: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          frequency: str = 'd') -> pd.DataFrame:
        """
        获取股票估值指标数据（日频）
        
        参数:
            code: 股票代码，例如：sh.600000
            start_date: 开始日期，格式YYYY-MM-DD，默认为None
            end_date: 结束日期，格式YYYY-MM-DD，默认为None
            frequency: 数据类型，默认为d日线；d=日k线、w=周、m=月
            
        返回: 包含以下字段的DataFrame：
            date: 交易所行情日期
            code: 证券代码
            close: 收盘价
            peTTM: 滚动市盈率
            pbMRQ: 市净率
            psTTM: 滚动市销率
            pcfNcfTTM: 滚动市现率
        """
        self._check_initialized()
        code = self._validate_stock_code(code)
        
        # 估值指标数据字段
        fields = "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM"
        
        # 获取估值指标数据
        rs = self.bs.query_history_k_data_plus(code=code,
                                             fields=fields,
                                             start_date=start_date,
                                             end_date=end_date,
                                             frequency=frequency,
                                             adjustflag="3")  # 使用不复权数据
        
        if rs.error_code != '0':
            raise RuntimeError(f"获取估值指标数据失败: {rs.error_msg}")
            
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
            
        return pd.DataFrame(data_list, columns=rs.fields) 