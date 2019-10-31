/**
* bootstrap-treenav.js v1.0.0 by @morrissinger
* Copyright 2013 Morris Singer
* http://www.apache.org/licenses/LICENSE-2.0
*/
if (!jQuery) { throw new Error("Bootstrap Tree Nav requires jQuery"); }

/* ==========================================================
 * bootstrap-treenav.js
 * https://github.com/morrissinger/BootstrapTreeNav
 * ==========================================================
 * Copyright 2013 Morris Singer
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */

+function ($) {

  'use strict';

  $.fn.navTree = function(options) {

    var defaults = {
      navTreeExpanded: 'icon-collapse-alt',
      navTreeCollapsed: 'icon-expand-alt'
    };
    
    options = $.extend(defaults, options);
    
    if ($(this).prop('tagName') === 'LI') {
      collapsible(this, options);
    } else if ($(this).prop('tagName') === 'UL') {
      collapsible(this, options);
    }

  };

  var collapsible = function(element, options) {
    var $childrenLi = $(element).find('li');
    $childrenLi.each(function(index, li) {
      collapsibleAll($(li), options);
      
      // Expand the tree so that the active item is shown.
      if ($(li).hasClass('active')) {
        $(li).parents('ul').each(function(i, ul) {
          $(ul).show();
          $(ul).siblings('span.opener')
               .removeClass('closed')
               .addClass('opened');

          // If there's a real target to this menu item link, then allow it to be
          // clicked to go to that page, now that the menu has been expanded.
          if ($(ul).siblings('a').attr('href') !== '#' && $(ul).siblings('a').attr('href') !== '') {
            $(ul).siblings('a').off('click.bs.tree');
          }

        });
      }
    });
  };

  var collapsibleAll = function(element, options) {
    var $childUl = $(element).children('ul');
    if ( $childUl.length > 0 ) {
      $childUl.hide();
      $(element).prepend('<span class="opener closed"><span class="tree-icon-closed"><i class="' + options.navTreeCollapsed + '"></i></span><span class="tree-icon-opened"><i class="' + options.navTreeExpanded + '"></i></span></span>');
      $(element).children('a').first().on('click.bs.tree', function(e) {
        e.preventDefault();
        var $opener = $(this).siblings('span.opener');
        if ($opener.hasClass('closed')) {
          expand(element);

          // If there's a real target to this menu item link, then allow it to be
          // clicked to go to that page, now that the menu has been expanded.
          if (($(this).attr('href') !== '#') && ($(this).attr('href') !== '')) {
            $(this).off('click.bs.tree');
          }
            
        } else {
          collapse(element);
        }
      });
      $(element).children('span.opener').first().on('click.bs.tree', function(e){
        var $opener = $(this);
        if ($opener.hasClass('closed')) {
          expand(element);
        } else {
          collapse(element);
        }
      });
    }
  };

  var expand = function(element) {
    var $opener = $(element).children('span.opener');
    $opener.removeClass('closed').addClass('opened');
    $(element).children('ul').first().slideDown('fast');
  };

  var collapse = function(element) {
    var $opener = $(element).children('span.opener');
    $opener.removeClass('opened').addClass('closed');
    $(element).children('ul').first().slideUp('fast');
  };

  $('ul[data-toggle=nav-tree]').each(function(){
    var $tree;
    $tree = $(this);
    $tree.navTree($tree.data());
  });
    
}(window.jQuery);