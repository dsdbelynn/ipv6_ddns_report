from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import asyncio

@register("ipv6_ddns_report", "Lynn", "查询用户的 IPv6 地址插件", "1.0.2")
class IPv6Plugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.umo = ""#从本地../data/umo.txt文件中读取
        self.last_ipv6 = "未知"
        self.monitor_task = None
        # 启动监控任务
        self.start_monitor()

    def start_monitor(self):
        """启动IPv6地址监控任务"""
        self.monitor_task = asyncio.create_task(self.monitor_ipv6_changes())
        # 创建一个额外的任务来发送消息，而不是直接await
        asyncio.create_task(self._send_start_notification())
    
    async def _send_start_notification(self):
        """发送启动通知"""
        message_chain = MessageChain().message("IPv6监控任务已启动!")
        await self.context.send_message(self.umo, message_chain)
    
    async def monitor_ipv6_changes(self):
        """定期监控IPv6地址变化的后台任务"""
        while True:
            try:
                # 查询当前IPv6地址
                current_ipv6, error = await self.query_ipv6()
                
                # 如果查询成功且地址发生变化
                if not error and current_ipv6 != self.last_ipv6:
                    old_ipv6 = self.last_ipv6
                    self.last_ipv6 = current_ipv6
                    # 处理地址变化
                    await self.handle_ipv6_change(old_ipv6, current_ipv6)
                
                # 等待5分钟
                await asyncio.sleep(5 * 60)  # 5分钟 = 300秒
            except Exception as e:
                logger.error(f"IPv6监控任务出错: {str(e)}")
                await asyncio.sleep(5)  # 出错后等待5秒再尝试
    
    async def handle_ipv6_change(self, old_ipv6, new_ipv6):
        """处理IPv6地址变化的方法，用户可自行实现具体操作"""
        message_chain = MessageChain().message(f"IPv6地址已变更: {old_ipv6} -> {new_ipv6}")
        await self.context.send_message(self.umo, message_chain)
    
    async def query_ipv6(self):
        """获取IPv6地址的核心功能函数"""
        ipv6_add = "未知"        
        try:
            async with aiohttp.ClientSession() as session:
                # 使用ipify的IPv6 API
                async with session.get('https://api6.ipify.org?format=json', timeout=10) as response:
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
