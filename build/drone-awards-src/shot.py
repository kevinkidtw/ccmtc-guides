import sys,asyncio
from playwright.async_api import async_playwright
async def main(url,out,w,h,full):
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page(viewport={'width':int(w),'height':int(h)},device_scale_factor=1)
        msgs=[]; pg.on('console',lambda m:msgs.append(m.text)); pg.on('pageerror',lambda e:msgs.append(str(e)))
        await pg.goto(url); await pg.wait_for_timeout(500)
        await pg.screenshot(path=out,full_page=full=='1')
        print(msgs)
        await b.close()
asyncio.run(main(*sys.argv[1:]))
