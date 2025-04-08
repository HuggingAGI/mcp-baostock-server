import logging
import asyncio
from typing import Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from .baostock_api import BaoStockAPI
# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("mcp-baostock.log")
    ],
    force=True
)

logger = logging.getLogger("mcp-baostock")

# 初始化 FastMCP 服务器
mcp = FastMCP(
    "mcp-baostock",
    version="0.1.0",
    description="MCP BaoStock Server for stock data",
    dependencies=["baostock"],
    env_vars={},
    debug=True  # 启用debug模式
)

stock_api = BaoStockAPI()

@mcp.tool()
async def get_current_time() -> str:
    """Get current time"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
async def get_stock_basic(code: str) -> dict:
    """Get stock basic information, including code, name, industry, market, ipodate etc."""
    data = stock_api.get_stock_basic(code)
    return data

@mcp.tool()
async def get_stock_kdata(code: str, start_date: str, end_date: str, frequency: str, adjustflag: str) -> dict:
    """Get stock kdata, including date, open, high, low, close, volume, amount, adjustflag, turn, tradestatus, pctChg, peTTM, pbMRQ, psTTM, pcfNcfTTM"""
    data = stock_api.get_history_k_data(code, start_date, end_date, frequency, adjustflag)
    return data

@mcp.tool()
async def get_industry_info(code: str) -> dict:
    """Get industry information, including code, name, parent_code, parent_name, level, order"""
    data = stock_api.get_industry_classified(code)
    return data

@mcp.tool()
async def get_dividend_info(code: str, year: str) -> dict:
    """Get dividend information, including code, year, yearType, endDate, dividend"""
    data = stock_api.get_dividend_data(code, year)
    return data

@mcp.tool()
async def get_profit_info(code: str, year: str, quarter: str) -> dict:
    """Get profit information, including code, year, quarter, report_type, net_profit, eps, roe, roa, gross_margin, net_margin, net_profit_margin, net_profit_margin_yoy, net_profit_margin_mom, net_profit_margin_qoq, net_profit_margin_qoq_yoy, net_profit_margin_qoq_mom"""
    data = stock_api.get_profit_data(code, year, quarter)
    return data 

@mcp.tool()
async def get_operation_info(code: str, year: str, quarter: str) -> dict:
    """Get operation information, including code, year, quarter, report_type, net_profit, eps, roe, roa, gross_margin, net_margin, net_profit_margin, net_profit_margin_yoy, net_profit_margin_mom, net_profit_margin_qoq, net_profit_margin_qoq_yoy, net_profit_margin_qoq_mom"""
    data = stock_api.get_operation_data(code, year, quarter)
    return data

@mcp.tool()
async def get_growth_info(code: str, year: str, quarter: str) -> dict:
    """Get growth information, including code, year, quarter, report_type, net_profit, eps, roe, roa, gross_margin, net_margin, net_profit_margin, net_profit_margin_yoy, net_profit_margin_mom, net_profit_margin_qoq, net_profit_margin_qoq_yoy, net_profit_margin_qoq_mom"""
    data = stock_api.get_growth_data(code, year, quarter)
    return data

@mcp.tool()
async def get_index_data(code: str, start_date: str, end_date: str, frequency: str) -> dict:
    """Get index kdata, including date, code, open, high, low, close, volume, amount, adjustflag, turn, tradestatus, pctChg, peTTM, pbMRQ, psTTM, pcfNcfTTM"""
    data = stock_api.get_index_data(code, start_date, end_date, frequency)
    return data

@mcp.tool()
async def get_valuation_info(code: str, start_date: str, end_date: str, frequency: str) -> dict:
    """Get valuation information, including date, code, close, peTTM, pbMRQ, psTTM, pcfNcfTTM"""
    data = stock_api.get_valuation_data(code, start_date, end_date, frequency)
    return data


async def run_server():
    """运行 MCP BaoStock 服务器"""
    logger.info("正在初始化 BaoStock 服务器...")
    try:
        # 启动 MCP 服务器
        logger.info("正在启动 MCP BaoStock 服务器...")
        await mcp.run_sse_async()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        await mcp.shutdown()
    except Exception as e:
        logger.error(f"Server failed: {e}")
        raise
    finally:
        logger.info("Server shutdown complete") 

def main():
    """Start the BaoStock MCP server."""
    try:
        print("BaoStock MCP Server")
        print("Starting server... Press Ctrl+C to exit")
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Server stopped.")
