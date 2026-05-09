"""Task executor"""
from app.config import Config
from app.controller import DeviceController

class TaskExecutor:
    def __init__(self, config: Config, images_dir="images"):
        self.config = config
        self.images_dir = images_dir
        self.controller = None

    def set_controller(self, controller: DeviceController):
        self.controller = controller

    async def execute_task(self, task_name: str) -> bool:
        task = next((t for t in self.config.tasks if t.get('task_name') == task_name), None)
        if not task:
            print(f"Task '{task_name}' not found")
            return False
        
        print(f"Executing task: {task_name}")
        for step in task.get('steps', []):
            print(f"  Step: {step.get('action')}")
            await self._execute_step(step)
        return True

    async def execute_tasks_with_trigger(self, trigger: str):
        results = []
        for task in self.config.tasks:
            if task.get('trigger') == trigger:
                success = await self.execute_task(task.get('task_name'))
                results.append((task.get('task_name'), success))
        return results

    async def _execute_step(self, step):
        action = step.get('action')
        if action == "wait_ms":
            import asyncio
            await asyncio.sleep(step.get('duration_ms', 0) / 1000)
        elif action == "tap":
            if step.get('target_id'):
                print(f"    Tapping target: {step.get('target_id')}")
            elif step.get('start_coord'):
                x, y = step.get('start_coord')
                await self.controller.tap(x, y)
        elif action == "swipe":
            if step.get('start_coord') and step.get('end_coord'):
                sx, sy = step.get('start_coord')
                ex, ey = step.get('end_coord')
                duration = step.get('duration_ms', 300)
                await self.controller.swipe(sx, sy, ex, ey, duration)
        elif action == "input_text":
            if step.get('text'):
                await self.controller.input_text(step.get('text'))
        elif action == "key_event":
            if step.get('keycode'):
                keycode = int(step.get('keycode')) if str(step.get('keycode')).isdigit() else 66
                await self.controller.key_event(keycode)
        elif action == "wait_target":
            print(f"    Waiting for target: {step.get('target_id')}")
            import asyncio
            await asyncio.sleep(2)
        elif action == "long_press":
            if step.get('start_coord'):
                x, y = step.get('start_coord')
                duration = step.get('duration_ms', 1000)
                await self.controller.swipe(x, y, x, y, duration)