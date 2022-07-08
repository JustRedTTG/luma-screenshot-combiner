import os, threading
from PIL import Image
from ftplib import FTP

size_bot = (320, 240)
size_top = (400, 240)

if os.path.exists('con.txt'): # check if it's saved
    with open('con.txt', 'r') as f: ip, port = f.read().split(':')
else:
    ip, port = input('3ds ip: '), input('3ds ftp port: ')
    with open('con.txt', 'w') as f: f.write(f'{ip}:{port}')

if os.path.exists('secure.txt'): # check if it's saved
    with open('secure.txt', 'r') as f: user, password = f.read().split(', ')
else:
    user, password = input('3ds ftp user: '), input('3ds ftp password: ')
    with open('secure.txt', 'w') as f: f.write(f'{user}, {password}')

ftp = FTP(user=user, passwd=password)
ftp.connect(ip, int(port))

ftp.login()

ftp.cwd('luma/screenshots')

if not os.path.exists('screenshots'): os.mkdir('screenshots')
os.chdir('screenshots/')

files = []
ftp.retrlines('NLST', files.append)
threads = 0

free_slots = []
done = 0
def get_file(file):
    global threads, done
    threads += 1

    if len(free_slots) > 0:
        ftp = free_slots[0]
        del free_slots[0]
    else:
        ftp = FTP(user=user, passwd=password)
        ftp.connect(ip, int(port))
        ftp.login()
    with open(file.replace('/luma/screenshots/', './'), 'wb') as f:
        ftp.retrbinary(f'RETR {file}', f.write)

    free_slots.append(ftp)
    done += 1
    threads -= 1

def delete_file(file):
    global threads, done
    threads += 1

    if len(free_slots) > 0:
        ftp = free_slots[0]
        del free_slots[0]
    else:
        ftp = FTP(user=user, passwd=password)
        ftp.connect(ip, int(port))
        ftp.login()

    ftp.delete(file)

    free_slots.append(ftp)
    done += 1
    threads -= 1

ftp.close()
maxthreads = 4
for file in files:
    while threads >= maxthreads: pass
    threading.Thread(target=get_file, args=(file,)).start()
    print(f'\r got: {done}/{len(files)}, threads: {threads}', end='')
print('\n')
done = 0
for file in files:
    while threads >= maxthreads: pass
    threading.Thread(target=delete_file, args=(file,)).start()
    print(f'\rDeleted: {done}/{len(files)}, threads: {threads}', end='')

for ftp in free_slots:
    ftp.close()

print('\nYou can disconnect the ftp now')
os.chdir(f'{os.getcwd()}/../')
if not os.path.exists('combined'): os.mkdir('combined')

combines = []
tops = []
bots = []
lonely_tops = []
lonely_bots = []

for file in os.listdir('screenshots'):
    if file.endswith('top.bmp'): tops.append(file)
    elif file.endswith('bot.bmp'): bots.append(file)

# combine
for top in tops:
    if top.replace('top','bot') in bots:
        combines.append(top.removesuffix('_top.bmp'))
        bots.remove(top.replace('top','bot'))
    else: lonely_tops.append(top)
lonely_bots = bots

print(f'''\
Total images to combine: {len(combines)}
Lonely top images: {len(lonely_tops)}
Lonely bottom images: {len(lonely_bots)}
''')
done = 0
for filename in combines:
    final = Image.new('RGB', (max(size_top[0], size_bot[0]), size_top[1] + size_bot[1]))

    top = Image.open(f'screenshots/{filename}_top.bmp')
    top = top.resize(size_top)

    bot = Image.open(f'screenshots/{filename}_bot.bmp')
    bot = bot.resize(size_bot)

    final.paste(top, (0, 0))
    final.paste(bot, (int(size_top[0]/2 - size_bot[0]/2), size_top[1]))

    final.save(f'combined/{filename}.png')
    #
    done += 1
    print(f'\r combined: {done}/{len(combines)}', end='')
