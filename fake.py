import random

import faker

f = faker.Faker('ru_RU')
print(f.name())
city = ''
while city[:1] != 'г':
    city = f.city()
print(city)
print(random.randint(11, 18))