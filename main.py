from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import asyncio

@register("ipv6_ddns_report", "Lynn", "查询用户的 IPv6 地址插件", "1.0.0")
class IPv6Plugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    @filter.command("ipv6地址")
    async def print_ipv6(self, event: AstrMessageEvent):
        '''这是一个查询IPV6的指令'''
        # 先发送一条开始查询的消息
        yield event.plain_result("开始查询您的 IPv6 地址...")
        
        ipv6_add = "未知"

        retries = 0
        max_retries = 3
        
        while retries < max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    # 使用ipify的IPv6 API
                    async with session.get('https://api6.ipify.org?format=json', timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'ip' in data and data['ip']:
                                ipv6_add = data['ip']
                                break
            except Exception as e:
                # 可以添加简单的错误分类处理
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    yield event.plain_result(f"第{retries + 1}次查询超时，稍后重试...")
                else:
                    yield event.plain_result(f"第{retries + 1}次查询出错: {error_msg}")
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(1)
        yield event.plain_result(f"您的IPv6地址是: {ipv6_add}")
        

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
