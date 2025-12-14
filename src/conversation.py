import asyncio

from app.services.database import db


class Conversation:
    def __init__(self, session_id, agents):
        self.session_id = session_id
        self.running_tasks = dict()
        self.agents = agents

    @property
    def messages(self):
        return db.get_session_messages(session_id=self.session_id)

    async def main_loop(self):
        # 循环接受任意一个agent的执行任务结果
        # 结束后，如果当前session最后说话的agent不是当前agent，则再启动其运行任务

        # ─── Main loop ───────────────────────────────────────────────
        while self.running_tasks:
            done, _ = await asyncio.wait(
                self.running_tasks.keys(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            # process finished jobs
            for fut in done:
                del self.running_tasks[fut]
                result = fut.result()

                self.check_new_running_tasks()

    def check_new_running_tasks(self):
        # 找到当前session里面最后说话的那个agent
        # 遍历所有agent，对除了最后说话的那个agent以外，其他agent，如果他没有运行正在生成的任务，则启动其运行任务任务
        existing_agents = [self.running_tasks[fut] for fut in self.running_tasks]
        last_agent_name = self.messages[-1]['role']
        for agent in self.agents:
            if agent in existing_agents or agent.name == last_agent_name:
                continue

            fut = asyncio.create_task(
                agent(session_id=self.session_id),
                # name=f"job-{agent.name}",
            )
            self.running_tasks[fut] = agent

    def get_newest_file_versions(self):
        # get all file versions belong to the current session id. For each unique file_id, return the one with the latest create_time.
        all_versions = db.get_file_versions(session_id=self.session_id)

        if not all_versions:
            return []

        # Group by file_id and get the latest version for each
        latest_versions = {}
        for version in all_versions:
            file_id = version['file_id']
            if file_id not in latest_versions:
                latest_versions[file_id] = version
            else:
                # Compare create_time and keep the latest
                if version['create_time'] > latest_versions[file_id]['create_time']:
                    latest_versions[file_id] = version

        return list(latest_versions.values())