/*
* jquery-treeview-menu v1.0.0
*
* @requires jQuery v1.4.1 or later.
* @requires jquery.treeview v1.4.1 or later.
* Use jquery-treeview-menu.css
*
* Copyright (c) 2011 Cybozu Labs, Inc.
* http://labs.cybozu.co.jp/
*
* Licensed under the GPL Version 2 license.
*/

(function ($) {

    $.fn.treeviewMenu = function (options) {

        if (treeviewMenuMethods[options]) {
            return treeviewMenuMethods[options].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (options & typeof options != "object") {
            $.error("Method " + options + " does not exists on treeviewMenu.");
        }

        var settings = { chooseText: "(Choose an option)", collapsed: true, zIndex: 100 };
        settings = $.extend(settings, options);

        this.each(function () {
            var picker = this;

            $(this).append('<a href="#" class="tvm-root ui-widget-content"><span class="tvm-selection">' + settings.chooseText + '</span><span class="ui-icon ui-icon-triangle-1-s" style="float: right;"></span></a><div class="tvm-container ui-widget-content" style="position: absolute; z-index: ' + settings.zIndex + ';"></div>');
            if (settings.width) {
                $(".tvm-root", this).css("width", settings.width);
            }
            if (settings.content) {
                $(".tvm-container", this).append(settings.content);
            }
            $(".tvm-container", this).hide().click(function (event) {
                event.stopPropagation();
            });
            $(".tvm-container ul:first", this).treeview({ collapsed: settings.collapsed });
            $(".tvm-root", this).click(function (event) {
                $(".tvm-container", picker).toggle();
                event.stopPropagation();
            });
            $(".tvm-container a", this).click(function () {
                var $this = $(this);
                $(".tvm-container", picker).hide();
                setSelection(picker, $this.attr("id"), $this.text());
                $(picker).change();
            });
            $(document).click(function () {
                $(".tvm-container", picker).hide();
            });
        });

        return this;
    };

    var treeviewMenuMethods = {
        getSelection: function () {
            return $(this).data("selection");
        },

        setSelection: function (obj) {
            this.each(function () {
                setSelection(this, obj.value, obj.text);
            });
            return this;
        }
    };

    function setSelection(picker, value, text) {
        $(".tvm-selection", picker).text(text);
        $(picker).data("selection", { value: value, text: text });
    }

})(jQuery);
