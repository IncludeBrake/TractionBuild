
import pytest, asyncio
from zerotoship.core.learning_memory import LearningMemory
@pytest.mark.asyncio
async def test_learning_memory_add_search():
    m=LearningMemory()
    await m.add("p1","AI workflow automation")
    res=await m.search("automation")
    assert len(res)==1
    assert "automation" in res[0]["text"]
