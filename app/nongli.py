import datetime

import sxtwl
Gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
Zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ShX = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
numCn = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
jqmc = ["冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏",
        "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
        "立冬", "小雪", "大雪"]
ymc = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
rmc = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
       "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
       "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十", "卅一"]
XiZ = ['摩羯', '水瓶', '双鱼', '白羊', '金牛', '双子', '巨蟹', '狮子', '处女', '天秤', '天蝎', '射手']
WeekCn = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]

def nongli():
    today = datetime.date.today()
    day = sxtwl.fromSolar(today.year, today.month, today.day)
    weeknum = WeekCn[day.getWeek()]
    ytg = day.getYearGZ(True)
    nongli = (f"农历{Gan[ytg.tg] + Zhi[ytg.dz]}{ShX[ytg.dz]}年%s%s月%s日" %
              ('闰' if day.isLunarLeap() else '', ymc[day.getLunarMonth() - 1], rmc[day.getLunarDay() - 1]))
    jieqi = ''
    if day.hasJieQi():
        jq = day.getJieQi()
        jq_name = jqmc[day.getJieQi()]
        jd = day.getJieQiJD()
        t = sxtwl.JD2DD(jd)
        jieqi = f'今天是二十四节气中的{jq_name}，具体在今天的 {t.h}:{t.m}:{round(t.s, 2)}。'
    else:
        day2 = day
        for i in range(1, 30):
            day = day.after(1)
            if day.hasJieQi():
                jq_name = jqmc[day.getJieQi()]
                jd = day.getJieQiJD()

                t = sxtwl.JD2DD(jd)
                jieqi = f'还有 {i} 天就是二十四节气的{jq_name}啦！具体在 {t.Y:04d}-{t.M:02d}-{t.D:02} {int(t.h):02d}:{int(t.m):02d}:{round(t.s, 2):02.2f}。'

                break
        day = day2
    return day,weeknum,nongli,jieqi,today

if __name__ == '__main__':
    print(nongli())