[1mdiff --git a/main.py b/main.py[m
[1mindex 0ab1824..b4cd005 100755[m
[1m--- a/main.py[m
[1m+++ b/main.py[m
[36m@@ -258,7 +258,7 @@[m [mdef save(case_data):[m
         pickle.dump(case_data, file)[m
 [m
 [m
[31m-def create_graph(iterator):[m
[32m+[m[32mdef create_graph(iterator, showDayNums=False):[m
     x = [int(z) for z in iterator][m
     cum = [x[0]][m
     for i in range(1, len(x)):[m
[36m@@ -274,6 +274,12 @@[m [mdef create_graph(iterator):[m
         plot.plot(dates, [30] * 14, "g--", label="trigger level 1")[m
     plot.xticks(dates, dates, rotation=45)[m
     plot.legend()[m
[32m+[m[32m    # Add individual day labels[m
[32m+[m[32m    if showDayNums:[m
[32m+[m[32m        for i, v in enumerate(x):[m
[32m+[m[32m            if v == 0:[m
[32m+[m[32m                continue[m
[32m+[m[32m            plot.text(i, v, str(v), color="blue", fontweight="bold")[m
     data = BytesIO()[m
     plot.subplots_adjust(bottom=0.17)[m
     plot.ylabel("Number of positive tests")[m
