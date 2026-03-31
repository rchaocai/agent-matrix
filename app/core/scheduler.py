"""
任务调度服务

使用APScheduler实现Agent的定时调度
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """任务调度服务"""

    def __init__(self, agent_manager=None):
        self.scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
        self.agent_manager = agent_manager
        self.running = False

    async def start(self):
        """启动调度器"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("调度器已启动")

    async def stop(self):
        """停止调度器"""
        if self.running:
            self.scheduler.shutdown(wait=False)
            self.running = False
            logger.info("调度器已停止")

    async def schedule_agent(self, agent_config: dict):
        """调度Agent任务"""
        agent_id = agent_config.get('agent', {}).get('id')
        schedule_config = agent_config.get('agent', {}).get('schedule')

        if not agent_id:
            logger.error("Agent配置缺少id字段")
            return

        if not schedule_config:
            logger.warning(f"Agent {agent_id} 没有配置schedule")
            return

        cron_expr = schedule_config.get('cron')
        if not cron_expr:
            logger.warning(f"Agent {agent_id} 没有配置cron表达式")
            return

        # 获取时区配置（优先使用Agent配置的时区）
        agent_timezone = schedule_config.get('timezone', 'Asia/Shanghai')

        try:
            # 解析cron表达式 "分 时 日 月 周"
            minute, hour, day, month, day_of_week = cron_expr.split()

            self.scheduler.add_job(
                self._execute_agent,
                CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    timezone=agent_timezone
                ),
                id=agent_id,
                args=[agent_id],
                replace_existing=True
            )
            logger.info(f"Agent {agent_id} 已调度: {cron_expr} (时区: {agent_timezone})")
        except Exception as e:
            logger.error(f"调度Agent {agent_id} 失败: {str(e)}")

    async def unschedule_agent(self, agent_id: str):
        """取消Agent调度"""
        try:
            self.scheduler.remove_job(agent_id)
            logger.info(f"Agent {agent_id} 调度已取消")
        except Exception as e:
            logger.warning(f"取消Agent {agent_id} 调度失败: {str(e)}")

    async def _execute_agent(self, agent_id: str):
        """执行Agent任务"""
        if self.agent_manager:
            logger.info(f"开始执行Agent: {agent_id}")
            try:
                await self.agent_manager.run_agent(agent_id)
            except Exception as e:
                logger.error(f"执行Agent {agent_id} 失败: {str(e)}", exc_info=True)

    def get_scheduled_jobs(self) -> List[Dict]:
        """获取所有已调度的任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs

    def get_job_status(self, agent_id: str) -> Optional[Dict]:
        """获取指定Agent的调度状态"""
        try:
            job = self.scheduler.get_job(agent_id)
            if job:
                return {
                    'id': job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
        except Exception:
            pass
        return None
