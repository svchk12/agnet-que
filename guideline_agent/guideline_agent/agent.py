from google.adk.agents import SequentialAgent

from .sub_agents.summary import summary_agent
from .sub_agents.checklist import checklist_agent

root_agent = SequentialAgent(
    name="guideline_agent",
    description="가이드라인 문서를 요약하고 체크리스트를 생성하는 에이전트입니다.",
    sub_agents=[summary_agent, checklist_agent]
)