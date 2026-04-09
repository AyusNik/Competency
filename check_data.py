import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['cat_db']
    
    print("=== CONTENT MAPPINGS ===")
    cms = await db.content_mappings.find().to_list(20)
    for c in cms:
        print(c)
    
    print("\n=== TRAININGS (first 3) ===")
    trainings = await db.trainings.find().to_list(3)
    for t in trainings:
        print(t)

    print("\n=== ILEARN DB COURSES (first 3) ===")
    ilearn_db = client['ilearn_db']
    courses = await ilearn_db.courses.find().to_list(3)
    for c in courses:
        print(c)

    print("\n=== ILEARN DB ASSESSMENTS (first 3) ===")
    assessments = await ilearn_db.assessments.find().to_list(3)
    for a in assessments:
        print(a)

asyncio.run(run())
