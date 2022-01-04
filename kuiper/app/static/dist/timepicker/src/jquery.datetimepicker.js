(function (factory) {
    /* global define */
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define(['jquery'], factory);
    } else {
        // Browser globals: jQuery
        factory(window.jQuery);
    }
}(function ($) {

    /**
     * constructor
     * @param element
     * @param options
     * @returns {{}}
     */
    function DateTimePicker(element, options) {
        var picker = {},
            CONSTS = $.fn.datetimepicker.CONSTS,
            NAV = CONSTS.NAV,
            I18N = (CONSTS.I18N[options.language]) ? CONSTS.I18N[options.language] : CONSTS.I18N['en'],
            cache = {
                showYear: null,
                showMonth: null
            },
            currentDate = (options.date instanceof Date) ? new Date(options.date.getTime()) : null,
            firstDayOfWeek = options.firstDayOfWeek,
            $el = $(element),
            $datetable, //D(date) panel
            $monthtable, //YM(year and month) panel
            $timetable, //T(time) panel

            /**
             * calculate thu number of days in one month
             * @param date {Date} date
             * @param month {Number} month
             * @private
             */
            utilsGetMonthDays = function (date, month) {
                var MD = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
                var year = date.getFullYear();
                if (month == null) {
                    month = date.getMonth();
                }
                if (((0 === (year % 4)) && ((0 !== (year % 100)) || (0 === (year % 400)))) && month === 1) {
                    return 29;
                } else {
                    return MD[month];
                }
            },

            utilsIsEmpty = function (value) {
                return value === "" || value == null;
            },

            utilsApplyFunc = function (obj, func, param, defaultValue) {
                if ($.isFunction(func)) {
                    return func.apply(obj, param ? param : []);
                }
                return defaultValue;
            },

            /**
             * 让字符串通过指定字符做补齐的函数
             *
             * @param text {String}  原始字符串
             * @param size {Number}  总共需要的位数
             * @param ch {String}  用于补齐的字符
             * @return {String}  补齐后的字符串
             */
            utilsLeftPad = function (text, size, ch) {
                var result = text + '';
                if (!ch) {
                    ch = " ";
                }
                while (result.length < size) {
                    result = ch + result;
                }
                return result.toString();
            },

            /**
             * 日期格式解析
             * @param format {JSON} 日期格式内容
             * @param date {Date} 日期对象
             * @returns {String} 返回日期字符串
             */
            _compileDateFormat = function (format, date) {
                var str = format.str, len = format.len, ch = format['char'];
                switch (ch) {
                    case 'Y': //年
                        if (len <= 3) {
                            str = (date.getFullYear() + '').slice(2, 4);
                        } else {
                            str = date.getFullYear();
                        }
                        break;
                    case 'M': //月
                        if (len > 2) {
                            str = CONSTS.MN[date.getMonth()];
                        } else if (len < 2) {
                            str = date.getMonth() + 1;
                        } else {
                            str = utilsLeftPad(date.getMonth() + 1, 2, '0');
                        }
                        break;
                    case 'D': //日
                        if (len > 1) {
                            str = utilsLeftPad(date.getDate(), 2, '0');
                        } else {
                            str = date.getDate();
                        }
                        break;
                    case 'h': //时(12)
                        var hour = date.getHours() % 12;
                        if (hour === 0) {
                            hour = 12;
                        }
                        if (len > 1) {
                            str = utilsLeftPad(hour, 2, '0');
                        } else {
                            str = hour;
                        }
                        break;
                    case 'H': //时(24)
                        if (len > 1) {
                            str = utilsLeftPad(date.getHours(), 2, '0');
                        } else {
                            str = date.getHours();
                        }
                        break;
                    case 'm':
                        if (len > 1) {
                            str = utilsLeftPad(date.getMinutes(), 2, '0');
                        } else {
                            str = date.getMinutes();
                        }
                        break;
                    case 's':
                        if (len > 1) {
                            str = utilsLeftPad(date.getSeconds(), 2, '0');
                        } else {
                            str = date.getSeconds();
                        }
                        break;
                    default:
                        str = format.str;
                        break;
                }
                return str;
            },

            /**
             * 日期对象按照指定格式转化成字符串
             * e.g. Thu Dec 12 2013 00:00:00 GMT+0800 + 'yyyy-MM-dd' --> '2013-12-12'
             * @param {Date} date 日期对象
             * @param {String} format 日期格式
             * @return {String} 返回日期字符串
             */
            utilsDate2str = function (date, format) {
                if (!date) {
                    return '';
                }
                var len = format.length, result = '';
                if (len > 0) {
                    var flagch = format.charAt(0), start = 0, str = flagch;
                    for (var i = 1; i < len; i++) {
                        var ch = format.charAt(i);
                        if (flagch !== ch) {
                            result += _compileDateFormat({
                                'char': flagch,
                                'str': str,
                                'len': i - start
                            }, date);
                            flagch = ch;
                            start = i;
                            str = flagch;
                        } else {
                            str += ch;
                        }
                    }
                    result += _compileDateFormat({
                        'char': flagch,
                        'str': str,
                        'len': len - start
                    }, date);
                }
                return result;
            },

            /**
             * create button cell
             * @param tr {$} tr
             * @param text {String} text
             * @param colspan {Number} colspan
             * @param nav {Number} nav key
             * @param cls {String} class
             * @returns {*} return td dom
             * @private
             */
            _createCell = function ($tr, text, colspan, nav, cls) {
                var $cell = $('<td/>')
                    .attr('colspan', colspan)
                    .html(text)
                    .appendTo($tr);
                if (nav) {
                    $cell.data('nav', nav);
                }
                $cell.addClass(cls);
                return $cell;
            },

            /**
             * create D panel
             * @param options
             * @returns {jQuery}
             * @private
             */
            _createDatePicker = function () {
                var $table = $('<table cellspacing = "2px" cellpadding = "0" class="dt"/>');
                var $thead = $('<thead/>').appendTo($table);
                //head
                //head - tools
                var $row = $('<tr class = "mainhead"/>');
                //head - tools - next month
                $table.$prevm = _createCell($row, '<i class="icon-datepicker-prev"/>', 1, NAV['prevm'], "prevm");
                //head - tools - title
                $table.$title = $('<td class="title" colspan="5"/>').data('nav', NAV['title']).appendTo($row);
                //head - tools - prev month
                $table.$nextm = _createCell($row, '<i class="icon-datepicker-next"/>', 1, NAV['nextm'], "nextm");
                $row.appendTo($thead);
                //head - week names
                $row = $('<tr/>');
                var i;
                for (i = 0; i < 7; ++i) {
                    var $fdcell = $('<td/>').appendTo($row);
                    var dd = (i + firstDayOfWeek) % 7;
                    $fdcell.addClass('day name').text(I18N.SDN[dd]);
                    if (dd === 0 || dd === 6) { //Saturday, Sunday
                        $fdcell.addClass("weekend");
                    }
                }
                $row.appendTo($thead);
                //body
                var $tbody = $('<tbody onselectstart="return false;"/>').appendTo($table);
                for (i = 6; i > 0; i--) {
                    var $bodyRow = $('<tr/>').appendTo($tbody);
                    for (var t = 0; t < 7; t++) {
                        $('<td/>').appendTo($bodyRow);
                    }
                }
                return $table;
            },

            /**
             * create YM panel
             * @private
             */
            _createMonthPicker = function () {
                var $table = $('<table cellspacing = "2px" cellpadding = "0" class="mt"/>');
                //tbody
                var $tbody = $('<tbody/>').appendTo($table);
                //tbody - tools
                var $row = $('<tr/>').appendTo($tbody);
                for (var n = 0; n < 2; n++) {
                    $('<td class="month"/>').appendTo($row);
                }
                //tbody - 翻年按钮
                _createCell($row, '<i class="icon-datepicker-prev"/>', 1, NAV['prevy'], ' prevy');
                _createCell($row, '<i class="icon-datepicker-next"/>', 1, NAV['nexty'], ' nexty');
                //tbody - years
                for (var m = 0; m < 5; m++) {
                    $row = $('<tr/>').appendTo($tbody);
                    $('<td class="month"/><td class="month"/>' +
                        '<td class="year"/><td class="year"/>').appendTo($row);
                }
                //foot - buttons
                var $tfoot = $('<tfoot class="buttonpane"/>').appendTo($table);
                $row = $('<tr/>').appendTo($tfoot);
                //tbody - 确定与取消
                _createCell($row, I18N["OK"], 4, NAV['mok'], 'ok');
                return $table;
            },

            /**
             * Create a table containing the buttons.
             * @return {jQuery}
             * @private
             */
            _createButtonPane = function () {
                var $buttonpane = $('<table class="buttonpane"/>');
                var $row = $('<tr/>');
                // clear button
                _createCell($row, I18N["CLEAR"], null, NAV['clear'], 'clear');
                // today button
                _createCell($row, I18N["TODAY"], null, NAV['today'], 'today');
                // ok button
                _createCell($row, I18N["OK"], null, NAV['dok'], 'ok');
                $row.appendTo($buttonpane);
                return $buttonpane;
            },

            /**
             * go to prev month
             * @private
             */
            _toPrevMonth = function () {
                var sd = options.startDate, date = currentDate;
                var month = cache.showMonth,
                    year = cache.showYear;
                if (!sd) {
                    if (month > 0) {
                        _setMonth(month - 1);
                    } else {
                        date.setFullYear(year - 1);
                        _setMonth(11);
                    }
                    return;
                }
                if (year > sd.getFullYear()) {
                    if (month > 0) {
                        _setMonth(month - 1);
                    } else {
                        date.setFullYear(year - 1);
                        _setMonth(11);
                    }
                } else if (year == sd.getFullYear()) {
                    if (month > sd.getMonth() && month > 0) {
                        _setMonth(month - 1);
                        if (date < sd) {
                            currentDate = new Date(sd);
                        }
                    }
                }
            },

            /**
             * go to next month
             * @private
             */
            _toNextMonth = function () {
                var edd = options.endDate, date = currentDate;
                var month = cache.showMonth,
                    year = cache.showYear;
                if (!edd) {
                    if (month < 11) {
                        _setMonth(month + 1);
                    } else {
                        date.setFullYear(year + 1);
                        _setMonth(0);
                    }
                    return;
                }
                if (year < edd.getFullYear()) {
                    if (month < 11) {
                        _setMonth(month + 1);
                    } else {
                        date.setFullYear(year + 1);
                        _setMonth(0);
                    }
                } else if (year == edd.getFullYear()) {
                    if (month < edd.getMonth()) {
                        _setMonth(month + 1);
                        if (date > edd) {
                            currentDate = new Date(edd);
                        }
                    }
                }
            },

            /**
             * go to prev 10 years
             * @private
             */
            _toPrevDecade = function () {
                var sd = options.startDate, date = currentDate;
                var year = date.getFullYear() - 10, month = date.getMonth();
                var minMonth, minYear;
                if (sd && year == (minYear = sd.getFullYear())) {
                    minMonth = sd.getMonth();
                }
                if (!minYear || minYear < CONSTS.MINYEAR) {
                    minYear = CONSTS.MINYEAR;
                }
                if (year < minYear) {
                    date.setFullYear(minYear);
                    if (month < minMonth) {
                        date.setMonth(minMonth);
                    }
                } else {
                    date.setFullYear(year);
                }
            },

            /**
             * go to next 10 years
             * @private
             */
            _toNextDecade = function () {
                var edd = options.endDate, date = currentDate;
                var year = date.getFullYear() + 10, month = date.getMonth();
                var maxMonth, maxYear;
                if (edd && year == (maxYear = edd.getFullYear())) {
                    maxMonth = edd.getMonth();
                }
                if (!maxYear || maxYear > CONSTS.MAXYEAR) {
                    maxYear = CONSTS.MAXYEAR;
                }
                if (year > maxYear) {
                    date.setFullYear(maxYear);
                    if (month < maxMonth) {
                        date.setMonth(maxMonth);
                    }
                } else {
                    date.setFullYear(year);
                }
            },

            _setMonth = function (m) {
                var date = currentDate;
                var day = date.getDate(),
                    edd = options.endDate,
                    std = options.startDate;
                var max = utilsGetMonthDays(date, m);
                if (day > max) {
                    date.setDate(max);
                }
                date.setMonth(m);
                if (edd && date > edd) {
                    date.setDate(edd.getDate());
                }
                if (std && date < std) {
                    date.setDate(std.getDate());
                }
            },

            /**
             * load data on D panel
             * @param table {$} DOM
             * @param date {Date} current date
             * @private
             */
            _loadDateData = function (table, date) {
                if (!date) {
                    return;
                }
                var year = date.getFullYear(),
                    month = date.getMonth(),
                    day = date.getDate();
                var today = new Date(),
                    TY = today.getFullYear(),
                    TM = today.getMonth(),
                    TD = today.getDate();
                cache.showYear = year;
                cache.showMonth = month;
                var std = options.startDate,
                    edd = options.endDate;
                //set title
                table.$title.text(I18N.MN[month] + ", " + year);
                //set button
                var nextDay = new Date(date);
                nextDay.setDate(utilsGetMonthDays(nextDay, null) + 1);
                if ((edd && nextDay > edd) || nextDay.getFullYear() > CONSTS.MAXYEAR) {
                    table.$nextm.addClass('disabled').removeClass('hover').data('disabled', true);
                } else {
                    table.$nextm.removeClass('disabled').data('disabled', false);
                }
                var prevDay = new Date(date);
                prevDay.setDate(0);
                if ((std && prevDay < std) || prevDay.getFullYear() < CONSTS.MINYEAR) {
                    table.$prevm.addClass('disabled').removeClass('hover').data('disabled', true);
                } else {
                    table.$prevm.removeClass('disabled').data('disabled', false);
                }
                //set date
                date.setDate(1);
                var day1 = (date.getDay() - firstDayOfWeek) % 7;
                date.setDate(0 - day1);
                date.setDate(date.getDate() + 1);
                var $frow = table.find('tbody').children().eq(0);
                //set td date
                for (var i = 0; i < 6; i++) {
                    if (!$frow.length) {
                        break;
                    }
                    var $cells = $frow.children();
                    var iday;
                    for (var j = 0; j < 7; ++j, date.setDate(iday + 1)) {
                        var $cell = $cells.eq(j);
                        $cell.removeClass().data('nav', NAV['day']);
                        if (!$cell.length) {
                            break;
                        }
                        iday = date.getDate();
                        $cell.text(iday);
                        var current_month = (date.getMonth() == month);
                        if (!current_month) {
                            $cell.addClass('oday').data('disabled', true);
                            continue;
                        }
                        var disabled = false;
                        if ((std != null && std > date) || (edd != null && edd < date)) {
                            //out of date range
                            $cell.addClass('day disabled');
                            disabled = true;
                        } else {
                            //in date range
                            $cell.addClass('day');
                        }
                        $cell.data('disabled', disabled);
                        if (!disabled) {
                            if (current_month && iday == day) {
                                cache.selectedDate && cache.selectedDate.removeClass('selected');
                                $cell.addClass('selected');
                                cache.selectedDate = $cell;
                                cache.showDay = iday;
                            }
                            if (date.getFullYear() == TY &&
                                date.getMonth() == TM &&
                                iday == TD) {
                                $cell.addClass('today');
                            }
                            var wday = date.getDay();
                            if (wday === 0 || wday === 6) {
                                $cell.addClass("weekend");
                            }
                        }
                    }
                    $frow = $frow.next();
                }
            },

            /**
             * load data on YM panel
             * @param table {$} DOM
             * @param date {Date} current date
             * @private
             */
            _loadMonthData = function (table, date) {
                if (!date) {
                    return;
                }
                var year = date.getFullYear(), month = date.getMonth();
                var midyear = $(table).data('midYear');
                if (!midyear) {
                    midyear = year;
                } else {
                    if (year > midyear + 5) {
                        midyear += 10;
                    } else if (year < midyear - 4) {
                        midyear -= 10;
                    }
                }
                $(table).data('midYear', midyear);
                var years = [midyear - 4, midyear - 3, midyear - 2, midyear - 1, midyear,
                    midyear + 1, midyear + 2, midyear + 3, midyear + 4, midyear + 5];
                var ycells = $("td.year", table);
                var mcells = $("td.month", table);
                var ed = options.endDate;
                var sd = options.startDate;
                var maxYear, maxMonth, minYear, minMonth;
                //end date
                if (ed) {
                    if (ed && year == (maxYear = ed.getFullYear())) {
                        maxMonth = ed.getMonth();
                    }
                }
                if (!maxYear || maxYear > CONSTS.MAXYEAR) {
                    maxYear = CONSTS.MAXYEAR;
                }
                //start date
                if (sd) {
                    if (sd && year == (minYear = sd.getFullYear())) {
                        minMonth = sd.getMonth();
                    }
                }
                if (!minYear || minYear < CONSTS.MINYEAR) {
                    minYear = CONSTS.MINYEAR;
                }
                //load 12 months
                for (var i = 0; i < 12; i++) {
                    var $mcell = mcells.eq(i).text(I18N.MN[i])
                        .data('nav', NAV['month']).data('month', i);
                    if (i == month) {
                        cache.selectedMonth && cache.selectedMonth.removeClass('selected');
                        $mcell.addClass("selected");
                        cache.selectedMonth = $mcell;
                    }
                    if ((!utilsIsEmpty(minMonth) && i < minMonth) || (!utilsIsEmpty(maxMonth) && i > maxMonth)) {
                        $mcell.addClass("disabled").data('disabled', true);
                    } else {
                        $mcell.removeClass("disabled").data('disabled', false);
                    }
                    //一页可显示的10年数据加载
                    if (i < 10) {
                        var $ycell = ycells.eq(i).text(years[i]).data('nav', NAV['year']);
                        if (years[i] == year) {
                            cache.selectedYear && cache.selectedYear.removeClass('selected');
                            $ycell.addClass("selected");
                            cache.selectedYear = $ycell;
                        }
                        if ((!utilsIsEmpty(minYear) && years[i] < minYear) || (!utilsIsEmpty(maxYear) && years[i] > maxYear)) {
                            $ycell.addClass("disabled").data('disabled', true);
                        } else {
                            $ycell.removeClass("disabled").data('disabled', false);
                        }
                    }
                }
                //do page up
                var $prev = $("td.prevy", table).removeClass('disabled').data('disabled', false);
                if (years[0] <= minYear) {
                    $prev.addClass("disabled").data('disabled', true).removeClass('hover');
                }
                //do page down
                var $next = $("td.nexty", table).removeClass('disabled').data('disabled', false);
                if (years[9] >= maxYear) {
                    $next.addClass("disabled").data('disabled', true).removeClass('hover');
                }
            },

            /**
             * Transfer date values into UI inputs.
             * @param {Object} table The time table object.
             * @param {Date} date The date
             * @param {String} viewmode The datetimepicker's view mode.
             */
            _loadTimeData = function (table, date, viewmode) {
                if (!date) {
                    table.$h.val('00');
                    table.$m.val('00');
                    table.$s.val('00');
                    return;
                }

                // Reset seconds if they are not relevant.
                if (viewmode == CONSTS.VIEWMODE.HM || viewmode == CONSTS.VIEWMODE.YMDHM) {
                    date.setSeconds(0);
                }

                var hour = date.getHours() + '',
                    minute = date.getMinutes() + '',
                    second = date.getSeconds() + '';
                table.$h.val(utilsLeftPad(hour, 2, '0'));
                table.$m.val(utilsLeftPad(minute, 2, '0'));
                table.$s.val(utilsLeftPad(second, 2, '0'));
            },

            /**
             * do time increase
             * @param {Object} timetable T panel DOM
             * @param {Object} input time input
             * @private
             */
            _doTimeInc = function (timetable, input) {
                var inputType = input.data('time');
                if (inputType === 'h') {
                    var hours = (currentDate.getHours() + 1) % 24;
                    currentDate.setHours(hours);
                    timetable.$h.val(utilsLeftPad(hours, 2, '0'));
                } else if (inputType === 'm') {
                    var minutes = (currentDate.getMinutes() + 5) % 60;
                    currentDate.setMinutes(minutes);
                    timetable.$m.val(utilsLeftPad(minutes, 2, '0'));
                } else {
                    var seconds = (currentDate.getSeconds() + 5) % 60;
                    currentDate.setSeconds(seconds);
                    timetable.$s.val(utilsLeftPad(seconds, 2, '0'));
                }
                input.select();
                utilsApplyFunc(picker, options.onDateChange, arguments, false);
            },
            /**
             * do time decrease
             * @param {Object} timetable T panel DOM
             * @param {Object} input time input
             * @private
             */
            _doTimeDec = function (timetable, input) {
                var inputType = input.data('time');
                if (inputType === 'h') {
                    var hours = (currentDate.getHours() + 23) % 24;
                    currentDate.setHours(hours);
                    timetable.$h.val(utilsLeftPad(hours, 2, '0'));
                } else if (inputType === 'm') {
                    var minutes = (currentDate.getMinutes() + 55) % 60;
                    currentDate.setMinutes(minutes);
                    timetable.$m.val(utilsLeftPad(minutes, 2, '0'));
                } else {
                    var seconds = (currentDate.getSeconds() + 55) % 60;
                    currentDate.setSeconds(seconds);
                    timetable.$s.val(utilsLeftPad(seconds, 2, '0'));
                }
                input.select();
                utilsApplyFunc(picker, options.onDateChange, arguments, false);
            },

            /**
             * Make sure a number is between a minimum and a maximum
             */
            clampNumber = function (value, min, max) {
                return isNaN(value) ? min : Math.min(max, Math.max(min, value));
            },

            /**
             * create the time picker row containing the individual time input fields
             * @param {String} viewmode One of the constants VIEWMODE.XXX
             */
            _createTimePicker = function (viewmode) {
                var $table = $('<table cellspacing = "0" cellpadding = "0" class="tt"/>');
                var $tbody = $('<tbody>').appendTo($table);
                $table.$h = $('<input type="number" min="0" max="23" maxlength="2"/>').data('time', 'h').change(function () {
                    var value = parseInt(this.value, 10);
                    var hours = clampNumber(value, 0, 23);
                    // Replace the value if it has not been not a valid number
                    if (value != hours) {
                        this.value = hours;
                    }
                    currentDate.setHours(hours);
                    utilsApplyFunc(picker, options.onDateChange, arguments);
                }).focus(function () {
                    $table.focus = $(this);
                });
                $table.$m = $('<input type="number" min="0" max="59" maxlength="2"/>').data('time', 'm').change(function () {
                    var value = parseInt(this.value, 10);
                    var minutes = clampNumber(value, 0, 59);
                    // Replace the value if it has not been not a valid number
                    if (value != minutes) {
                        this.value = minutes;
                    }
                    currentDate.setMinutes(minutes);
                    utilsApplyFunc(picker, options.onDateChange, arguments);
                }).focus(function () {
                    $table.focus = $(this);
                });
                $table.$s = $('<input type="number" min="0" max="59" maxlength="2"/>').data('time', 's').change(function () {
                    var value = parseInt(this.value, 10);
                    var seconds = clampNumber(value, 0, 59);
                    // Replace the value if it has not been not a valid number
                    if (value != seconds) {
                        this.value = seconds;
                    }
                    currentDate.setSeconds(seconds);
                    utilsApplyFunc(picker, options.onDateChange, arguments);
                }).focus(function () {
                    $table.focus = $(this);
                });
                $table.focus = $table.$m;
                var $add = $('<td/>').append($('<i class="icon-datepicker-plus"/>')).data('nav', NAV['plus']);
                var $min = $('<td/>').append($('<i class="icon-datepicker-minus"/>')).data('nav', NAV['minus']);
                var $row = $('<tr/>').append($('<td rowspan="2"/>').text(I18N.TIME))
                    .append($('<td rowspan="2"/>').append($table.$h))
                    .append($('<td class="common" rowspan="2"/>').text(':'))
                    .append($('<td rowspan="2"/>').append($table.$m));

                // Only add the seconds input if it's requested
                if (viewmode != CONSTS.VIEWMODE.YMDHM && viewmode != CONSTS.VIEWMODE.HM) {
                    $row.append($('<td class="common" rowspan="2"/>').text(':'))
                        .append($('<td rowspan="2"/>').append($table.$s));
                }

                $row.append($add).appendTo($tbody);
                $('<tr/>').append($min).appendTo($tbody);
                return $table;
            },

            /**
             * add T(time) panel
             * @param timetable T panel DOM
             * @private
             */
            _addTimeOptPane = function ($wrapper) {
                var $table = $('<table/>');
                var $tr = $('<tr/>').appendTo($table);
                //清空按钮
                _createCell($tr, I18N["CLEAR"], 1, NAV['clear'], 'clear');
                //当前按钮
                _createCell($tr, I18N["CURRENT"], 1, NAV['current'], 'current');
                //确认按钮
                _createCell($tr, I18N["OK"], 1, NAV['dok'], 'ok');
                $table.appendTo($wrapper);
            },
            /**
             * bind events
             * @private
             */
            _bindEvts = function () {
                var proxy = function (event) {
                    var target = event.target;
                    var $target = $(target).closest('td');
                    var type = event.type;
                    var navitype = $target.data('nav');
                    var _arguments = arguments;
                    if ($target.data('disabled') || $target.length === 0 || !navitype) {
                        return;
                    }
                    if (!currentDate) {
                        currentDate = currentDate || new Date();
                    }
                    if (type === 'mouseover') {
                        $target.addClass('hover');
                    } else if (type === "mouseup") {
                        $target.removeClass('hover');
                        switch (navitype) {
                            case NAV['prevm']:
                                //previous month
                                _toPrevMonth();
                                _loadDateData($datetable, new Date(currentDate));
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['nextm']:
                                //next month
                                _toNextMonth();
                                _loadDateData($datetable, new Date(currentDate));
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['title']:
                                //click 'title' button to open YM panel
                                _loadMonthData($monthtable, new Date(cache.showYear, cache.showMonth));
                                var $parent = $monthtable.parent('.perfect-datetimepicker');
                                $monthtable.css({
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    height: $parent.height(),
                                    width: $parent.width(),
                                    'z-index': 100000
                                }).show("fast");
                                break;
                            case NAV['clear']:
                                //清空按钮
                                currentDate = null;
                                cache.selectedDate && cache.selectedDate.removeClass('selected');
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                utilsApplyFunc(picker, options.onClear, _arguments);
                                break;
                            case NAV['current']:
                                //click 'current' button
                                currentDate = new Date();
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                            case NAV['today']:
                                //click 'today' button
                                var today = new Date();
                                if ((options.startDate && today < options.startDate) ||
                                    (options.endDate && today > options.endDate)) {
                                    return;
                                } else {
                                    currentDate = new Date(today);
                                    _loadDateData($datetable, today);
                                    _loadTimeData($timetable, today);
                                    cache.selectedDate && cache.selectedDate.removeClass('selected');
                                    cache.selectedDate = $datetable.find('td.today').addClass('selected');
                                }
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['dok']:
                                //click 'ok' button on D panel
                                utilsApplyFunc(picker, options.onOk, _arguments);
                                break;
                            case NAV['prevy']:
                                //previous ten years
                                _toPrevDecade();
                                _loadMonthData($monthtable, new Date(currentDate));
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['nexty']:
                                //next ten years
                                _toNextDecade();
                                _loadMonthData($monthtable, new Date(currentDate));
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['mok']:
                                //click 'ok' button on YM panel
                                _loadDateData($datetable, new Date(currentDate));
                                if ($datetable.parent().length > 0) {
                                    $monthtable.hide("fast");
                                }
                                break;
                            case NAV['cancel']:
                                //click 'cancel' button
                                _loadDateData($datetable, new Date(currentDate));
                                $monthtable.hide("fast");
                                break;
                            case NAV['year']:
                                //choose one year
                                cache.selectedYear && cache.selectedYear.removeClass('selected');
                                cache.selectedYear = $target;
                                var date = currentDate;
                                date.setFullYear($target.text());
                                _loadMonthData($monthtable, new Date(date));
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['month']:
                                //choose one month
                                cache.selectedMonth && cache.selectedMonth.removeClass('selected');
                                cache.selectedMonth = $target.addClass('selected');
                                currentDate.setMonth($target.data('month'));
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['day']:
                                //choose one day
                                cache.selectedDate && cache.selectedDate.removeClass('selected');
                                cache.selectedDate = $target.addClass('selected');
                                var curDate = currentDate;
                                curDate.setFullYear(cache.showYear);
                                curDate.setMonth(cache.showMonth);
                                curDate.setDate($target.text());
                                utilsApplyFunc(picker, options.onDateChange, _arguments);
                                break;
                            case NAV['plus']:
                                //plus time
                                _doTimeInc($timetable, $timetable.focus);
                                break;
                            case NAV['minus']:
                                //minus time
                                _doTimeDec($timetable, $timetable.focus);
                                break;
                            default:
                                break;
                        }
                    } else if (type === "mouseout") {
                        //MOUSEOUT事件
                        $target.removeClass('hover');
                    }
                };
                $el.unbind();
                $el.bind("mousedown", proxy)
                    .bind("mouseover", proxy)
                    .bind("mouseup", proxy)
                    .bind("mouseout", proxy);
            };

        //initialize all panels
        // wrap widget in a form element to be able to turn off html5 form validation
        var $wrapper = $('<form novalidate/>').appendTo($el).addClass(options.baseCls);
        $datetable = _createDatePicker();
        _loadDateData($datetable, new Date(currentDate));
        $monthtable = _createMonthPicker();
        $timetable = _createTimePicker(options.viewMode);
        var $buttonpane = _createButtonPane();
        var VIEWMODE = CONSTS.VIEWMODE;

        switch (options.viewMode) {
            case VIEWMODE.YM : // yyyyMM
                _loadMonthData($monthtable, new Date(currentDate));
                $wrapper.append($monthtable.show());
                break;
            case VIEWMODE.HM : // HHmm
            case VIEWMODE.HMS : // HHmmss
                _loadTimeData($timetable, currentDate, options.viewMode);
                $wrapper.append($timetable.show());
                _addTimeOptPane($wrapper);
                break;
            case VIEWMODE.YMD : //yyyyMMdd
                $wrapper.append($datetable.show());
                $monthtable.hide().appendTo($wrapper);
                $wrapper.append($buttonpane);
                break;

            case VIEWMODE.YMDHMS:
            case VIEWMODE.YMDHM:
            default : // yyyyMMddHHmm(ss)
                $datetable.appendTo($wrapper).show();
                $monthtable.hide().appendTo($wrapper);
                _loadTimeData($timetable, currentDate, options.viewMode);
                $timetable.show().appendTo($wrapper);
                $wrapper.append($buttonpane);
                break;
        }

        _bindEvts();
        picker.element = $el;
        picker.$datetable = $datetable;
        picker.$monthtable = $monthtable;
        picker.$timetable = $timetable;
        picker.getValue = function () {
            var viewMode = CONSTS.VIEWMODE;
            var date = currentDate;
            if (date && (options.viewMode === viewMode.YMD || options.viewMode === viewMode.YM)) {
                //如果不包含时间，则把时间计为00:00:00
                date.setHours(0, 0, 0, 0);
            }
            return date;
        };

        /** API **/
        picker.setValue = function (value) {
            if (value instanceof Date) {
                currentDate = value;
                _loadDateData($datetable, value);
                _loadMonthData($monthtable, value);
                _loadTimeData($timetable, value, options.viewMode);
            }
        };
        picker.getText = function (format) {
            return utilsDate2str(this.getValue(), format ? format : 'YYYY/MM/DD HH:mm:ss');
        };
        picker.destroy = function () {
            this.element.removeData('datetimepicker');
            this.element.remove();
            return picker;
        };
        return picker;
    }

    /**
     * constructor
     * @param options
     * @returns {*}
     */
    $.fn.datetimepicker = function (options) {
        return this.each(function () {
            var $this = $(this);
            if (!$this.data('dateTimePicker')) {
                options = $.extend(true, {}, $.fn.datetimepicker.defaults, options);
                $this.data('dateTimePicker', new DateTimePicker(this, options));
            }
        });
    };

    $.fn.datetimepicker.init = function (el, options) {
        var o = $.extend(true, {}, $.fn.datetimepicker.defaults, options);
        var dtp = new DateTimePicker(el, o);
        $(el).data('dateTimePicker', dtp);
        return dtp;
    };

    /**
     * constants
     * @type {JSON}
     */
    $.fn.datetimepicker.CONSTS = {
        I18N: {
            zh: {
                SDN: ["日", "一", "二", "三", "四", "五", "六"],
                MN: ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
                DN: ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"],
                CALENDAR: "日历",
                CLEAR: "清空",
                TODAY: "今天",
                OK: "确定",
                CURRENT: "当前",
                TIME: "时间"
            },
            en: {
                SDN: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                MN: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                DN: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                CALENDAR: "Calendar",
                CLEAR: "Clear",
                TODAY: "Today",
                OK: "OK",
                CURRENT: "Now",
                TIME: "Time"
            },
            de: {
                SDN: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
                MN: ["Jan", "Feb", "Mrz", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"],
                DN: ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"],
                CALENDAR: "Kalender",
                CLEAR: "Löschen",
                TODAY: "Heute",
                OK: "OK",
                CURRENT: "Jetzt",
                TIME: "Zeit"
            },
            nl: {
                SDN: ["Zo", "Ma", "Di", "Wo", "Do", "Vr", "Za"],
                MN: ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"],
                DN: ["Zondag", "Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag"],
                CALENDAR: "Kalender",
                CLEAR: "Legen",
                TODAY: "Vandaag",
                OK: "OK",
                CURRENT: "Nu",
                TIME: "Tijd"
            }
        },

        VIEWMODE: {
            YM: 'YM',  // yyyyMM
            YMD: 'YMD', // yyyyMMdd
            HMS: 'HMS', // HHmmss
            HM: 'HM', // HHmm
            YMDHMS: 'YMDHMS', // yyyyMMddHHmmss
            YMDHM: 'YMDHM' // yyyyMMddHHmm
        },

        MINYEAR: 1900,
        MAXYEAR: 2999,

        NAV: {
            'prevm': 2, //previous month
            'nextm': 3, //next month
            'title': 4, //title
            'clear': 5, //clear
            'today': 6, //today
            'dok': 7,   //ok in day pane
            'prevy': 8, //previous ten years
            'nexty': 9, //next ten years
            'cancel': 10, //cancel
            'mok': 11,   //ok in month pane
            'plus': 12, //plus
            'minus': 13, //minus
            'current': 15, //current
            'day': 100, //day
            'month': 200, //month
            'year': 300 //year
        }
    };

    /**
     * default configuration
     * @type {JSON}
     */
    $.fn.datetimepicker.defaults = {
        baseCls: "perfect-datetimepicker",  //Basic class
        viewMode: $.fn.datetimepicker.CONSTS.VIEWMODE.YMD,
        firstDayOfWeek: 0, //0~6: Sunday~Saturday, default: 0(Sunday)
        date: null, //initial date
        endDate: null, //end date
        startDate: null, //start date
        language: 'en', //I18N
        //date update event
        onDateChange: null,
        //clear button click event
        onClear: null,
        //ok button click event
        onOk: null,
        //close button click event
        onClose: null
    };
}));
