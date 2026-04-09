import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    cat = client['cat_db']
    ilearn = client['ilearn_db']

    cat_courses = set()
    async for t in cat.trainings.find():
        for gk in ['basic_groups', 'advanced_groups']:
            for g in t.get(gk, []):
                for item in g.get('items', []):
                    for c in item.get('courses', []):
                        cat_courses.add(c)

    ilearn_mapped = set()
    async for c in ilearn.courses.find():
        if c.get('cat_course_name'):
            ilearn_mapped.add(c['cat_course_name'])

    missing = sorted(cat_courses - ilearn_mapped)
    covered = sorted(cat_courses & ilearn_mapped)
    print(f'COVERED ({len(covered)}):')
    for c in covered: print(f'  OK: {c}')
    print(f'\nMISSING ({len(missing)}):')
    for c in missing: print(f'  MISSING: {c}')
    client.close()

asyncio.run(check())
