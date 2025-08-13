import os
import datetime
from neo4j import AsyncGraphDatabase
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class Neo4jLockManager:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI", "neo4j://neo4j:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD"))
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    async def close(self):
        await self.driver.close()

    async def create_lock(self, idea_text: str, user_id: str, expiration_months=3):
        embedding = self.model.encode(idea_text).tolist()
        expiration = (datetime.date.today() + datetime.timedelta(days=30 * expiration_months)).isoformat()
        
        async with self.driver.session() as session:
            await session.run(
                "CREATE (l:LockedIdea {fingerprint: $embedding, idea: $idea, user_id: $user_id, expiration: date($expiration)})",
                embedding=embedding, idea=idea_text, user_id=user_id, expiration=expiration
            )

    async def check_lock(self, idea_text: str, threshold=0.95) -> tuple[bool, str | None]:
        embedding = self.model.encode(idea_text).tolist()
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (l:LockedIdea) WHERE l.expiration > date() RETURN l.fingerprint AS fp, l.idea AS idea"
            )
            async for record in result:
                sim = cosine_similarity([embedding], [record['fp']])[0][0]
                if sim > threshold:
                    return True, record['idea'] # Locked
            return False, None # Not locked