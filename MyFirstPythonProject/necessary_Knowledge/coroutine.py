import time
import asyncio #导入协程库

@asyncio.coroutine #修饰器——表明函数协程运行
def taskIO_1():
    print("开始运行IO任务1...")
    yield from asyncio.sleep(2) #利用生成器增加断点
    print("IO任务1已完成，耗时2s")
    return taskIO_1().__name__

@asyncio.coroutine
#生成另一个相同的任务
# @asyncio.coroutine可以用在函数前面加async代替 async def taskIO_2():
def taskIO_2():
    print("开始运行IO任务2...")
    yield from asyncio.sleep(3) # yield from 可以用await代替 await asyncio.sleep(3)
    print("IO任务2已完成，耗时3s")
    return taskIO_2().__name__

@asyncio.coroutine
def main(): #调用函数
    tasks=[taskIO_1(),taskIO_2()] #打包任务
    done,pending=yield from asyncio.wait(tasks) #子生成器
    for r in done:
        print("协程无序返回值："+r.result())

if __name__=='__main__':
    start=time.time()
    loop=asyncio.get_event_loop() #创建一个时间循环对象
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
    print("所有IO任务总耗时%.5f秒" % float(time.time()-start))


