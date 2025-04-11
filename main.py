from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import asyncio

@register("ipv6_ddns_report", "Lynn", "查询用户的 IPv6 地址插件", "1.0.1")
class IPv6Plugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    async def query_ipv6(self):
        """获取IPv6地址的核心功能函数"""
        ipv6_add = "未知"        
        try:
            async with aiohttp.ClientSession() as session:
                # 使用ipify的IPv6 API
                async with session.get('https://api6.ipify.org?format=json', timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'ip' in data and data['ip']:
                            ipv6_add = data['ip']

        except Exception as e:
            error_msg = str(e)
            error_type = "超时" if "timeout" in error_msg.lower() else f"错误: {error_msg}"
            return ipv6_add, error_type
                
        return ipv6_add, None
    
    @filter.command("ipv6地址")
    async def print_ipv6(self, event: AstrMessageEvent):
        '''这是一个查询IPV6的指令'''
        # 先发送一条开始查询的消息
        yield event.plain_result("开始查询您的 IPv6 地址...")
        
        retries = 0
        max_retries = 3
        
        while retries < max_retries:
            ipv6_add, error = await self.query_ipv6()
            
            if error:
                yield event.plain_result(f"第{retries + 1}次查询{error}，稍后重试...")
                retries += 1
                if retries < max_retries:
                    await asyncio.sleep(1)
            else:
                yield event.plain_result(f"您的IPv6地址是: {ipv6_add}")
                break
        
        if retries == max_retries:
            yield event.plain_result(f"查询失败，您的IPv6地址是: {ipv6_add}")
        

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
