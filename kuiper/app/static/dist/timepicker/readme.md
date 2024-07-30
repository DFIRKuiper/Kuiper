# Perfect-DateTimePicker
---

## A jQuery plugin for Date and Time Picker(基于jQuery的日期时间选择器)

**Demo:** [http://jiandaoyun.github.io/Perfect-DateTimePicker/](http://jiandaoyun.github.io/Perfect-DateTimePicker/)

### Features(特性)
0. Simple Interaction.(交互简单)
0. Concise Interface.(界面整洁)
0. Bootstrap Style.(类Bootstrap风格)

### Preview(预览图)
![](https://rawgit.com/jiandaoyun/Perfect-DateTimePicker/master/examples/1.png)
![](https://rawgit.com/jiandaoyun/Perfect-DateTimePicker/master/examples/2.png)
![](https://rawgit.com/jiandaoyun/Perfect-DateTimePicker/master/examples/3.png)
![](https://rawgit.com/jiandaoyun/Perfect-DateTimePicker/master/examples/4.png)
![](https://rawgit.com/jiandaoyun/Perfect-DateTimePicker/master/examples/5.png)
![](https://rawgit.com/jiandaoyun/Perfect-DateTimePicker/master/examples/6.png)
![](https://rawgit.com/jiandaoyun/Perfect-DateTimePicker/master/examples/7.png)

### API(接口)

* options(属性配置)

<table>
<tr><td><b>property(属性)</b></td><td><b>type(类型)</b></td><td><b>description(描述)</b></td></tr>
<tr><td>baseCls</td><td>String</td><td>base class(主样式)</td></tr>
<tr><td>language</td><td>String</td><td>'zh'|'en'</td></tr>
<tr><td>viewMode</td><td>String</td><td>'YM'|'YMD'|'YMDHMS'|'HMS'</td></tr>
<tr><td>startDate</td><td>Date</td><td>start date(起始日期)</td></tr>
<tr><td>endDate</td><td>Date</td><td>end date(结束日期)</td></tr>
<tr><td>date</td><td>Date</td><td>initial date(初始值)</td></tr>
<tr><td>firstDayOfWeek</td><td>Number</td><td>the first Day Of Week,0~6:Sunday~Saturday,default:0(指定每周的第一天，默认周日)</td></tr>
<tr><td>onDateChange</td><td>Function</td><td>date change event(日期修改事件)</td></tr>
<tr><td>onClear</td><td>Function</td><td>clear button click event(清除按钮事件)</td></tr>
<tr><td>onOk</td><td>Function</td><td>ok button click event(确认按钮事件)</td></tr>
<tr><td>onClose</td><td>Function</td><td>close button click event(关闭按钮事件)</td></tr>
</table>

* APIs(调用接口)

<table>
<tr><td><b>function(方法)</b></td><td><b>type(类型)</b></td><td><b>parameters(参数)</b></td><td><b>description(描述)</b></td></tr>
<tr><td>getValue</td><td>Function</td><td>无</td><td>获取当前日期对象</td></tr>
<tr><td>getText</td><td>Function</td><td>format(可选，日期格式，例如: 'YYYY-MM-DD HH:mm:ss')</td><td>获取当前日期的文本格式</td></tr>
<tr><td>destroy</td><td>Function</td><td>无</td><td>销毁对象</td></tr>
<tr><td>element</td><td>Object</td><td>无</td><td>返回选择器的jQuery对象</td></tr>
<tr><td>$datetable</td><td>Object</td><td>无</td><td>返回日期选择面板的jQuery对象</td></tr>
<tr><td>$monthtable</td><td>Object</td><td>无</td><td>返回年月选择面板的jQuery对象</td></tr>
<tr><td>$timetable</td><td>Object</td><td>无</td><td>返回时间选择面板的jQuery对象</td></tr>
</table>

### Example(代码示例)

```javascript
    var picker = $('#demo1').datetimepicker({
        date: new Date(),
        viewMode: 'YMDHMS',
        firstDayOfWeek: 0,
        onDateChange: function(){
            $('#date-text').text(this.getText());
        },
        onClose: function(){
            this.element.remove();
        }
    });
    console.log(picker.getText());
    console.log(picker.getValue());
    picker.element.hide();
```

### Compatible(浏览器兼容性)
IE8+

### License(协议)
[MIT license](https://github.com/jiandaoyun/Perfect-DateTimePicker/blob/master/LICENSE)

